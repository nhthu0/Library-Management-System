class UserRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def find_by_username(self, username):
        cursor = self.db.cursor(dictionary=True)
        query = """
            SELECT u.*, a.adminID, r.readerID, r.expiration_date 
            FROM USERS u 
            LEFT JOIN ADMINS a ON u.userID = a.userID 
            LEFT JOIN READERS r ON u.userID = r.userID 
            WHERE u.username = %s
        """
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()
        return user

    def update_user_profile(self, user_id, profile_data):
        cursor = self.db.cursor()
        try:
            query = """
                UPDATE USERS 
                SET full_name = %s, email = %s, phone_number = %s 
                WHERE userID = %s
            """
            cursor.execute(query, (
                profile_data.get('full_name'),
                profile_data.get('email'),
                profile_data.get('phone_number'),
                user_id
            ))
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            cursor.close()