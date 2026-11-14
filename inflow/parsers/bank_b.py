from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from openpyxl import load_workbook

def parse_b(path: Path):
    ws=load_workbook(path,data_only=True,read_only=True).active; account=str(ws.cell(1,2).value); out=[]; header=None
    for idx,row in enumerate(ws.iter_rows(values_only=True),1):
        vals=list(row)
        if vals and vals[0]=="Date": header=idx; continue
        if not header or not vals or vals[0] is None: continue
        dt=vals[0]; dt=dt.date() if isinstance(dt,datetime) else dt
        if isinstance(dt,date): iso=dt.isoformat()
        else: iso=datetime.strptime(str(dt),"%d/%m/%Y").date().isoformat()
        amt=Decimal(str(vals[2])).quantize(Decimal(".01")); baltext=str(vals[3]).strip()
        bal_raw=Decimal(baltext[:-2].strip().replace(",",""))
        # If number is already negative, the sign is authoritative; negate only positive values tagged Dr.
        bal=-bal_raw if (baltext.endswith("Dr") and bal_raw>=0) else bal_raw
        out.append({"account_id":account,"txn_id":f"{path.name}:{idx}","txn_date":iso,"description":str(vals[1]).strip(),"amount":amt,"balance":bal,"source_file":path.name,"source_line":idx})
    return out,None
