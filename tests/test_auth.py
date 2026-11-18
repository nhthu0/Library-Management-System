
import unittest
from unittest.mock import Mock

from app.services.auth_service import AuthService


class TestAuthService(unittest.TestCase):

    def setUp(self):
        self.user_repo = Mock()
        self.reader_repo = Mock()
        self.auth = AuthService(
            self.user_repo,
            self.reader_repo
        )

    def test_hash_password(self):
        password = "Test@123456"
        hashed = self.auth.hash_password(password)

        self.assertNotEqual(hashed, password)
        self.assertTrue(
            self.auth.verify_password(password, hashed)
        )
        self.assertFalse(
            self.auth.verify_password("WrongPassword", hashed)
        )

    def test_register_reader(self):
        self.user_repo.find_by_username.return_value = None
        self.reader_repo.create_reader.return_value = 101

        data = {
            "username": "test_reader",
            "password": "Test@123456",
            "full_name": "Test Reader",
            "email": "test@example.com"
        }

        result = self.auth.register_reader(data)

        self.assertEqual(result, 101)
        saved = self.reader_repo.create_reader.call_args.args[0]
        self.assertTrue(
            self.auth.verify_password(
                "Test@123456",
                saved["password"]
            )
        )

    def test_duplicate_username(self):
        self.user_repo.find_by_username.return_value = {
            "userID": 1
        }

        with self.assertRaises(ValueError):
            self.auth.register_reader({
                "username": "existing_user",
                "password": "Test@123456"
            })

        self.reader_repo.create_reader.assert_not_called()

    def test_login_success(self):
        hashed = self.auth.hash_password("Test@123456")

        self.user_repo.find_by_username.return_value = {
            "userID": 101,
            "username": "test_reader",
            "password": hashed,
            "role": "READER",
            "account_status": "Active",
            "readerID": 10,
            "adminID": None
        }

        result = self.auth.login(
            "test_reader",
            "Test@123456"
        )

        self.assertEqual(result["user_id"], 101)
        self.assertEqual(result["role"], "READER")

    def test_login_wrong_password(self):
        hashed = self.auth.hash_password("Test@123456")

        self.user_repo.find_by_username.return_value = {
            "userID": 101,
            "username": "test_reader",
            "password": hashed,
            "role": "READER",
            "account_status": "Active"
        }

        with self.assertRaises(ValueError):
            self.auth.login(
                "test_reader",
                "WrongPassword"
            )

    def test_login_locked_account(self):
        hashed = self.auth.hash_password("Test@123456")

        self.user_repo.find_by_username.return_value = {
            "userID": 101,
            "username": "test_reader",
            "password": hashed,
            "role": "READER",
            "account_status": "Locked"
        }

        with self.assertRaises(PermissionError):
            self.auth.login(
                "test_reader",
                "Test@123456"
            )


if __name__ == "__main__":
    unittest.main()
