import csv
from pathlib import Path


def export_report_to_csv(
    report_data: dict,
    file_path: str
) -> str:
    """Export report data to a CSV file."""

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

            writer.writerow(["Section", "Metric", "Value"])

            for section, content in report_data.items():
                if isinstance(content, dict):
                    for key, value in content.items():
                        writer.writerow([section, key, value])

                elif isinstance(content, list):
                    for index, item in enumerate(content, start=1):
                        if isinstance(item, dict):
                            for key, value in item.items():
                                writer.writerow([
                                    section,
                                    f"{index} - {key}",
                                    value
                                ])
                        else:
                            writer.writerow([section, index, item])

                else:
                    writer.writerow(["Summary", section, content])

        return str(output_path)

    except OSError as error:
        raise OSError(
            "Unable to export report to CSV."
        ) from error
