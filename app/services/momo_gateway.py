import hashlib
import hmac
import json
import os
import re
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4


class MoMoGatewayError(RuntimeError):
    def __init__(self, message, result_code=None):
        super().__init__(message)
        self.result_code = result_code


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class MoMoSandbox:
    """Signed requests to MoMo's test environment."""

    HOST = "test-payment.momo.vn"
    CREATE_FIELDS = (
        "accessKey", "amount", "extraData", "ipnUrl", "orderId", "orderInfo",
        "partnerCode", "redirectUrl", "requestId", "requestType",
    )
    CREATE_RESPONSE_FIELDS = (
        "accessKey", "amount", "message", "orderId", "partnerCode", "payUrl",
        "requestId", "responseTime", "resultCode",
    )
    QUERY_FIELDS = ("accessKey", "orderId", "partnerCode", "requestId")

    def __init__(self):
        self.partner_code = os.getenv("MOMO_PARTNER_CODE", "").strip()
        self._access_key = os.getenv("MOMO_ACCESS_KEY", "").strip()
        self._secret_key = os.getenv("MOMO_SECRET_KEY", "").strip()
        self._redirect_url = os.getenv("MOMO_REDIRECT_URL", "").strip()
        self._ipn_url = os.getenv("MOMO_IPN_URL", "").strip()

        if not all((self.partner_code, self._access_key, self._secret_key)):
            raise MoMoGatewayError("Set the MoMo Sandbox partner code, access key and secret key.")
        if not self._valid_callback(self._redirect_url) or not self._valid_callback(self._ipn_url):
            raise MoMoGatewayError("Set valid MoMo Sandbox redirect and IPN URLs.")

        self._http = build_opener(_RejectRedirects())

    @staticmethod
    def _valid_callback(value):
        try:
            url = urlsplit(value)
            host = url.hostname
        except ValueError:
            return False
        return (
            bool(host) and not url.username and not url.password and not url.fragment
            and (url.scheme == "https" or (
                url.scheme == "http" and host in {"localhost", "127.0.0.1", "::1"}
            ))
        )

    @classmethod
    def validate_payment_url(cls, value):
        if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
            raise MoMoGatewayError("MoMo did not provide a valid Sandbox checkout link.")
        try:
            url = urlsplit(value)
        except ValueError:
            raise MoMoGatewayError("MoMo did not provide a valid Sandbox checkout link.") from None
        if url.scheme != "https" or url.netloc.lower() != cls.HOST:
            raise MoMoGatewayError("MoMo did not provide a valid Sandbox checkout link.")
        return value

    def _sign(self, data, fields):
        values = {**data, "accessKey": self._access_key}
        message = "&".join(f"{name}={values[name]}" for name in fields)
        return hmac.new(self._secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

    def _post(self, action, order_id, request_id, fields, **details):
        if (
            not isinstance(order_id, str) or len(order_id) > 64
            or not re.fullmatch(r"[A-Za-z0-9](?:[-_.]*[A-Za-z0-9])*", order_id)
        ):
            raise ValueError("Invalid MoMo order ID.")
        body = {
            "partnerCode": self.partner_code, "orderId": order_id, "requestId": request_id,
            "lang": "en", **details,
        }
        body["signature"] = self._sign(body, fields)
        request = Request(
            f"https://{self.HOST}/v2/gateway/api/{action}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=UTF-8", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self._http.open(request, timeout=30) as response:
                raw = response.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ValueError("Response was too large.")
                result = json.loads(raw)
        except (OSError, ValueError):
            raise MoMoGatewayError("Could not verify the MoMo Sandbox response. Check payment status before retrying.") from None

        if (
            not isinstance(result, dict)
            or result.get("partnerCode") != self.partner_code
            or result.get("orderId") != order_id
            or result.get("requestId") != request_id
            or type(result.get("resultCode")) is not int
        ):
            raise MoMoGatewayError("MoMo Sandbox returned a response for an unexpected request.")
        return result

    def create(self, order_id, amount):
        if type(amount) is not int or not 1_000 <= amount <= 50_000_000:
            raise ValueError("MoMo Sandbox accepts whole amounts from 1,000 to 50,000,000 VND.")
        # The order ID is also the idempotency key for retries of this checkout.
        result = self._post(
            "create", order_id, order_id, self.CREATE_FIELDS,
            amount=amount, extraData="", ipnUrl=self._ipn_url, orderInfo="Library overdue fine",
            redirectUrl=self._redirect_url, requestType="captureWallet", autoCapture=True,
        )
        result_code = result["resultCode"]
        if result_code != 0:
            raise MoMoGatewayError(f"MoMo Sandbox could not create checkout (code {result_code}).", result_code)
        if type(result.get("amount")) is not int or result["amount"] != amount:
            raise MoMoGatewayError("MoMo Sandbox returned an unexpected checkout amount.")
        if "signature" in result:
            try:
                expected_signature = self._sign(result, self.CREATE_RESPONSE_FIELDS)
            except KeyError:
                raise MoMoGatewayError("MoMo Sandbox returned an incomplete checkout signature.") from None
            signature = result["signature"]
            if not isinstance(signature, str) or not signature.isascii() or not hmac.compare_digest(signature, expected_signature):
                raise MoMoGatewayError("MoMo Sandbox returned an invalid checkout signature.")
        return self.validate_payment_url(result.get("payUrl"))

    def query(self, order_id):
        result = self._post("query", order_id, uuid4().hex, self.QUERY_FIELDS)
        if result["resultCode"] == 0 and (
            type(result.get("amount")) is not int or result["amount"] <= 0
            or type(result.get("transId")) is not int or result["transId"] <= 0
        ):
            raise MoMoGatewayError("MoMo Sandbox returned incomplete transaction details.")
        return result
