from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.controllers.auth_controller import AuthController
from app.services.auth_service import AuthService
from app.views.login_view import LoginView
from app.views.register_view import RegisterView
from main import LibraryManagementApp


@pytest.fixture
def auth():
    return AuthService(Mock(), Mock())


@pytest.mark.parametrize(
    ("password", "expected_error"),
    [
        pytest.param("123456", None, id="TC01"),
        pytest.param(
            "wrongpass",
            "Tên đăng nhập hoặc mật khẩu không chính xác.",
            id="TC02",
        ),
    ],
)
def test_sign_in(auth, password, expected_error):
    auth.user_repo.find_by_username.return_value = {
        "userID": 101,
        "username": "student01",
        "password": auth.hash_password("123456"),
        "role": "Reader",
        "account_status": "Active",
        "readerID": 10,
    }
    view = Mock()
    view.username.get.return_value = "student01"
    view.password.get.return_value = password
    app = SimpleNamespace(
        auth_controller=AuthController(auth),
        current_view=view,
        current_user=None,
        show_reader_dashboard=Mock(),
        show_admin_dashboard=Mock(),
    )
    view.on_login = lambda username, value: LibraryManagementApp.handle_login(
        app, username, value
    )

    LoginView.handle_login(view)

    auth.user_repo.find_by_username.assert_called_once_with("student01")
    app.show_admin_dashboard.assert_not_called()
    if expected_error is None:
        assert app.current_user["user_id"] == 101
        assert app.current_user["reader_id"] == 10
        app.show_reader_dashboard.assert_called_once_with()
        view.message.configure.assert_not_called()
    else:
        assert app.current_user is None
        app.show_reader_dashboard.assert_not_called()
        view.message.configure.assert_called_once_with(text=expected_error)


def test_register_reader_tc03(auth, monkeypatch):
    auth.user_repo.find_by_username.return_value = None
    auth.reader_repo.create_reader.return_value = 101
    show_info = Mock()
    monkeypatch.setattr("main.messagebox.showinfo", show_info)
    view = Mock(admin_mode=False)
    view.username.get.return_value = "student01"
    view.full_name.get.return_value = "John"
    view.email.get.return_value = "john@gmail.com"
    view.phone.get.return_value = "0900000000"
    view.password.get.return_value = "123456"
    view.confirm_password.get.return_value = "123456"
    view.agree.get.return_value = True
    app = SimpleNamespace(
        auth_controller=AuthController(auth),
        current_view=view,
        show_login=Mock(),
    )
    view.on_register = lambda data: LibraryManagementApp.submit_registration(app, data)

    RegisterView.handle_register(view)

    view.show_error.assert_not_called()
    auth.user_repo.find_by_username.assert_called_once_with("student01")
    auth.reader_repo.create_reader.assert_called_once()
    saved = auth.reader_repo.create_reader.call_args.args[0]
    assert saved == {
        "username": "student01",
        "full_name": "John",
        "email": "john@gmail.com",
        "phone_number": "0900000000",
        "password": saved["password"],
    }
    assert saved["password"] != "123456"
    assert auth.verify_password("123456", saved["password"])
    app.show_login.assert_called_once_with()
    show_info.assert_called_once_with(
        "Registration", "Đăng ký tài khoản thành công", parent=app
    )
