import argparse,csv,json
from collections import defaultdict
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median

def run(out_dir,output=None):
 p=Path(out_dir); rows=list(csv.DictReader((p/"categorised.csv").open(encoding="utf-8"))); rec=json.loads((p/"reconciliation.json").read_text()); groups=defaultdict(list)
 for r in rows:groups[r["account_id"]].append(r)
 result={}
 for aid,rs in groups.items():
  rs.sort(key=lambda x:(x["txn_date"],int(x["source_line"]))); months=sorted({r["txn_date"][:7] for r in rs}); credits=[r for r in rs if Decimal(r["amount"])>0]; debits=[r for r in rs if Decimal(r["amount"])<0]
  salary=[r for r in credits if r["category"]=="SALARY"]; emis=[r for r in debits if r["category"]=="EMI_LOAN_REPAYMENT"]; bounces=[r for r in rs if r["category"]=="BOUNCE_RETURN"]; charges=[r for r in debits if r["category"]=="BOUNCE_CHARGE"]
  monthly_credits=[]
  for m in months:monthly_credits.append(sum((Decimal(r["amount"]) for r in credits if r["txn_date"].startswith(m)),Decimal("0")))
  monthly_salary=[]
  for m in months:monthly_salary.append(sum((Decimal(r["amount"]) for r in salary if r["txn_date"].startswith(m)),Decimal("0")))
  monthly_emi=[]
  for m in months:monthly_emi.append(sum((-Decimal(r["amount"]) for r in emis if r["txn_date"].startswith(m)),Decimal("0")))
  salary_avg=sum(monthly_salary,Decimal("0"))/Decimal(len(months)) if months else Decimal("0"); emi_avg=sum(monthly_emi,Decimal("0"))/Decimal(len(months)) if months else Decimal("0")
  # End-of-day balance carries forward on calendar days without transactions.
  daily={}
  for r in rs:daily[r["txn_date"]]=Decimal(r["balance"])
  start=date.fromisoformat(rs[0]["txn_date"]); end=date.fromisoformat(rs[-1]["txn_date"]); cur=start; last=Decimal(rs[0]["balance"]); eod=[]
  while cur<=end:
   if cur.isoformat() in daily:last=daily[cur.isoformat()]
   eod.append(last);cur+=timedelta(days=1)
  debit_value=sum((-Decimal(r["amount"]) for r in debits),Decimal("0")); questionable=sum((-Decimal(r["amount"]) for r in debits if r["category"]=="OTHER" or str(r["needs_review"]).lower()=="true"),Decimal("0")); coverage=questionable/debit_value if debit_value else Decimal("0")
  reasons=[]
  if rec.get(aid,{}).get("status")!="pass":reasons.append("reconciliation_failed")
  if coverage>Decimal("0.05"):reasons.append("low_categorisation_coverage")
  if len(months)<3:reasons.append("insufficient_history")
  result[aid]={"status":"needs_review" if reasons else "ready","reasons":reasons,"months_of_history":len(months),"average_monthly_credits":str((sum(monthly_credits,Decimal("0"))/Decimal(len(months))).quantize(Decimal(".01"))) if months else None,"salary":{"average_monthly_amount":str(salary_avg.quantize(Decimal(".01"))) if salary else None,"months_detected":len({r['txn_date'][:7] for r in salary}),"median_credit_day":median(int(r["txn_date"][8:10]) for r in salary) if salary else None,"txn_ids":[r["txn_id"] for r in salary]},"average_monthly_emi_outflow":str(emi_avg.quantize(Decimal(".01"))),"emi_txn_ids":[r["txn_id"] for r in emis],"bounce_count":len(bounces),"bounce_txn_ids":[r["txn_id"] for r in bounces],"total_bounce_charges":str(sum((-Decimal(r["amount"]) for r in charges),Decimal("0")).quantize(Decimal(".01"))),"bounce_charge_txn_ids":[r["txn_id"] for r in charges],"average_end_of_day_balance":str((sum(eod,Decimal("0"))/Decimal(len(eod))).quantize(Decimal(".01"))) if eod else None,"minimum_end_of_day_balance":str(min(eod).quantize(Decimal(".01"))) if eod else None,"foir":str((emi_avg/salary_avg).quantize(Decimal(".0001"))) if salary_avg else None,"foir_reason":None if salary_avg else "no_salary_detected","categorisation_uncertain_debit_ratio":str(coverage.quantize(Decimal(".0001")))}
  # Feature provenance includes transaction IDs for salary/EMI/bounces above.
 dest=Path(output) if output else p/"features.json";dest.write_text(json.dumps(result,indent=2));return result
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("out_dir");ap.add_argument("--out",default=None);a=ap.parse_args();print(json.dumps(run(a.out_dir,a.out),indent=2))
