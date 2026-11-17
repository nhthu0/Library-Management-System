class ReaderRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def create_reader(self, user_data):
        cursor = self.db.cursor()
        try:
            self.db.start_transaction()
            # 1. Insert vào bảng USERS
            user_query = """
                INSERT INTO USERS (username, full_name, email, password, phone_number, role, account_status)
                VALUES (%s, %s, %s, %s, %s, 'READER', 'Active')
            """
            cursor.execute(user_query, (
                user_data['username'],
                user_data['full_name'],
                user_data['email'],
                user_data['password'],
                user_data.get('phone_number')
            ))
            user_id = cursor.lastrowid

            # 2. Insert vào bảng READERS
            reader_query = "INSERT INTO READERS (userID, expiration_date) VALUES (%s, %s)"
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
            FROM USERS u 
            JOIN READERS r ON u.userID = r.userID 
            WHERE u.role = 'READER'
        """
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    def get_reader_by_id(self, reader_id):
        cursor = self.db.cursor(dictionary=True)
        query = """
            SELECT r.readerID, u.userID, u.username, u.full_name, u.email, u.phone_number, u.account_status, r.expiration_date 
            FROM USERS u 
            JOIN READERS r ON u.userID = r.userID 
            WHERE r.readerID = %s
        """
        cursor.execute(query, (reader_id,))
        result = cursor.fetchone()
        cursor.close()
        return result