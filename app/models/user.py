class User:
    def __init__(self, user_id, username, full_name, email, password, phone_number, role, account_status):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.email = email
        self.password = password
        self.phone_number = phone_number
        self.role = role  # 'ADMIN' hoặc 'READER'
        self.account_status = account_status  # 'Active', 'Locked', 'Inactive'