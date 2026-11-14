import argparse, csv, json, random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from openpyxl import Workbook
from .models import Transaction

HEADERS = ["account_id","txn_id","txn_date","description","amount","balance","source_file","source_line"]
NARRATIONS = [
    ("SALARY ACME TECHNOLOGIES", "credit", "SALARY"),
    ("NACH EMI HOME LOAN", "debit", "EMI_LOAN_REPAYMENT"),
    ("UPI/RAHUL/PHONEPE", "debit", "UPI_P2P"),
    ("ELECTRICITY BILL BESCOM", "debit", "UTILITIES"),
    ("ATM CASH WITHDRAWAL", "debit", "CASH_WITHDRAWAL"),
    ("RENT PAYMENT", "debit", "RENT"),
    ("NEFT OWN ACCOUNT TRANSFER", "debit", "SELF_TRANSFER"),
    ("INTEREST CREDIT", "credit", "INTEREST"),
    ("NACH RETURN EMI BOUNCE", "credit", "BOUNCE_RETURN"),
    ("NACH RETURN CHARGES", "debit", "BOUNCE_CHARGE"),
    ("GROCERY MART POS", "debit", "MERCHANT_SPEND"),
]

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=HEADERS); w.writeheader(); w.writerows(rows)

def generate(seed=42, out="data"):
    rng=random.Random(seed); root=Path(out); root.mkdir(parents=True,exist_ok=True)
    truth=[]; defects=[]; clean_count=0
    for idx in range(6):
        bank=idx//2; account=f"ACC{idx+1:03d}"; opening=Decimal("50000.00")
        fmt="ABC"[bank]; filename=f"bank_{fmt.lower()}_{idx+1}."+(["csv","xlsx","txt"][bank])
        rows=[]; bal=opening; start=date(2026,1,1)
        for month in range(6):
            for day, item in [(2,NARRATIONS[0]),(5,NARRATIONS[1]),(9,NARRATIONS[2]),(12,NARRATIONS[3]),(15,NARRATIONS[4]),(20,NARRATIONS[5]),(24,NARRATIONS[6]),(26,NARRATIONS[7]),(27,NARRATIONS[8]),(28,NARRATIONS[9]),(29,NARRATIONS[10])]:
                dt=date(2026,1,1)+timedelta(days=month*30+day-1)
                desc,kind,cat=item
                amt=Decimal(str(rng.choice([1800,2200,3500,42000,900,1500,700,125]))).quantize(Decimal(".01"))
                if kind=="debit": amt=-amt
                bal=(bal+amt).quantize(Decimal(".01"))
                row={"account_id":account,"txn_id":f"{filename}:{len(rows)+1}","txn_date":dt.isoformat(),"description":desc,"amount":format(amt,".2f"),"balance":format(bal,".2f"),"source_file":filename,"source_line":len(rows)+1}
                rows.append(row)
        # Add injected defects on two different accounts: one dropped middle transaction, one exact duplicate.
        if idx==0:
            dropped=rows.pop(15); defects.append({"account_id":account,"type":"dropped_row","txn_id":dropped["txn_id"]})
            # Subsequent balances now break; preserve source line identifiers.
        elif idx==1:
            dup=dict(rows[15]); dup["txn_id"]=f"{filename}:DUP{dup['source_line']}"; rows.insert(16,dup)
            defects.append({"account_id":account,"type":"duplicate_row","txn_id":dup["txn_id"]})
        else: clean_count+=1
        # render source formats; truth represents rows actually present in exports
        if bank==0:
            p=root/filename
            with p.open("w",newline="",encoding="utf-8") as f:
                f.write(f"Account: {account}\nOpening Balance: {opening:.2f}\n")
                w=csv.writer(f); w.writerow(["Date","Narration","Withdrawal","Deposit","Balance"])
                for r in rows:
                    a=Decimal(r["amount"]); w.writerow([date.fromisoformat(r["txn_date"]).strftime("%d/%m/%y"),r["description"],format(-a,".2f") if a<0 else "",format(a,".2f") if a>0 else "",r["balance"]])
        elif bank==1:
            wb=Workbook(); ws=wb.active; ws.append(["Account",account]); ws.append(["Date","Narration","Amount","Balance"]); ws.append([None,None,None,None])
            for r in rows:
                a=Decimal(r["amount"]); ws.append([date.fromisoformat(r["txn_date"]),r["description"],format(a,".2f"),r["balance"]+ (" Cr" if Decimal(r["balance"])>=0 else " Dr")])
            wb.save(root/filename)
        else:
            with (root/filename).open("w",encoding="utf-8") as f:
                f.write(f"ACCOUNT {account}  OPENING BALANCE {opening:,.2f}\n")
                for n,r in enumerate(rows):
                    if n%20==0: f.write("DATE       DESCRIPTION                              DEBIT       CREDIT      BALANCE\n")
                    a=Decimal(r["amount"]); deb=f"{-a:,.2f}" if a<0 else ""; cred=f"{a:,.2f}" if a>0 else ""
                    desc=r["description"]
                    if len(desc)>26: f.write(f"{date.fromisoformat(r['txn_date']).strftime('%d/%m/%y')}  {desc[:26]:26} {deb:>10} {cred:>10} {Decimal(r['balance']):>12,.2f}\n    {desc[26:]}\n")
                    else: f.write(f"{date.fromisoformat(r['txn_date']).strftime('%d/%m/%y')}  {desc:26} {deb:>10} {cred:>10} {Decimal(r['balance']):>12,.2f}\n")
                    if n%20==19: f.write("PAGE TOTAL                                  END OF PAGE\n")
        truth.extend(rows)
    write_csv(root/"truth"/"transactions.csv",truth)
    (root/"defects.json").write_text(json.dumps(defects,indent=2),encoding="utf-8")
    return truth,defects

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--seed",type=int,default=42); ap.add_argument("--out",default="data"); a=ap.parse_args(); generate(a.seed,a.out); print(f"Generated synthetic statements in {a.out}")
