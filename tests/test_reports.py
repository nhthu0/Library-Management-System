import pytest

from app.services.report_service import ReportService
from app.controllers.report_controller import ReportController


class FakeReportRepository:

    def __init__(self, statistics=None):
        self.statistics = statistics or {
            "total_titles": 100,
            "total_quantity": 500,
            "available_titles": 80,
            "unavailable_titles": 20,
            "by_category": [
                {
                    "category": "Programming",
                    "total_titles": 60,
                    "total_quantity": 300
                },
                {
                    "category": "Database",
                    "total_titles": 40,
                    "total_quantity": 200
                }
            ]
        }

        self.called = False

    def get_book_statistics(self):
        self.called = True
        return self.statistics


@pytest.fixture
def admin_user():
    return {
        "user_id": 1,
        "admin_id": 1,
        "username": "admin",
        "role": "ADMIN"
    }


@pytest.fixture
def reader_user():
    return {
        "user_id": 2,
        "reader_id": 2,
        "username": "reader",
        "role": "READER"
    }


@pytest.fixture
def report_service():
    service = ReportService()
    service.repo = FakeReportRepository()
    return service


# ==============================
# LMS-46: Book Statistics Tests
# ==============================

def test_admin_can_get_book_statistics(
    report_service,
    admin_user
):
    result = report_service.get_statistics(admin_user)

    assert result["total_titles"] == 100
    assert result["total_quantity"] == 500
    assert result["available_titles"] == 80
    assert result["unavailable_titles"] == 20

    assert len(result["by_category"]) == 2
    assert result["by_category"][0]["category"] == "Programming"


def test_statistics_repository_is_called(
    report_service,
    admin_user
):
    report_service.get_statistics(admin_user)

    assert report_service.repo.called is True


def test_reader_cannot_get_book_statistics(
    report_service,
    reader_user
):
    with pytest.raises(PermissionError):
        report_service.get_statistics(reader_user)

    assert report_service.repo.called is False


def test_statistics_require_login(report_service):
    with pytest.raises(PermissionError):
        report_service.get_statistics(None)

    assert report_service.repo.called is False


def test_admin_gets_empty_category_statistics(admin_user):
    service = ReportService()
    service.repo = FakeReportRepository({
        "total_titles": 0,
        "total_quantity": 0,
        "available_titles": 0,
        "unavailable_titles": 0,
        "by_category": []
    })

    result = service.get_statistics(admin_user)

    assert result["total_titles"] == 0
    assert result["total_quantity"] == 0
    assert result["available_titles"] == 0
    assert result["unavailable_titles"] == 0
    assert result["by_category"] == []


# ==============================
# LMS-46: Report Controller Tests
# ==============================

def test_controller_get_statistics_success(admin_user):
    controller = ReportController(admin_user)

    statistics = {
        "total_titles": 100,
        "total_quantity": 500,
        "available_titles": 80,
        "unavailable_titles": 20,
        "by_category": []
    }

    class FakeService:

        def get_statistics(self, current_user):
            assert current_user == admin_user
            return statistics

    controller.service = FakeService()

    result = controller.get_statistics()

    assert result["success"] is True
    assert result["data"] == statistics
    assert result["message"] == (
        "Retrieved book statistics successfully."
    )


def test_controller_permission_error(reader_user):
    controller = ReportController(reader_user)

    class FakeService:

        def get_statistics(self, current_user):
            raise PermissionError("Admin permission required.")

    controller.service = FakeService()

    result = controller.get_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Admin permission required."


def test_controller_database_error(admin_user):
    import mysql.connector

    controller = ReportController(admin_user)

    class FakeService:

        def get_statistics(self, current_user):
            raise mysql.connector.Error("Database details")

    controller.service = FakeService()

    result = controller.get_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == (
        "Database error occurred while retrieving statistics."
    )


def test_controller_unexpected_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:

        def get_statistics(self, current_user):
            raise RuntimeError("Internal error details.")

    controller.service = FakeService()

    result = controller.get_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "An unexpected error occurred."
    assert "Internal error details." not in result["message"]

# ==================================================
# LMS-47: READER STATISTICS - TESTS
# ==================================================

class FakeReaderStatisticsRepository:

    def __init__(self, statistics=None):
        self.statistics = statistics or {
            "total_readers": 100,
            "active_readers": 70,
            "locked_readers": 20,
            "inactive_readers": 10,
            "by_status": [
                {"account_status": "Active", "total_readers": 70},
                {"account_status": "Inactive", "total_readers": 10},
                {"account_status": "Locked", "total_readers": 20}
            ]
        }
        self.called = False

    def get_reader_statistics(self):
        self.called = True
        return self.statistics


@pytest.fixture
def reader_statistics_service():
    service = ReportService()
    service.repo = FakeReaderStatisticsRepository()
    return service


def test_admin_can_get_reader_statistics(
    reader_statistics_service, admin_user
):
    result = reader_statistics_service.get_reader_statistics(admin_user)

    assert result["total_readers"] == 100
    assert result["active_readers"] == 70
    assert result["locked_readers"] == 20
    assert result["inactive_readers"] == 10
    assert len(result["by_status"]) == 3


def test_reader_statistics_repository_is_called(
    reader_statistics_service, admin_user
):
    reader_statistics_service.get_reader_statistics(admin_user)
    assert reader_statistics_service.repo.called is True


def test_reader_cannot_get_reader_statistics(
    reader_statistics_service, reader_user
):
    with pytest.raises(PermissionError):
        reader_statistics_service.get_reader_statistics(reader_user)

    assert reader_statistics_service.repo.called is False


def test_reader_statistics_require_login(reader_statistics_service):
    with pytest.raises(PermissionError):
        reader_statistics_service.get_reader_statistics(None)

    assert reader_statistics_service.repo.called is False


def test_admin_gets_empty_reader_statistics(admin_user):
    service = ReportService()
    service.repo = FakeReaderStatisticsRepository({
        "total_readers": 0,
        "active_readers": 0,
        "locked_readers": 0,
        "inactive_readers": 0,
        "by_status": []
    })

    result = service.get_reader_statistics(admin_user)

    assert result["total_readers"] == 0
    assert result["active_readers"] == 0
    assert result["locked_readers"] == 0
    assert result["inactive_readers"] == 0
    assert result["by_status"] == []


def test_controller_get_reader_statistics_success(admin_user):
    controller = ReportController(admin_user)

    statistics = {
        "total_readers": 100,
        "active_readers": 70,
        "locked_readers": 20,
        "inactive_readers": 10,
        "by_status": []
    }

    class FakeService:
        def get_reader_statistics(self, current_user):
            assert current_user == admin_user
            return statistics

    controller.service = FakeService()
    result = controller.get_reader_statistics()

    assert result["success"] is True
    assert result["data"] == statistics
    assert result["message"] == (
        "Retrieved reader statistics successfully."
    )


def test_controller_reader_statistics_permission_error(reader_user):
    controller = ReportController(reader_user)

    class FakeService:
        def get_reader_statistics(self, current_user):
            raise PermissionError("Admin permission required.")

    controller.service = FakeService()
    result = controller.get_reader_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Admin permission required."


def test_controller_reader_statistics_database_error(admin_user):
    import mysql.connector

    controller = ReportController(admin_user)

    class FakeService:
        def get_reader_statistics(self, current_user):
            raise mysql.connector.Error("Database details")

    controller.service = FakeService()
    result = controller.get_reader_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == (
        "Database error occurred while retrieving reader statistics."
    )


def test_controller_reader_statistics_unexpected_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def get_reader_statistics(self, current_user):
            raise RuntimeError("Internal error details.")

    controller.service = FakeService()
    result = controller.get_reader_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "An unexpected error occurred."
    assert "Internal error details." not in result["message"]


# ==================================================
# LMS-48: BORROWING AND RETURNING STATISTICS
# ==================================================

class FakeBorrowingReportRepository:

    def __init__(self, statistics=None):
        self.statistics = statistics or {
            "total_borrowings": 25,
            "total_returns": 20,
            "borrowings_by_date": [
                {"report_date": "2026-11-10", "total": 10},
                {"report_date": "2026-11-11", "total": 15}
            ],
            "returns_by_date": [
                {"report_date": "2026-11-12", "total": 20}
            ]
        }
        self.called = False
        self.received_dates = None

    def get_borrowing_report(self, start_date, end_date):
        self.called = True
        self.received_dates = (start_date, end_date)
        return self.statistics


@pytest.fixture
def borrowing_report_service():
    service = ReportService()
    service.repo = FakeBorrowingReportRepository()
    return service


def test_admin_can_get_borrowing_report(
    borrowing_report_service, admin_user
):
    result = borrowing_report_service.get_borrowing_report(
        "2026-11-01",
        "2026-11-30",
        admin_user
    )

    assert result["total_borrowings"] == 25
    assert result["total_returns"] == 20
    assert len(result["borrowings_by_date"]) == 2
    assert len(result["returns_by_date"]) == 1


def test_borrowing_report_repository_is_called(
    borrowing_report_service, admin_user
):
    borrowing_report_service.get_borrowing_report(
        "2026-11-01",
        "2026-11-30",
        admin_user
    )

    assert borrowing_report_service.repo.called is True
    assert borrowing_report_service.repo.received_dates == (
        "2026-11-01",
        "2026-11-30"
    )


def test_reader_cannot_get_borrowing_report(
    borrowing_report_service, reader_user
):
    with pytest.raises(PermissionError):
        borrowing_report_service.get_borrowing_report(
            "2026-11-01",
            "2026-11-30",
            reader_user
        )

    assert borrowing_report_service.repo.called is False


def test_borrowing_report_requires_login(borrowing_report_service):
    with pytest.raises(PermissionError):
        borrowing_report_service.get_borrowing_report(
            "2026-11-01",
            "2026-11-30",
            None
        )

    assert borrowing_report_service.repo.called is False


@pytest.mark.parametrize(
    "start_date,end_date",
    [
        ("2026-13-01", "2026-11-30"),
        ("invalid", "2026-11-30"),
        ("2026-11-01", "2026/11/30"),
        ("20261101", "20261130")
    ]
)
def test_borrowing_report_rejects_invalid_dates(
    borrowing_report_service, admin_user, start_date, end_date
):
    with pytest.raises(ValueError):
        borrowing_report_service.get_borrowing_report(
            start_date,
            end_date,
            admin_user
        )

    assert borrowing_report_service.repo.called is False


def test_borrowing_report_rejects_start_date_after_end_date(
    borrowing_report_service, admin_user
):
    with pytest.raises(ValueError, match="Start date must not be after end date"):
        borrowing_report_service.get_borrowing_report(
            "2026-11-30",
            "2026-11-01",
            admin_user
        )

    assert borrowing_report_service.repo.called is False


def test_borrowing_report_rejects_non_string_dates(
    borrowing_report_service, admin_user
):
    with pytest.raises(ValueError):
        borrowing_report_service.get_borrowing_report(
            None,
            "2026-11-30",
            admin_user
        )

    assert borrowing_report_service.repo.called is False


def test_controller_get_borrowing_report_success(admin_user):
    controller = ReportController(admin_user)

    statistics = {
        "total_borrowings": 25,
        "total_returns": 20,
        "borrowings_by_date": [],
        "returns_by_date": []
    }

    class FakeService:
        def get_borrowing_report(
            self, start_date, end_date, current_user
        ):
            assert start_date == "2026-11-01"
            assert end_date == "2026-11-30"
            assert current_user == admin_user
            return statistics

    controller.service = FakeService()

    result = controller.get_borrowing_report(
        "2026-11-01",
        "2026-11-30"
    )

    assert result["success"] is True
    assert result["data"] == statistics
    assert result["message"] == (
        "Retrieved borrowing and returning statistics successfully."
    )


def test_controller_borrowing_report_permission_error(reader_user):
    controller = ReportController(reader_user)

    class FakeService:
        def get_borrowing_report(
            self, start_date, end_date, current_user
        ):
            raise PermissionError("Admin permission required.")

    controller.service = FakeService()

    result = controller.get_borrowing_report(
        "2026-11-01",
        "2026-11-30"
    )

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Admin permission required."


def test_controller_borrowing_report_validation_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def get_borrowing_report(
            self, start_date, end_date, current_user
        ):
            raise ValueError("Invalid date format.")

    controller.service = FakeService()

    result = controller.get_borrowing_report(
        "invalid",
        "2026-11-30"
    )

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Invalid date format."


def test_controller_borrowing_report_database_error(admin_user):
    import mysql.connector

    controller = ReportController(admin_user)

    class FakeService:
        def get_borrowing_report(
            self, start_date, end_date, current_user
        ):
            raise mysql.connector.Error("Database details")

    controller.service = FakeService()

    result = controller.get_borrowing_report(
        "2026-11-01",
        "2026-11-30"
    )

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == (
        "Database error occurred while retrieving borrowing and returning statistics."
    )


def test_controller_borrowing_report_unexpected_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def get_borrowing_report(
            self, start_date, end_date, current_user
        ):
            raise RuntimeError("Internal error details.")

    controller.service = FakeService()

    result = controller.get_borrowing_report(
        "2026-11-01",
        "2026-11-30"
    )

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "An unexpected error occurred."
    assert "Internal error details." not in result["message"]
