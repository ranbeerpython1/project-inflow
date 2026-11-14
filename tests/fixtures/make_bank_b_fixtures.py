"""Generate adversarial Bank B XLSX fixtures for Task 1 tests.

Run once: python tests/fixtures/make_bank_b_fixtures.py
"""
from openpyxl import Workbook
from pathlib import Path
from decimal import Decimal
import datetime

FIXTURES = Path(__file__).parent


def make_cdr_fixture():
    """XLSX with Cr/Dr balance text, mixed positive and negative amounts."""
    wb = Workbook()
    ws = wb.active
    ws.append(["Account", "FIXB2"])
    ws.append(["Date", "Narration", "Amount", "Balance"])
    ws.append([None, None, None, None])  # blank separator row

    rows = [
        # (date_str, narration, amount_str, balance_str)
        ("01/01/2026", "SALARY CREDIT",      "42000.00",  "92000.00 Cr"),
        ("05/01/2026", "NACH EMI HOME LOAN", "-1800.00",  "90200.00 Cr"),
        ("15/01/2026", "ATM CASH WITHDRAWAL","-900.00",   "89300.00 Cr"),
        ("20/01/2026", "INTEREST CREDIT",     "125.00",   "89425.00 Cr"),
        ("25/01/2026", "LARGE DEBIT",         "-90000.00","610.00 Dr"),   # goes negative → Dr balance
        ("28/01/2026", "SALARY CREDIT",       "42000.00", "41390.00 Cr"),
    ]

    for date_str, narr, amt, bal in rows:
        # Store date as a plain string (not datetime) to exercise the
        # strptime fallback path in bank_b.parse_b.
        ws.append([date_str, narr, amt, bal])

    wb.save(FIXTURES / "bank_b_cdr.xlsx")


def make_datetime_fixture():
    """XLSX where the Date column contains real datetime objects (normal path)."""
    wb = Workbook()
    ws = wb.active
    ws.append(["Account", "FIXB3"])
    ws.append(["Date", "Narration", "Amount", "Balance"])
    ws.append([None, None, None, None])

    rows = [
        (datetime.datetime(2026, 1, 1),  "SALARY CREDIT",       "42000.00", "92000.00 Cr"),
        (datetime.datetime(2026, 1, 5),  "NACH EMI HOME LOAN",  "-1800.00", "90200.00 Cr"),
        (datetime.datetime(2026, 1, 15), "ATM CASH WITHDRAWAL",  "-900.00", "89300.00 Cr"),
    ]

    for dt, narr, amt, bal in rows:
        ws.append([dt, narr, amt, bal])

    wb.save(FIXTURES / "bank_b_datetime.xlsx")


if __name__ == "__main__":
    make_cdr_fixture()
    make_datetime_fixture()
    print("Fixtures written.")
