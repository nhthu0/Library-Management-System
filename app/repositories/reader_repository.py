class ReaderRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def create_reader(self, user_data):
        cursor = self.db.cursor()
        try:
            self.db.start_transaction()
            user_query = """
                INSERT INTO users (username, full_name, email, password, phone_number, role, account_status)
                VALUES (%s, %s, %s, %s, %s, 'Reader', 'Active')
            """
            cursor.execute(user_query, (
                user_data['username'],
                user_data['full_name'],
                user_data['email'],
                user_data['password'],
                user_data.get('phone_number')
            ))
            user_id = cursor.lastrowid

            reader_query = "INSERT INTO readers (userID, expiration_date) VALUES (%s, %s)"
            cursor.execute(reader_query, (user_id, user_data.get('expiration_date')))

            self.db.commit()
            return user_id
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            cursor.close()

    def get_all_readers(self):
        cursor = self.db.cursor(dictionary=True)
        query = """
            SELECT r.readerID, u.userID, u.username, u.full_name, u.email, u.phone_number, u.account_status, r.expiration_date
            FROM users u
            JOIN readers r ON u.userID = r.userID
            WHERE u.role = 'Reader'
        """
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    def get_reader_by_id(self, reader_id):
        cursor = self.db.cursor(dictionary=True)
        query = """
            SELECT r.readerID, u.userID, u.username, u.full_name, u.email, u.phone_number, u.account_status, r.expiration_date
            FROM users u
            JOIN readers r ON u.userID = r.userID
            WHERE r.readerID = %s
        """
        cursor.execute(query, (reader_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    def set_status(self, reader_id, status):
        if status not in ("Active", "Locked"):
            raise ValueError("Choose Active or Locked.")
        cursor = self.db.cursor()
        try:
            cursor.execute(
                """UPDATE users u JOIN readers r ON r.userID = u.userID
                   SET u.account_status = %s WHERE r.readerID = %s AND u.role = 'Reader'""",
                (status, reader_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Reader not found or account status already changed.")
            self.db.commit()
        finally:
            cursor.close()

    def delete_reader(self, reader_id):
        cursor = self.db.cursor()
        try:
            self.db.start_transaction()
            cursor.execute("SELECT userID FROM readers WHERE readerID = %s FOR UPDATE", (reader_id,))
            reader = cursor.fetchone()
            if not reader:
                raise ValueError("Reader not found.")
            cursor.execute("SELECT 1 FROM borrowing_records WHERE readerID = %s LIMIT 1", (reader_id,))
            if cursor.fetchone():
                raise ValueError("This reader has loan history. Lock the account to preserve the records.")
            cursor.execute("DELETE FROM readers WHERE readerID = %s", (reader_id,))
            cursor.execute("DELETE FROM users WHERE userID = %s", (reader[0],))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            cursor.close()
