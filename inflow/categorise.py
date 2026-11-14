import argparse,csv,json,re
from pathlib import Path
TAXONOMY={"SALARY","EMI_LOAN_REPAYMENT","BOUNCE_RETURN","BOUNCE_CHARGE","CASH_WITHDRAWAL","RENT","UTILITIES","UPI_P2P","MERCHANT_SPEND","SELF_TRANSFER","INTEREST","OTHER"}
RULES=[("SALARY",r"SALARY|PAYROLL"),("BOUNCE_CHARGE",r"RETURN CHARGE|BOUNCE CHARGE"),("BOUNCE_RETURN",r"NACH RETURN|BOUNCE RETURN"),("EMI_LOAN_REPAYMENT",r"EMI|LOAN REPAY"),("CASH_WITHDRAWAL",r"ATM|CASH WITHDRAW"),("RENT",r"RENT"),("UTILITIES",r"ELECTRICITY|BILL|WATER"),("UPI_P2P",r"UPI|PHONEPE|GPAY"),("SELF_TRANSFER",r"OWN ACCOUNT|SELF TRANSFER"),("INTEREST",r"INTEREST"),("MERCHANT_SPEND",r"POS|GROCERY|MART")]
def mask_pii(text): return re.sub(r"\d{6,}","[MASKED]",text)
class LLMProvider:
 def classify(self,descriptions): raise NotImplementedError
class FakeLLMProvider(LLMProvider):
 def classify(self,descriptions):
  result=[]
  for d in descriptions:
   u=d.upper(); cat="OTHER"
   # Deliberately broader deterministic simulation than the keyword baseline.
   patterns=[("BOUNCE_CHARGE",r"ACH RTN FEE|NACH RETN CHG|RETURNED ITEM FEE"),("BOUNCE_RETURN",r"NACH RETN|ACH RETURN|EMI RETURNED|LOAN INSTALMENT RETURN"),("EMI_LOAN_REPAYMENT",r"NACH DR HOMEFIN|ACH DEBIT LOAN|LOAN INSTALMENT"),("UPI_P2P",r"IMPS/MBK|IMPS TRANSFER|P2P TRANSFER"),("SELF_TRANSFER",r"NEFT OWN A/C|TRANSFER BETWEEN OWN"),("SALARY",r"PAY CREDIT ACME|MONTHLY REMUNERATION")]
   for c,p in patterns:
    if re.search(p,u):cat=c;break
   if cat=="OTHER":
    for c,p in RULES:
     if re.search(p,u):cat=c;break
   result.append({"category":cat,"confidence":0.82})
  return json.dumps(result)
class RulesCategoriser:
 def classify(self,d):
  for cat,pattern in RULES:
   if re.search(pattern,d.upper()):return cat,0.95
  return "OTHER",0.35
class LLMCategoriser:
 def __init__(self,provider):self.provider=provider;self.calls=0
 def classify(self,descriptions):
  out=[]
  for i in range(0,len(descriptions),25):
   batch=[mask_pii(x) for x in descriptions[i:i+25]]
   parsed=None
   for attempt in range(2):
    self.calls+=1
    try:
     raw=self.provider.classify(batch)
     parsed=json.loads(raw) if isinstance(raw,str) else None
     if not isinstance(parsed,list) or len(parsed)!=len(batch):raise ValueError("Expected one JSON object per description")
     if any(not isinstance(x,dict) or x.get("category") not in TAXONOMY or not isinstance(x.get("confidence"), (int,float)) for x in parsed):raise ValueError("Invalid category or confidence")
     break
    except (ValueError,TypeError,json.JSONDecodeError):parsed=None
   if parsed is None:out.extend([("OTHER",0.0,True)]*len(batch))
   else:out.extend([(x["category"],float(x["confidence"]),False) for x in parsed])
  return out
class HybridCategoriser:
 def __init__(self,provider,threshold=.7):self.rules=RulesCategoriser();self.llm=LLMCategoriser(provider);self.threshold=threshold
 def run(self,rows):
  low=[]; decisions=[]
  for i,r in enumerate(rows):
   c,conf=self.rules.classify(r["description"])
   if conf>=self.threshold:decisions.append((c,conf,"rules",False))
   else:decisions.append(None);low.append(i)
  if low:
   llmres=self.llm.classify([rows[i]["description"] for i in low])
   for i,(c,conf,review) in zip(low,llmres):decisions[i]=(c,conf,"llm",review)
  return decisions

def run(out_dir,provider="fake"):
 p=Path(out_dir); rows=list(csv.DictReader((p/"transactions.csv").open(encoding="utf-8"))); h=HybridCategoriser(FakeLLMProvider()); decisions=h.run(rows)
 fields=list(rows[0])+["category","confidence","categoriser","needs_review"] if rows else []
 with (p/"categorised.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r,d in zip(rows,decisions):r.update(dict(category=d[0],confidence=d[1],categoriser=d[2],needs_review=d[3]));w.writerow(r)
 return rows,decisions,h.llm.calls
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("out_dir");ap.add_argument("--provider",default="fake");a=ap.parse_args();r,d,c=run(a.out_dir,a.provider);print(f"Categorised {len(r)} rows; fake/LLM calls={c}")
