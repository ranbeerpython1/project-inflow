"""
Task 1 – Adversarial fixture tests.

Covers:
  • Bank A CSV with comma-formatted amounts
  • Bank B XLSX with Cr/Dr balance notation (absolute value + suffix)
  • Bank B XLSX with real datetime cells (not strings)
  • Bank C TXT multi-page statement with page-break headers
  • Bank C TXT with a long description that overflows into numeric columns
"""
from decimal import Decimal
from pathlib import Path
import pytest
from inflow.parsers import detect_and_parse

FIX = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Bank A – CSV
# ---------------------------------------------------------------------------

def test_bank_a_comma_formatted_amounts():
    """CSV with comma-thousands in withdrawal/deposit columns should parse correctly."""
    rows, opening = detect_and_parse(FIX / "bank_a_comma_amounts.csv")
    assert opening == Decimal("100000.00")
    assert len(rows) == 3
    # First row is a salary deposit
    assert rows[0].amount == Decimal("42000.00")
    assert rows[0].balance == Decimal("142000.00")
    # Second row is a debit
    assert rows[1].amount == Decimal("-1800.00")


# ---------------------------------------------------------------------------
# Bank B – XLSX Cr/Dr balance notation
# ---------------------------------------------------------------------------

def test_bank_b_cr_dr_positive_balance():
    """Rows tagged 'Cr' should produce a positive balance Decimal."""
    rows, opening = detect_and_parse(FIX / "bank_b_cdr.xlsx")
    # First four rows remain in credit (positive balance)
    for r in rows[:4]:
        assert r["balance"] > 0, f"Expected positive balance, got {r['balance']}"


def test_bank_b_cr_dr_negative_balance():
    """A row tagged 'Dr' with a positive absolute value must produce a negative balance."""
    rows, _ = detect_and_parse(FIX / "bank_b_cdr.xlsx")
    # Row index 4 (LARGE DEBIT) tips the account into overdraft → '610.00 Dr'
    # The parser must negate it because the raw number is positive and tag is Dr.
    dr_row = rows[4]
    assert dr_row["balance"] == Decimal("-610.00"), (
        f"Expected -610.00 for Dr balance, got {dr_row['balance']}"
    )


def test_bank_b_datetime_cells_parse_correctly():
    """XLSX cells storing real datetime objects must yield correct ISO dates."""
    rows, _ = detect_and_parse(FIX / "bank_b_datetime.xlsx")
    assert len(rows) == 3
    assert rows[0]["txn_date"] == "2026-01-01"
    assert rows[1]["txn_date"] == "2026-01-05"
    assert rows[2]["txn_date"] == "2026-01-15"


# ---------------------------------------------------------------------------
# Bank C – TXT multi-page
# ---------------------------------------------------------------------------

def test_bank_c_multipage_row_count():
    """Multi-page TXT fixture must yield all data rows, ignoring PAGE TOTAL lines."""
    rows, opening = detect_and_parse(FIX / "bank_c_multipage.txt")
    assert opening == Decimal("50000.00")
    # 11 rows page 1 (incl. 1 with wrapped narration) + 8 rows page 2 partial
    # + 3 rows after second page break = 22 rows total
    assert len(rows) == 22


def test_bank_c_multipage_page_break_skipped():
    """PAGE TOTAL / END OF PAGE lines must not appear as transactions."""
    rows, _ = detect_and_parse(FIX / "bank_c_multipage.txt")
    dates = {r["txn_date"] for r in rows}
    # All parsed dates should be valid ISO strings, not header garbage
    for d in dates:
        assert len(d) == 10 and d[4] == "-" and d[7] == "-", f"Bad date: {d}"


def test_bank_c_multipage_wrapped_narration():
    """A description that wraps onto the next line must be concatenated."""
    rows, _ = detect_and_parse(FIX / "bank_c_multipage.txt")
    grocery_row = next(r for r in rows if r["description"].startswith("GROCERY MART POS VERY LONG"))
    assert "NAME CONTINUED ON NEXT LINE" in grocery_row["description"]


def test_bank_c_multipage_credit_row():
    """Credit-only rows (no debit) must produce a positive amount."""
    rows, _ = detect_and_parse(FIX / "bank_c_multipage.txt")
    salary_rows = [r for r in rows if "SALARY" in r["description"]]
    assert salary_rows, "Expected at least one SALARY row"
    for r in salary_rows:
        assert r["amount"] > 0, f"Salary should be positive, got {r['amount']}"


def test_bank_c_multipage_debit_row():
    """Debit-only rows must produce a negative amount."""
    rows, _ = detect_and_parse(FIX / "bank_c_multipage.txt")
    emi_rows = [r for r in rows if "EMI" in r["description"]]
    assert emi_rows, "Expected at least one EMI row"
    for r in emi_rows:
        assert r["amount"] < 0, f"EMI should be negative, got {r['amount']}"
