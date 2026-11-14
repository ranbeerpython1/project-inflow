import csv,json
from pathlib import Path
from inflow.features import run

def make_case(tmp_path, reason):
    out=tmp_path/"out";out.mkdir(); rows=[]
    # 3 months; create 1 salary credit and one EMI debit per month.
    for m in range(1,4):
        rows += [dict(account_id="A",txn_id=f"s{m}",txn_date=f"2026-0{m}-02",description="salary",amount="20000.00",balance="20000.00",source_file="x",source_line=str(m*2),category="SALARY",needs_review="false"),dict(account_id="A",txn_id=f"e{m}",txn_date=f"2026-0{m}-05",description="emi",amount="-5000.00",balance="15000.00",source_file="x",source_line=str(m*2+1),category="EMI_LOAN_REPAYMENT",needs_review="false")]
    if reason=="low_categorisation_coverage":
        for r in rows:
            if Decimal(r["amount"])<0:r["category"]="OTHER"
    with (out/"categorised.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/"reconciliation.json").write_text(json.dumps({"A":{"status":"fail" if reason=="reconciliation_failed" else "pass","issues":[]}}))
    return out
from decimal import Decimal

def test_reconciliation_failed_gate(tmp_path):
    assert "reconciliation_failed" in run(make_case(tmp_path,"reconciliation_failed"))["A"]["reasons"]

def test_low_categorisation_coverage_gate(tmp_path):
    assert "low_categorisation_coverage" in run(make_case(tmp_path,"low_categorisation_coverage"))["A"]["reasons"]

def test_insufficient_history_gate(tmp_path):
    out=tmp_path/"out";out.mkdir(); rows=[dict(account_id="A",txn_id="1",txn_date="2026-01-02",description="salary",amount="1000.00",balance="1000.00",source_file="x",source_line="1",category="SALARY",needs_review="false")]
    with (out/"categorised.csv").open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/"reconciliation.json").write_text(json.dumps({"A":{"status":"pass","issues":[]}}))
    assert "insufficient_history" in run(out)["A"]["reasons"]

def test_hand_computed_features_include_carry_forward_and_foir(tmp_path):
    out=tmp_path/"out";out.mkdir();rows=[]
    for month,opening in [(1,0),(2,8000),(3,16000)]:
        salary_balance=opening+10000
        rows.append(dict(account_id="A",txn_id=f"s{month}",txn_date=f"2026-{month:02d}-01",description="salary",amount="10000.00",balance=f"{salary_balance:.2f}",source_file="x",source_line=str(month*2),category="SALARY",needs_review="false"))
        rows.append(dict(account_id="A",txn_id=f"e{month}",txn_date=f"2026-{month:02d}-02",description="emi",amount="-2000.00",balance=f"{salary_balance-2000:.2f}",source_file="x",source_line=str(month*2+1),category="EMI_LOAN_REPAYMENT",needs_review="false"))
    with (out/"categorised.csv").open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/"reconciliation.json").write_text(json.dumps({"A":{"status":"pass","issues":[]}}))
    got=run(out)["A"]
    assert got["average_monthly_credits"]=="10000.00"
    assert got["salary"]["average_monthly_amount"]=="10000.00"
    assert got["average_monthly_emi_outflow"]=="2000.00"
    assert got["foir"]=="0.2000"
    assert got["minimum_end_of_day_balance"]=="8000.00"
    assert got["average_end_of_day_balance"]=="12295.08"
    assert got["salary"]["txn_ids"]==["s1","s2","s3"]
    assert got["emi_txn_ids"]==["e1","e2","e3"]
