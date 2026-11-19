class AuthController:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def login(self, username, password):
        try:
            data = self.auth_service.login(username, password)
            return {
                "success": True,
                "message": "Đăng nhập thành công",
                "data": data
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": None
            }

    def register(self, user_data):
        try:
            self.auth_service.register_reader(user_data)
            return {
                "success": True,
                "message": "Đăng ký tài khoản thành công",
                "data": {}
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": None
            }

    def logout(self):
        try:
            return {
                "success": True,
                "message": "Đăng xuất thành công",
                "data": {}
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": None
            }