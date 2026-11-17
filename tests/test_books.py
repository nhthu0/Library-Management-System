import pytest
from app.controllers.book_controller import BookController


@pytest.fixture
def admin_controller():
    return BookController(current_user={"user_id": 1, "username": "admin", "role": "ADMIN"})


@pytest.fixture
def reader_controller():
    return BookController(current_user={"user_id": 2, "username": "reader01", "role": "READER"})


def test_get_all_books(reader_controller):
    res = reader_controller.get_all_books()
    assert res["success"] is True
    assert isinstance(res["data"], list)


def test_reader_cannot_add_book(reader_controller):
    res = reader_controller.add_book({
        "title": "Unauthorized Book",
        "author": "Test",
        "category": "Test",
        "quantity": 3
    })
    assert res["success"] is False
    assert res["data"] is None


def test_admin_crud_book_lifecycle(admin_controller):
    # 1. Thêm sách mới
    add_res = admin_controller.add_book({
        "title": "Refactoring",
        "author": "Martin Fowler",
        "category": "Software Engineering",
        "publisher": "Addison-Wesley",
        "publication_year": 2018,
        "quantity": 4
    })
    assert add_res["success"] is True
    new_id = add_res["data"]["book_id"]

    # 2. Xem chi tiết, tìm kiếm và kiểm tra số lượng khả dụng
    assert admin_controller.get_book_by_id(new_id)["success"] is True
    assert admin_controller.search_books("Refactoring")["success"] is True
    assert admin_controller.check_book_availability(new_id)["data"]["is_available"] is True

    # 3. Cập nhật sách
    upd_res = admin_controller.update_book(new_id, {"quantity": 0})
    assert upd_res["success"] is True
    assert upd_res["data"]["status"] == "Unavailable"
    assert upd_res["data"]["available_quantity"] == 0

    # 4. Xóa sách
    del_res = admin_controller.delete_book(new_id)
    assert del_res["success"] is True