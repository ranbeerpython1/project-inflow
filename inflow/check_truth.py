import argparse,csv
from collections import Counter
from pathlib import Path
KEYS=["txn_date","amount","balance","description"]
def load(p):
 with open(p,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def run(data,out):
 truth=load(Path(data)/"truth"/"transactions.csv"); actual=load(Path(out)/"transactions.csv")
 a=Counter(tuple(r[k] for k in KEYS) for r in actual); b=Counter(tuple(r[k] for k in KEYS) for r in truth); matched=sum((a & b).values()); total=sum(b.values()); pct=100*matched/total if total else 100
 print(f"Truth match: {matched}/{total} ({pct:.2f}%)"); return pct
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("data");ap.add_argument("out");a=ap.parse_args();run(a.data,a.out)
