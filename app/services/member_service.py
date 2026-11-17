class MemberService:
    def __init__(self, reader_repo, user_repo):
        self.reader_repo = reader_repo
        self.user_repo = user_repo

    def get_all_readers(self):
        return self.reader_repo.get_all_readers()

    def get_reader_by_id(self, reader_id):
        reader = self.reader_repo.get_reader_by_id(reader_id)
        if not reader:
            raise Exception("Không tìm thấy độc giả")
        return reader

    def update_reader(self, reader_id, reader_data):
        reader = self.reader_repo.get_reader_by_id(reader_id)
        if not reader:
            raise Exception("Không tìm thấy độc giả")
        self.user_repo.update_user_profile(reader['userID'], reader_data)