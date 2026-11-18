
class MemberController:
    def __init__(self, member_service):
        self.member_service = member_service

    def get_my_profile(self, current_user_id):
        try:
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
