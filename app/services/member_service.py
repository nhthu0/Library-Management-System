
class MemberService:
    def __init__(self, reader_repo, user_repo):
        self.reader_repo = reader_repo
        self.user_repo = user_repo

    def get_my_profile(self, current_user_id):
        if not current_user_id:
            raise ValueError("ID người dùng không hợp lệ.")

        user = self.user_repo.find_by_id(current_user_id)

        if not user:
            raise ValueError("Không tìm thấy thông tin cá nhân.")
        user.pop("password", None)

        return user

    def update_my_profile(self, current_user_id, profile_data):
        if not current_user_id:
            raise ValueError("ID người dùng không hợp lệ.")

        if not isinstance(profile_data, dict) or not profile_data:
            raise ValueError("Dữ liệu cập nhật không hợp lệ.")

        user = self.user_repo.find_by_id(current_user_id)

        if not user:
            raise ValueError("Không tìm thấy thông tin cá nhân.")

        self.user_repo.update_user_profile(
            current_user_id,
            profile_data
        )

        return self.get_my_profile(current_user_id)

    def get_all_readers(self):
        return self.reader_repo.get_all_readers()

    def get_reader_by_id(self, reader_id):
        reader = self.reader_repo.get_reader_by_id(reader_id)

        if not reader:
            raise ValueError("Không tìm thấy độc giả.")

        return reader

    def update_reader(self, reader_id, reader_data):
        reader = self.reader_repo.get_reader_by_id(reader_id)

        if not reader:
            raise ValueError("Không tìm thấy độc giả.")

        self.user_repo.update_user_profile(
            reader["userID"],
            reader_data
        )

        return self.reader_repo.get_reader_by_id(reader_id)
