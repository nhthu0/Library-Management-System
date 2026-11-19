import mysql.connector
from app.services.book_service import BookService


class BookController:
    def __init__(self, current_user: dict | None = None):
        self.service = BookService()
        self.current_user = current_user

    def set_current_user(self, current_user: dict | None):
        self.current_user = current_user

    def _success(self, message: str, data=None) -> dict:
        return {
            "success": True,
            "message": message,
            "data": data
        }

    def _error(self, message: str) -> dict:
        return {
            "success": False,
            "message": message,
            "data": None
        }

    def get_all_books(self) -> dict:
        try:
            books = self.service.get_all_books()
            return self._success("Retrieved all books successfully.", books)
        except (ValueError, PermissionError) as e:
            return self._error(str(e))
        except mysql.connector.Error:
            return self._error("Database error occurred while retrieving books.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def get_book_by_id(self, book_id: int) -> dict:
        try:
            book = self.service.get_book_by_id(book_id)
            return self._success("Retrieved book details successfully.", book)
        except (ValueError, PermissionError) as e:
            return self._error(str(e))
        except mysql.connector.Error:
            return self._error("Database error occurred while retrieving book details.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def search_books(self, keyword: str) -> dict:
        try:
            books = self.service.search_books(keyword)
            return self._success("Search completed successfully.", books)
        except (ValueError, PermissionError) as e:
            return self._error(str(e))
        except mysql.connector.Error:
            return self._error("Database error occurred while searching books.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def check_book_availability(self, book_id: int) -> dict:
        try:
            availability = self.service.check_book_availability(book_id)
            return self._success("Checked book availability successfully.", availability)
        except (ValueError, PermissionError) as e:
            return self._error(str(e))
        except mysql.connector.Error:
            return self._error("Database error occurred while checking availability.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def add_book(self, book_data: dict) -> dict:
        try:
            created = self.service.add_book(book_data, self.current_user)
            return self._success("Book added successfully.", created)
        except (ValueError, PermissionError) as e:
            return self._error(str(e))
        except mysql.connector.Error:
            return self._error("Database error occurred while adding book.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def update_book(self, book_id: int, book_data: dict) -> dict:
        try:
            updated = self.service.update_book(book_id, book_data, self.current_user)
            return self._success("Book updated successfully.", updated)
        except (ValueError, PermissionError) as e:
            return self._error(str(e))
        except mysql.connector.Error:
            return self._error("Database error occurred while updating book.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def delete_book(self, book_id: int) -> dict:
        try:
            deleted = self.service.delete_book(book_id, self.current_user)
            return self._success("Book deleted successfully.", deleted)
        except (ValueError, PermissionError) as e:
            return self._error(str(e))
        except mysql.connector.Error:
            return self._error("Database error occurred while deleting book.")
        except Exception:
            return self._error("An unexpected error occurred.")