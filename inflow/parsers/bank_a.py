import csv, re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from ..models import Transaction

def parse_a(path: Path):
    lines=path.read_text(encoding="utf-8").splitlines(); account=re.search(r"Account:\s*(\S+)",lines[0]).group(1); opening=Decimal(re.search(r"Opening Balance:\s*([\d.]+)",lines[1]).group(1))
    reader=csv.DictReader(lines[2:]); out=[]
    for i,r in enumerate(reader,4):
        amt=Decimal("0")
        if r.get("Withdrawal"): amt-=Decimal(r["Withdrawal"].replace(",",""))
        if r.get("Deposit"): amt+=Decimal(r["Deposit"].replace(",",""))
        out.append(Transaction(account,f"{path.name}:{i}",datetime.strptime(r["Date"],"%d/%m/%y").date().isoformat(),r["Narration"].strip(),amt,Decimal(r["Balance"].replace(",","")),path.name,i))
    return out,opening
