
class MemberController:
    def __init__(self, member_service, current_user, auth_service):
        self.member_service = member_service
        self.current_user = current_user or {}
        self.auth_service = auth_service

    def _require_admin(self):
        if str(self.current_user.get("role", "")).upper() != "ADMIN":
            raise PermissionError("Admin access is required.")
        profile = self.member_service.user_repo.find_by_id(self.current_user.get("user_id"))
        if not profile or not profile.get("adminID") or profile["account_status"] != "Active":
            raise PermissionError("An active administrator account is required.")

    def _manage(self, operation, message):
        try:
            self._require_admin()
            return {"success": True, "message": message, "data": operation()}
        except Exception as error:
            return {"success": False, "message": str(error), "data": None}

    def create_reader(self, data):
        return self._manage(lambda: self.auth_service.register_reader(data), "Reader account created.")

    def set_reader_status(self, reader_id, status):
        return self._manage(
            lambda: self.member_service.reader_repo.set_status(reader_id, status),
            "Reader status updated.",
        )

    def delete_reader(self, reader_id):
        return self._manage(
            lambda: self.member_service.reader_repo.delete_reader(reader_id),
            "Reader account deleted.",
        )

    def get_my_profile(self, current_user_id):
        try:
            if current_user_id != self.current_user.get("user_id"):
                raise PermissionError("You can only access your own profile.")
            profile = self.member_service.get_my_profile(
                current_user_id
            )

            if profile is None:
                raise ValueError("Không tìm thấy thông tin cá nhân.")

            return {
                "success": True,
                "message": "Lấy thông tin cá nhân thành công",
                "data": profile
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": None
            }

    def update_my_profile(self, current_user_id, profile_data):
        try:
            if current_user_id != self.current_user.get("user_id"):
                raise PermissionError("You can only access your own profile.")
            result = self.member_service.update_my_profile(
                current_user_id,
                profile_data
            )

            return {
                "success": True,
                "message": "Cập nhật thông tin cá nhân thành công",
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": None
            }

    def get_all_readers(self):
        try:
            self._require_admin()
            readers = self.member_service.get_all_readers()

            return {
                "success": True,
                "message": "Lấy danh sách độc giả thành công",
                "data": readers if readers else []
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": []
            }

    def get_reader_by_id(self, reader_id):
        try:
            self._require_admin()
            reader = self.member_service.get_reader_by_id(reader_id)

            return {
                "success": True,
                "message": "Lấy thông tin độc giả thành công",
                "data": reader
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": None
            }

    def update_reader(self, reader_id, reader_data):
        try:
            self._require_admin()
            result = self.member_service.update_reader(
                reader_id,
                reader_data
            )

            return {
                "success": True,
                "message": "Cập nhật độc giả thành công",
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "data": None
            }
