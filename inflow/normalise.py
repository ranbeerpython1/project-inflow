import argparse,csv,json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from .parsers import detect_and_parse
from .models import Transaction

def asdict_tx(t): return t.to_dict() if isinstance(t,Transaction) else {**t,"amount":format(t["amount"],".2f"),"balance":format(t["balance"],".2f")}
def run(data_dir,out_dir):
    data=Path(data_dir); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); allrows=[]; openings={}
    for p in sorted(data.iterdir()):
        if p.suffix.lower() not in {".csv",".xlsx",".txt"}: continue
        txs,opening=detect_and_parse(p)
        for t in txs: allrows.append(asdict_tx(t))
        aid=txs[0].account_id if txs and isinstance(txs[0],Transaction) else (txs[0]["account_id"] if txs else p.stem)
        openings[aid]=opening
    fields=["account_id","txn_id","txn_date","description","amount","balance","source_file","source_line"]
    with (out/"transactions.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(allrows)
    groups=defaultdict(list)
    for r in allrows: groups[r["account_id"]].append(r)
    report={}
    for aid,rows in groups.items():
        rows.sort(key=lambda x:(x["txn_date"],int(x["source_line"])))
        issues=[]; prev=openings.get(aid)
        seen=set()
        for r in rows:
            sig=(r["txn_date"],r["description"],r["amount"],r["balance"])
            if sig in seen: issues.append({"type":"duplicate_row","txn_id":r["txn_id"]})
            seen.add(sig)
            bal=Decimal(r["balance"]); amt=Decimal(r["amount"])
            if prev is not None and abs((prev+amt)-bal)>Decimal("0.01"):
                issues.append({"type":"balance_break","txn_id":r["txn_id"],"expected":format(prev+amt,".2f"),"actual":format(bal,".2f")})
            prev=bal
        report[aid]={"status":"pass" if not issues else "fail","issues":issues}
    (out/"reconciliation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return allrows,report
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("data_dir"); ap.add_argument("--out",default="out"); a=ap.parse_args(); rows,rep=run(a.data_dir,a.out); print(f"Normalised {len(rows)} transactions across {len(rep)} accounts")
