
import os
import uuid

import pytest

from app.database.connection import get_connection
from app.repositories.user_repository import UserRepository
from app.repositories.reader_repository import ReaderRepository
from app.services.auth_service import AuthService
from app.services.member_service import MemberService


@pytest.fixture
def services():
    # Chỉ cho phép kiểm thử trên database riêng.
    if os.getenv("DB_NAME") != "library_management_test":
        pytest.fail(
            "Phải đặt DB_NAME=library_management_test trước khi chạy."
        )

    db = get_connection()
    cursor = db.cursor()
    user_id = None

    try:
        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]

        if database_name != "library_management_test":
            pytest.fail(
                f"Không được chạy Integration Test trên {database_name}"
            )

        user_repo = UserRepository(db)
        reader_repo = ReaderRepository(db)

        yield {
            "db": db,
            "user_repo": user_repo,
            "reader_repo": reader_repo,
            "auth": AuthService(user_repo, reader_repo),
            "member": MemberService(reader_repo, user_repo),
            "created_users": [],
        }

    finally:
        # Chỉ xóa tài khoản do bài test này tạo.
        # Việc xóa READERS được thực hiện bởi ON DELETE CASCADE.
        # Dọn dữ liệu trước khi đóng kết nối.
        if db.is_connected():
            db.close()


def test_register_login_and_update_profile(services):
    auth = services["auth"]
    member = services["member"]
    db = services["db"]

    unique = uuid.uuid4().hex[:12]
    username = f"test_{unique}"
    email = f"{username}@example.com"
    password = "Test@123456"

    user_id = None

    try:
        # 1. Đăng ký Reader
        # 1. Đăng ký Reader
# Kết thúc transaction đọc trước khi bắt đầu đăng ký
        db.rollback()
        user_id = auth.register_reader({
            "username": username,
            "full_name": "Integration Test User",
            "email": email,
            "password": password,
            "phone_number": "0900000000",
        })

        assert user_id is not None

        # 2. Đăng nhập
        login_result = auth.login(username, password)

        assert login_result["user_id"] == user_id
        assert login_result["role"] == "Reader"

        # 3. Kiểm tra mật khẩu đã được hash bằng bcrypt
        stored_user = services["user_repo"].find_by_username(username)

        assert stored_user["password"].startswith("$2")
        assert stored_user["password"] != password

        # 4. Lấy hồ sơ
        profile = member.get_my_profile(user_id)

        assert profile["username"] == username
        assert profile["email"] == email
        assert "password" not in profile

        # 5. Cập nhật hồ sơ
        new_name = "Updated Integration User"

        updated_profile = member.update_my_profile(
            user_id,
            {
                "full_name": new_name,
                "phone_number": "0911111111",
            }
        )

        assert updated_profile["full_name"] == new_name
        assert updated_profile["phone_number"] == "0911111111"

        # 6. Kiểm tra dữ liệu thực tế trong MySQL
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT full_name, phone_number "
                "FROM USERS WHERE userID = %s",
                (user_id,)
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

        assert row is not None
        assert row["full_name"] == new_name
        assert row["phone_number"] == "0911111111"

    finally:
        # Dọn tài khoản thử nghiệm, kể cả khi test thất bại.
        if user_id is None:
            # Trường hợp đăng ký thành công nhưng chưa nhận được ID.
            cursor = db.cursor()
            try:
                cursor.execute(
                    "SELECT userID FROM USERS WHERE username = %s",
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
            finally:
                cursor.close()

        if user_id is not None:
            cursor = db.cursor()
            try:
                cursor.execute(
                    "DELETE FROM READERS WHERE userID = %s",
                    (user_id,)
                )
                cursor.execute(
                    "DELETE FROM USERS WHERE userID = %s",
                    (user_id,)
                )
                db.commit()
            finally:
                cursor.close()
