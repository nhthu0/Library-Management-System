import hashlib

class AuthService:
    def __init__(self, user_repo, reader_repo):
        self.user_repo = user_repo
        self.reader_repo = reader_repo

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        user = self.user_repo.find_by_username(username)
        if not user:
            raise Exception("Tài khoản không tồn tại")
        
        if user['account_status'] != 'Active':
            raise Exception("Tài khoản đang bị khóa hoặc không hoạt động")

        hashed_pwd = self.hash_password(password)
        if user['password'] != hashed_pwd:
            raise Exception("Mật khẩu không chính xác")

        return {
            "user_id": user['userID'],
            "username": user['username'],
            "role": user['role'],
            "reader_id": user.get('readerID'),
            "admin_id": user.get('adminID')
        }

    def register_reader(self, user_data):
        existing = self.user_repo.find_by_username(user_data['username'])
        if existing:
            raise Exception("Tên đăng nhập đã tồn tại")

        user_data['password'] = self.hash_password(user_data['password'])
        return self.reader_repo.create_reader(user_data)