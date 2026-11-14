from pathlib import Path
import shutil
from inflow.parsers import detect_and_parse

FIX=Path(__file__).parent/"fixtures"
def test_bank_a_fixture():
    rows,opening=detect_and_parse(FIX/"bank_a_fixture.csv")
    assert opening==1000 and rows[0].amount== -100

def test_bank_b_fixture():
    rows,opening=detect_and_parse(FIX/"bank_b_fixture.xlsx")
    assert opening is None and rows[0]["amount"]==500

def test_bank_c_wrapped_narration_and_page_break():
    rows,opening=detect_and_parse(FIX/"bank_c_fixture.txt")
    assert rows[0]["description"]=="AMAZON PAYMENT XYZ ONLINE ORDER DETAIL"
    assert len(rows)==2 and opening==1000

def test_content_detection_ignores_wrong_extension(tmp_path):
    target=tmp_path/"random_name.not_csv"
    shutil.copy(FIX/"bank_a_fixture.csv",target)
    rows,opening=detect_and_parse(target)
    assert rows[0].description=="UPI PAYMENT"
