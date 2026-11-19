class AdminRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_admin_by_user_id(self, user_id):
        cursor = self.db.cursor(dictionary=True)
        query = "SELECT * FROM ADMINS WHERE userID = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return result