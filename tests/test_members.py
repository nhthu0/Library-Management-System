
import unittest
from unittest.mock import Mock

from app.services.member_service import MemberService


class TestMemberService(unittest.TestCase):

    def setUp(self):
        self.reader_repo = Mock()
        self.user_repo = Mock()
        self.service = MemberService(
            self.reader_repo,
            self.user_repo
        )

    def test_get_my_profile(self):
        self.user_repo.find_by_id.return_value = {
            "userID": 1,
            "username": "reader01",
            "password": "hashed_password",
            "full_name": "Test Reader"
        }

        result = self.service.get_my_profile(1)

        self.assertEqual(result["userID"], 1)
        self.assertNotIn("password", result)

    def test_get_my_profile_not_found(self):
        self.user_repo.find_by_id.return_value = None

        with self.assertRaises(ValueError):
            self.service.get_my_profile(999)

    def test_update_my_profile(self):
        self.user_repo.find_by_id.return_value = {
            "userID": 1,
            "username": "reader01",
            "full_name": "Test Reader",
            "email": "new@example.com"
        }

        result = self.service.update_my_profile(
            1,
            {"email": "new@example.com"}
        )

        self.user_repo.update_user_profile.assert_called_once_with(
            1,
            {"email": "new@example.com"}
        )
        self.assertEqual(result["email"], "new@example.com")

    def test_get_all_readers(self):
        self.reader_repo.get_all_readers.return_value = [
            {"readerID": 1},
            {"readerID": 2}
        ]

        result = self.service.get_all_readers()

        self.assertEqual(len(result), 2)

    def test_get_reader_by_id(self):
        self.reader_repo.get_reader_by_id.return_value = {
            "readerID": 1,
            "userID": 10
        }

        result = self.service.get_reader_by_id(1)

        self.assertEqual(result["readerID"], 1)

    def test_get_reader_not_found(self):
        self.reader_repo.get_reader_by_id.return_value = None

        with self.assertRaises(ValueError):
            self.service.get_reader_by_id(999)

    def test_update_reader(self):
        self.reader_repo.get_reader_by_id.return_value = {
            "readerID": 1,
            "userID": 10
        }

        self.service.update_reader(
            1,
            {"full_name": "Updated Reader"}
        )

        self.user_repo.update_user_profile.assert_called_once_with(
            10,
            {"full_name": "Updated Reader"}
        )


if __name__ == "__main__":
    unittest.main()
