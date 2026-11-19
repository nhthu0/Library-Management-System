
import csv
from pathlib import Path


def _sanitize_csv_value(value):
    """
    Prevent CSV Formula Injection.
    Keep numeric values unchanged.
    """
    if not isinstance(value, str):
        return value

    normalized = value.lstrip(
        " \t\r\n\v\f"
    )

    if normalized.startswith(("=", "+", "-", "@")):
        return "'" + value

    return value


def export_report_to_csv(
    report_data: dict,
    file_path: str
) -> str:
    """Export report data to a CSV file safely."""

    if not isinstance(report_data, dict):
        raise ValueError("Report data must be a dictionary.")

    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("Invalid CSV file path.")

    output_path = Path(file_path)

    try:
        with output_path.open(
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as csv_file:

            writer = csv.writer(csv_file)

            writer.writerow([
                "Section",
                "Metric",
                "Value"
            ])

            for section, content in report_data.items():

                if isinstance(content, dict):
                    for key, value in content.items():
                        writer.writerow([
                            _sanitize_csv_value(section),
                            _sanitize_csv_value(key),
                            _sanitize_csv_value(value)
                        ])

                elif isinstance(content, list):
                    for index, item in enumerate(
                        content,
                        start=1
                    ):
                        if isinstance(item, dict):
                            for key, value in item.items():
                                writer.writerow([
                                    _sanitize_csv_value(section),
                                    _sanitize_csv_value(
                                        f"{index} - {key}"
                                    ),
                                    _sanitize_csv_value(value)
                                ])
                        else:
                            writer.writerow([
                                _sanitize_csv_value(section),
                                index,
                                _sanitize_csv_value(item)
                            ])

                else:
                    writer.writerow([
                        "Summary",
                        _sanitize_csv_value(section),
                        _sanitize_csv_value(content)
                    ])

        return str(output_path)

    except OSError as error:
        raise OSError(
            "Unable to export report to CSV."
        ) from error
