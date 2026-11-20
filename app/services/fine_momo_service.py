from contextlib import contextmanager
from datetime import date
from uuid import uuid4

from app.database.connection import get_connection
from app.services.momo_gateway import MoMoGatewayError, MoMoSandbox


class FineMomoService:
    # These results describe a terminal failed or cancelled payment, rather than
    # a communication error or order that is still awaiting confirmation.
    TERMINAL_FAILURES = frozenset({1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1017, 1026})

    def __init__(self, connection_factory=None, gateway=None):
        self._connection_factory = connection_factory or get_connection
        self._gateway = gateway

    @property
    def gateway(self):
        if self._gateway is None:
            self._gateway = MoMoSandbox()
        return self._gateway

    @contextmanager
    def _transaction(self):
        conn = self._connection_factory()
        try:
            with conn.cursor(dictionary=True) as cursor:
                conn.start_transaction(isolation_level="READ COMMITTED")
                yield cursor
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _reader_id(fine_id, current_user):
        if type(fine_id) is not int or fine_id <= 0:
            raise ValueError("Invalid fine ID.")
        if not isinstance(current_user, dict) or str(current_user.get("role", "")).upper() != "READER":
            raise PermissionError("An active reader account is required.")
        user_id = current_user.get("user_id")
        if type(user_id) is not int or user_id <= 0:
            raise PermissionError("Sign in again before paying a fine.")
        return user_id

    @staticmethod
    def _load_fine(cursor, fine_id, user_id):
        # The cash-payment path also locks the fine before looking at its order.
        cursor.execute(
            """SELECT f.amount, f.payment_status
               FROM fines f
               WHERE f.fineID = %s AND EXISTS (
                   SELECT 1 FROM borrowing_records b
                   JOIN readers r ON r.readerID = b.readerID
                   JOIN users u ON u.userID = r.userID
                   WHERE b.borrowingID = f.borrowingID AND b.status = 'Returned'
                     AND u.userID = %s AND u.role = 'Reader' AND u.account_status = 'Active'
               )
               FOR UPDATE""",
            (fine_id, user_id),
        )
        fine = cursor.fetchone()
        if fine is None:
            raise PermissionError("Only the owner can pay a fine for a confirmed return.")
        cursor.execute(
            """SELECT order_id, partner_code, amount, state, pay_url
               FROM fine_momo_orders WHERE fineID = %s FOR UPDATE""",
            (fine_id,),
        )
        return fine, cursor.fetchone()

    def start(self, fine_id, current_user):
        """Reserve and open one sandbox checkout per unpaid fine."""
        user_id = self._reader_id(fine_id, current_user)
        with self._transaction() as cursor:
            fine, order = self._load_fine(cursor, fine_id, user_id)
            if fine["payment_status"] != "Unpaid":
                raise ValueError("This fine has already been paid.")
            amount = int(fine["amount"])
            if amount != fine["amount"] or not 1000 <= amount <= 50_000_000:
                raise ValueError("This fine amount is outside MoMo's supported range.")

            if order and order["state"] == "Paid":
                raise RuntimeError("A settled MoMo order needs reconciliation by the library.")
            partner_code = self.gateway.partner_code
            if order and order["state"] == "Pending":
                if order["partner_code"] != partner_code or order["amount"] != amount:
                    raise ValueError("The merchant or fine amount changed. Contact the library.")
                order_id = order["order_id"]
                pay_url = order["pay_url"]
            else:
                order_id = uuid4().hex
                pay_url = None
                if order is None:
                    cursor.execute(
                        """INSERT INTO fine_momo_orders (order_id, partner_code, amount, fineID)
                           VALUES (%s, %s, %s, %s)""",
                        (order_id, partner_code, amount, fine_id),
                    )
                else:
                    cursor.execute(
                        """UPDATE fine_momo_orders
                           SET order_id = %s, partner_code = %s, amount = %s,
                               state = 'Pending', pay_url = NULL, transaction_id = NULL
                           WHERE fineID = %s""",
                        (order_id, partner_code, amount, fine_id),
                    )

        if pay_url:
            return MoMoSandbox.validate_payment_url(pay_url)

        # Persist the order ID before the network call. Retries reuse it so a
        # timeout cannot trigger a second charge for the same fine.
        try:
            pay_url = self.gateway.create(order_id, amount)
        except MoMoGatewayError as error:
            if error.result_code in self.TERMINAL_FAILURES:
                with self._transaction() as cursor:
                    self._load_fine(cursor, fine_id, user_id)
                    self._fail_order(cursor, fine_id, order_id)
            raise

        with self._transaction() as cursor:
            fine, order = self._load_fine(cursor, fine_id, user_id)
            if fine["payment_status"] != "Unpaid" or not order or order["order_id"] != order_id:
                raise ValueError("The payment record changed. Refresh before paying.")
            if order["state"] != "Pending" or fine["amount"] != amount:
                raise ValueError("The fee changed. Check the payment status before retrying.")
            cursor.execute(
                "UPDATE fine_momo_orders SET pay_url = %s WHERE fineID = %s AND order_id = %s",
                (pay_url, fine_id, order_id),
            )
        return pay_url

    @staticmethod
    def _fail_order(cursor, fine_id, order_id):
        cursor.execute(
            """UPDATE fine_momo_orders SET state = 'Failed', pay_url = NULL
               WHERE fineID = %s AND order_id = %s AND state = 'Pending'""",
            (fine_id, order_id),
        )

    def check(self, fine_id, current_user):
        """Reconcile a sandbox order without trusting any browser callback."""
        user_id = self._reader_id(fine_id, current_user)
        with self._transaction() as cursor:
            fine, order = self._load_fine(cursor, fine_id, user_id)
            if fine["payment_status"] == "Paid":
                return "Paid"
            if order is None:
                raise ValueError("Start a MoMo payment before checking its status.")
            if order["state"] == "Failed":
                return "Failed"
            if order["state"] == "Paid":
                raise RuntimeError("A settled MoMo order needs reconciliation by the library.")

        if order["partner_code"] != self.gateway.partner_code:
            raise ValueError("The MoMo merchant changed. Contact the library.")
        response = self.gateway.query(order["order_id"])
        if response.get("partnerCode") != order["partner_code"] or response.get("orderId") != order["order_id"]:
            raise RuntimeError("The MoMo response does not match this payment.")

        code = response.get("resultCode")
        if type(code) is not int:
            raise RuntimeError("MoMo returned an invalid payment status.")
        if code != 0 and code not in self.TERMINAL_FAILURES:
            return "Pending"
        if code == 0:
            transaction_id = response.get("transId")
            paid_amount = response.get("amount")
            if type(paid_amount) is not int or paid_amount != order["amount"]:
                raise RuntimeError("The MoMo payment amount does not match this fine.")
            if type(transaction_id) is not int or not 0 < transaction_id < 2**64:
                raise RuntimeError("MoMo returned an invalid transaction identifier.")
            if response.get("refundTrans"):
                raise RuntimeError("MoMo reports a refund. Ask the library to reconcile this fine.")

        with self._transaction() as cursor:
            fine, current = self._load_fine(cursor, fine_id, user_id)
            if fine["payment_status"] == "Paid":
                return "Paid"
            if not current or current["order_id"] != order["order_id"]:
                raise ValueError("A newer payment attempt exists. Check again.")
            if code != 0:
                self._fail_order(cursor, fine_id, order["order_id"])
                return "Failed"
            if current["state"] != "Pending" or fine["amount"] != order["amount"]:
                raise ValueError("The fine or order changed. Contact the library.")
            cursor.execute(
                """UPDATE fine_momo_orders SET state = 'Paid', transaction_id = %s
                   WHERE fineID = %s AND order_id = %s""",
                (transaction_id, fine_id, order["order_id"]),
            )
            cursor.execute(
                """UPDATE fines SET payment_status = 'Paid', payment_date = %s
                   WHERE fineID = %s AND payment_status = 'Unpaid'""",
                (date.today().isoformat(), fine_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("The fine could not be marked as paid.")
        return "Paid"
