
import hashlib
import hmac

import bcrypt


class AuthService:
    def __init__(self, user_repo, reader_repo):
        self.user_repo = user_repo
        self.reader_repo = reader_repo

    def hash_password(self, password):
        if not isinstance(password, str) or not password:
            raise ValueError("Mật khẩu không được để trống.")

        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def verify_password(self, password, stored_hash):
        if not isinstance(password, str) or not isinstance(stored_hash, str):
            return False

        if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
            try:
                return bcrypt.checkpw(
                    password.encode("utf-8"),
                    stored_hash.encode("utf-8")
                )
            except ValueError:
                return False

        # Tương thích tạm thời với dữ liệu SHA-256 cũ.
        legacy_hash = hashlib.sha256(
            password.encode("utf-8")
        ).hexdigest()

        return hmac.compare_digest(legacy_hash, stored_hash)

    def login(self, username, password):
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Tên đăng nhập không được để trống.")

        if not isinstance(password, str) or not password:
            raise ValueError("Mật khẩu không được để trống.")

        user = self.user_repo.find_by_username(username.strip())

        if not user:
            raise ValueError("Tên đăng nhập hoặc mật khẩu không chính xác.")

        if user["account_status"] != "Active":
            raise PermissionError(
                "Tài khoản đang bị khóa hoặc không hoạt động."
            )

        if not self.verify_password(password, user["password"]):
            raise ValueError("Tên đăng nhập hoặc mật khẩu không chính xác.")

        return {
            "user_id": user["userID"],
            "username": user["username"],
            "role": user["role"],
            "reader_id": user.get("readerID"),
            "admin_id": user.get("adminID")
        }

    def register_reader(self, user_data):
        if not isinstance(user_data, dict):
            raise ValueError("Dữ liệu đăng ký không hợp lệ.")

        username = user_data.get("username")
        password = user_data.get("password")

        if not isinstance(username, str) or not username.strip():
            raise ValueError("Tên đăng nhập không được để trống.")

        if not isinstance(password, str) or not password:
            raise ValueError("Mật khẩu không được để trống.")

        username = username.strip()

        if self.user_repo.find_by_username(username):
            raise ValueError("Tên đăng nhập đã tồn tại.")

        new_user_data = user_data.copy()
        new_user_data["username"] = username
        new_user_data["password"] = self.hash_password(password)

        return self.reader_repo.create_reader(new_user_data)
