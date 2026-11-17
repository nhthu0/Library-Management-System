from models.user import User

class Reader(User):
    def __init__(self, user_id, username, full_name, email, password, phone_number, account_status, reader_id, expiration_date):
        super().__init__(user_id, username, full_name, email, password, phone_number, 'READER', account_status)
        self.reader_id = reader_id
        self.expiration_date = expiration_date