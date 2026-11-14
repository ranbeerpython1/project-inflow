import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

def parse_c(path: Path):
    text=path.read_text(encoding="utf-8"); m=re.search(r"ACCOUNT\s+(\S+)\s+OPENING BALANCE\s+([\d,]+\.\d{2})",text); account=m.group(1); opening=Decimal(m.group(2).replace(",","")); out=[]
    date_re=re.compile(r"^\d{2}/\d{2}/\d{2}\s{2}")
    # Detect column positions from the header line so the parser is layout-agnostic.
    header_m=re.search(r"^DATE\s+DESCRIPTION\s+(DEBIT)\s+(CREDIT)\s+BALANCE", text, re.MULTILINE)
    if header_m:
        # Offset from start of header line (which begins at 'DATE', col 0)
        debit_col=header_m.start(1)-header_m.start()
        credit_col=header_m.start(2)-header_m.start()
        # Adjust for line[9:] slicing: subtract the 9 date-prefix chars
        midpoint=(debit_col+credit_col)//2 - 9
    else:
        midpoint=33  # fallback: original fixture layout
    # Match signed or unsigned decimal numbers (commas allowed as thousand-separators).
    num_re=re.compile(r"-?[\d,]+\.\d{2}")
    for i,line in enumerate(text.splitlines(),1):
        if not date_re.match(line):
            if line.startswith("    ") and out: out[-1]["description"]=(out[-1]["description"]+" "+line.strip()).strip()
            continue
        dt=line[:8]
        # Collect all numbers found after the date prefix (col 9 onward).
        nums=[m2.group() for m2 in num_re.finditer(line[9:])]
        if not nums: continue  # PAGE TOTAL / header lines produce zero matches
        bal_s=nums[-1]; amount=Decimal("0")
        if len(nums)>=3:
            # Three numbers: debit, credit, balance.  Only one of debit/credit is non-zero.
            deb_s,cred_s=nums[0],nums[1]
            if deb_s: amount-=Decimal(deb_s.replace(",",""))
            if cred_s: amount+=Decimal(cred_s.replace(",",""))
        elif len(nums)==2:
            # Two numbers: balance plus one of debit/credit.
            # Use header-derived column positions to tell them apart.
            first_match=num_re.search(line[9:])
            midpoint=(debit_col+credit_col)//2
            if first_match and first_match.start() < midpoint:
                amount-=Decimal(nums[0].replace(",",""))   # debit
            else:
                amount+=Decimal(nums[0].replace(",",""))   # credit
        # Description: text between col 10 and the first gap of 2+ spaces before numerics.
        rest=line[10:]
        desc_match=re.match(r"(.+?)\s{2,}-?[\d,]", rest)
        desc=desc_match.group(1).strip() if desc_match else rest.strip()
        out.append({"account_id":account,"txn_id":f"{path.name}:{i}","txn_date":datetime.strptime(dt,"%d/%m/%y").date().isoformat(),"description":desc,"amount":amount,"balance":Decimal(bal_s.replace(",","")),"source_file":path.name,"source_line":i})
    return out,opening
