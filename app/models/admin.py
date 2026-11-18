from app.models.user import User

class Admin(User):
    def __init__(self, user_id, username, full_name, email, password, phone_number, account_status, admin_id):
        super().__init__(user_id, username, full_name, email, password, phone_number, 'ADMIN', account_status)
        self.admin_id = admin_id
