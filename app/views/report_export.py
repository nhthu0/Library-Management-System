from pathlib import Path


def report_rows(report):
    loans = {str(row["report_date"]): row["total"] for row in report["borrowings_by_date"]}
    returns = {str(row["report_date"]): row["total"] for row in report["returns_by_date"]}
    return [
        (day, loans.get(day, 0), returns.get(day, 0))
        for day in sorted(loans.keys() | returns.keys())
    ]


def save_report(path, start, end, report):
    rows = report_rows(report)
    headings = ("Date", "Loans", "Returns")
    totals = ("Total", report["total_borrowings"], report["total_returns"])
    title = f"Borrowing report  {start} to {end}"
    suffix = Path(path).suffix.lower()
    if suffix == ".xlsx":
        from openpyxl import Workbook
        book = Workbook()
        sheet = book.active
        sheet.title = "Borrowing report"
        for row in [(title,), headings, totals, *rows]:
            sheet.append(row)
        sheet.column_dimensions["A"].width = 32
        book.save(path)
    elif suffix == ".pdf":
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.figure import Figure
        with PdfPages(path) as pdf:
            for offset in range(0, max(1, len(rows)), 25):
                figure = Figure(figsize=(8.27, 11.69))
                figure.suptitle(title)
                axes = figure.add_subplot()
                axes.axis("off")
                table = axes.table(
                    cellText=[totals, *rows[offset:offset + 25]],
                    colLabels=headings, loc="upper center", cellLoc="left"
                )
                table.scale(1, 1.5)
                pdf.savefig(figure)
    else:
        raise ValueError("Choose an .xlsx or .pdf file.")
