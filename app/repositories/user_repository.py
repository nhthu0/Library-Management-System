
class UserRepository:
    ALLOWED_PROFILE_FIELDS = (
        "full_name",
        "email",
        "phone_number"
    )

    def __init__(self, db_connection):
        self.db = db_connection

    def find_by_username(self, username):
        cursor = self.db.cursor(dictionary=True)
        try:
            query = """
                SELECT u.*, a.adminID, r.readerID,
                       r.expiration_date
                FROM users u
                LEFT JOIN admins a ON u.userID = a.userID
                LEFT JOIN readers r ON u.userID = r.userID
                WHERE u.username = %s
            """
            cursor.execute(query, (username,))
            return cursor.fetchone()
        finally:
            cursor.close()
    def find_by_id(self, user_id):
        cursor = self.db.cursor(dictionary=True)

        try:
            query = """
                SELECT
                    u.userID,
                    u.username,
                    u.full_name,
                    u.email,
                    u.phone_number,
                    u.role,
                    u.account_status,
                    a.adminID,
                    r.readerID,
                    r.expiration_date
                FROM users u
                LEFT JOIN admins a ON u.userID = a.userID
                LEFT JOIN readers r ON u.userID = r.userID
                WHERE u.userID = %s
            """

            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()


    def update_user_profile(self, user_id, profile_data):
        if not isinstance(profile_data, dict):
            raise ValueError("Dữ liệu cập nhật không hợp lệ.")

        invalid_fields = (
            set(profile_data) - set(self.ALLOWED_PROFILE_FIELDS)
        )

        if invalid_fields:
            raise ValueError(
                "Trường cập nhật không hợp lệ: "
                + ", ".join(sorted(map(str, invalid_fields)))
            )

        if not profile_data:
            raise ValueError("Không có thông tin cần cập nhật.")

        for field, value in profile_data.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field} phải là chuỗi không được để trống."
                )

        fields = list(profile_data.keys())

        set_clause = ", ".join(
            f"{field} = %s" for field in fields
        )

        values = [
            profile_data[field].strip()
            for field in fields
        ]

        query = f"""
            UPDATE users
            SET {set_clause}
            WHERE userID = %s
        """

        cursor = self.db.cursor()

        try:
            cursor.execute(query, (*values, user_id))
            affected_rows = cursor.rowcount
            self.db.commit()
            return affected_rows
        except Exception:
            self.db.rollback()
            raise
        finally:
            cursor.close()
