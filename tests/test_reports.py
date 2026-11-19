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


# ==============================
# LMS-49: CSV Exporter Tests
# ==============================

import csv

from app.utils.csv_exporter import export_report_to_csv


def test_export_report_to_csv_success(tmp_path):
    report_data = {
        "book_statistics": {
            "total_titles": 100,
            "total_quantity": 500
        },
        "by_category": [
            {
                "category": "Lập trình",
                "total_titles": 60
            }
        ]
    }

    file_path = tmp_path / "report.csv"

    result = export_report_to_csv(report_data, str(file_path))

    assert result == str(file_path)
    assert file_path.exists()

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:
        rows = list(csv.reader(csv_file))

    assert rows[0] == ["Section", "Metric", "Value"]
    assert ["book_statistics", "total_titles", "100"] in rows
    assert ["book_statistics", "total_quantity", "500"] in rows
    assert ["by_category", "1 - category", "Lập trình"] in rows


def test_export_report_to_csv_empty_report(tmp_path):
    file_path = tmp_path / "empty.csv"

    export_report_to_csv({}, str(file_path))

    assert file_path.exists()


def test_export_report_to_csv_rejects_invalid_data(tmp_path):
    file_path = tmp_path / "invalid.csv"

    with pytest.raises(ValueError):
        export_report_to_csv(["invalid"], str(file_path))


def test_export_report_to_csv_rejects_invalid_path():
    with pytest.raises(ValueError):
        export_report_to_csv({"total": 10}, "")


# ==============================
# LMS-49: Book Status Statistics Tests
# ==============================

class FakeLMS49Repository:

    def __init__(self):
        self.book_status_called = False
        self.fine_statistics_called = False

    def get_book_status_statistics(self):
        self.book_status_called = True
        return {
            "currently_borrowed": 10,
            "returned": 20,
            "overdue": 3
        }

    def get_fine_statistics(self):
        self.fine_statistics_called = True
        return {
            "total_fines": 8,
            "total_amount": 500000,
            "paid_amount": 300000,
            "unpaid_amount": 200000,
            "paid_count": 5,
            "unpaid_count": 3
        }


@pytest.fixture
def lms49_service():
    service = ReportService()
    service.repo = FakeLMS49Repository()
    return service


def test_admin_can_get_book_status_statistics(
    lms49_service,
    admin_user
):
    result = lms49_service.get_book_status_statistics(admin_user)

    assert result["currently_borrowed"] == 10
    assert result["returned"] == 20
    assert result["overdue"] == 3
    assert lms49_service.repo.book_status_called is True


def test_reader_cannot_get_book_status_statistics(
    lms49_service,
    reader_user
):
    with pytest.raises(PermissionError):
        lms49_service.get_book_status_statistics(reader_user)

    assert lms49_service.repo.book_status_called is False


def test_book_status_statistics_requires_login(lms49_service):
    with pytest.raises(PermissionError):
        lms49_service.get_book_status_statistics(None)

    assert lms49_service.repo.book_status_called is False


def test_admin_can_get_fine_statistics(
    lms49_service,
    admin_user
):
    result = lms49_service.get_fine_statistics(admin_user)

    assert result["total_fines"] == 8
    assert result["total_amount"] == 500000
    assert result["paid_amount"] == 300000
    assert result["unpaid_amount"] == 200000
    assert result["paid_count"] == 5
    assert result["unpaid_count"] == 3
    assert lms49_service.repo.fine_statistics_called is True


def test_reader_cannot_get_fine_statistics(
    lms49_service,
    reader_user
):
    with pytest.raises(PermissionError):
        lms49_service.get_fine_statistics(reader_user)

    assert lms49_service.repo.fine_statistics_called is False


def test_fine_statistics_requires_login(lms49_service):
    with pytest.raises(PermissionError):
        lms49_service.get_fine_statistics(None)

    assert lms49_service.repo.fine_statistics_called is False


# ==============================
# LMS-49: Report Controller Tests
# ==============================

def test_controller_get_book_status_statistics_success(admin_user):
    controller = ReportController(admin_user)

    expected = {
        "currently_borrowed": 10,
        "returned": 20,
        "overdue": 3
    }

    class FakeService:
        def get_book_status_statistics(self, current_user):
            assert current_user == admin_user
            return expected

    controller.service = FakeService()
    result = controller.get_book_status_statistics()

    assert result["success"] is True
    assert result["data"] == expected


def test_controller_book_status_statistics_permission_error(reader_user):
    controller = ReportController(reader_user)

    class FakeService:
        def get_book_status_statistics(self, current_user):
            raise PermissionError("Admin permission required.")

    controller.service = FakeService()
    result = controller.get_book_status_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Admin permission required."


def test_controller_book_status_statistics_database_error(admin_user):
    import mysql.connector

    controller = ReportController(admin_user)

    class FakeService:
        def get_book_status_statistics(self, current_user):
            raise mysql.connector.Error("Database details")

    controller.service = FakeService()
    result = controller.get_book_status_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert "Database error" in result["message"]


def test_controller_book_status_statistics_unexpected_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def get_book_status_statistics(self, current_user):
            raise RuntimeError("Internal error details.")

    controller.service = FakeService()
    result = controller.get_book_status_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "An unexpected error occurred."
    assert "Internal error details." not in result["message"]


def test_controller_get_fine_statistics_success(admin_user):
    controller = ReportController(admin_user)

    expected = {
        "total_fines": 8,
        "total_amount": 500000,
        "paid_amount": 300000,
        "unpaid_amount": 200000,
        "paid_count": 5,
        "unpaid_count": 3
    }

    class FakeService:
        def get_fine_statistics(self, current_user):
            assert current_user == admin_user
            return expected

    controller.service = FakeService()
    result = controller.get_fine_statistics()

    assert result["success"] is True
    assert result["data"] == expected


def test_controller_fine_statistics_permission_error(reader_user):
    controller = ReportController(reader_user)

    class FakeService:
        def get_fine_statistics(self, current_user):
            raise PermissionError("Admin permission required.")

    controller.service = FakeService()
    result = controller.get_fine_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Admin permission required."


def test_controller_fine_statistics_database_error(admin_user):
    import mysql.connector

    controller = ReportController(admin_user)

    class FakeService:
        def get_fine_statistics(self, current_user):
            raise mysql.connector.Error("Database details")

    controller.service = FakeService()
    result = controller.get_fine_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert "Database error" in result["message"]


def test_controller_fine_statistics_unexpected_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def get_fine_statistics(self, current_user):
            raise RuntimeError("Internal error details.")

    controller.service = FakeService()
    result = controller.get_fine_statistics()

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "An unexpected error occurred."
    assert "Internal error details." not in result["message"]


# ==============================
# LMS-49: Report Export Service Tests
# ==============================

def test_admin_can_export_fine_statistics(
    lms49_service,
    admin_user,
    monkeypatch,
    tmp_path
):
    file_path = str(tmp_path / "fines.csv")
    captured = {}

    def fake_export(report_data, output_path):
        captured["report_data"] = report_data
        captured["file_path"] = output_path
        return output_path

    monkeypatch.setattr(
        "app.services.report_service.export_report_to_csv",
        fake_export
    )

    result = lms49_service.export_report(
        "fine_statistics",
        file_path,
        admin_user
    )

    assert result == file_path
    assert captured["file_path"] == file_path
    assert captured["report_data"]["total_fines"] == 8
    assert lms49_service.repo.fine_statistics_called is True


def test_reader_cannot_export_report(
    lms49_service,
    reader_user,
    tmp_path
):
    file_path = str(tmp_path / "fines.csv")

    with pytest.raises(PermissionError):
        lms49_service.export_report(
            "fine_statistics",
            file_path,
            reader_user
        )

    assert lms49_service.repo.fine_statistics_called is False


def test_export_report_rejects_unsupported_type(
    lms49_service,
    admin_user,
    tmp_path
):
    with pytest.raises(ValueError):
        lms49_service.export_report(
            "invalid_report",
            str(tmp_path / "report.csv"),
            admin_user
        )


def test_export_borrowing_report_requires_dates(
    lms49_service,
    admin_user,
    tmp_path
):
    with pytest.raises(ValueError):
        lms49_service.export_report(
            "borrowing_report",
            str(tmp_path / "borrowing.csv"),
            admin_user
        )


# ==============================
# LMS-49: Report Export Controller Tests
# ==============================

def test_controller_export_report_success(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def export_report(
            self, report_type, file_path, current_user,
            start_date, end_date
        ):
            assert report_type == "fine_statistics"
            assert current_user == admin_user
            return file_path

    controller.service = FakeService()

    result = controller.export_report(
        "fine_statistics",
        "/tmp/fines.csv"
    )

    assert result["success"] is True
    assert result["data"]["file_path"] == "/tmp/fines.csv"


def test_controller_export_report_permission_error(reader_user):
    controller = ReportController(reader_user)

    class FakeService:
        def export_report(self, *args):
            raise PermissionError("Admin permission required.")

    controller.service = FakeService()
    result = controller.export_report("fine_statistics", "/tmp/fines.csv")

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Admin permission required."


def test_controller_export_report_os_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def export_report(self, *args):
            raise OSError("Private file system details.")

    controller.service = FakeService()
    result = controller.export_report("fine_statistics", "/tmp/fines.csv")

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "Unable to export report to CSV."


def test_controller_export_report_database_error(admin_user):
    import mysql.connector

    controller = ReportController(admin_user)

    class FakeService:
        def export_report(self, *args):
            raise mysql.connector.Error("Database details.")

    controller.service = FakeService()
    result = controller.export_report("fine_statistics", "/tmp/fines.csv")

    assert result["success"] is False
    assert result["data"] is None
    assert "Database error" in result["message"]


def test_controller_export_report_unexpected_error(admin_user):
    controller = ReportController(admin_user)

    class FakeService:
        def export_report(self, *args):
            raise RuntimeError("Internal details.")

    controller.service = FakeService()
    result = controller.export_report("fine_statistics", "/tmp/fines.csv")

    assert result["success"] is False
    assert result["data"] is None
    assert result["message"] == "An unexpected error occurred."
    assert "Internal details." not in result["message"]
