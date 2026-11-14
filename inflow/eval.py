import argparse,csv,json
from pathlib import Path
from collections import Counter,defaultdict
from .categorise import RulesCategoriser,FakeLLMProvider,LLMCategoriser,HybridCategoriser

def metrics(y,p):
 labels=sorted(set(y)|set(p)); tp=Counter(); fp=Counter(); fn=Counter()
 for a,b in zip(y,p):
  if a==b:tp[a]+=1
  else:fp[b]+=1;fn[a]+=1
 precision={k:tp[k]/(tp[k]+fp[k]) if tp[k]+fp[k] else 0 for k in labels}; recall={k:tp[k]/(tp[k]+fn[k]) if tp[k]+fn[k] else 0 for k in labels}; f1={k:2*precision[k]*recall[k]/(precision[k]+recall[k]) if precision[k]+recall[k] else 0 for k in labels}
 return {"accuracy":sum(a==b for a,b in zip(y,p))/len(y) if y else 0,"macro_f1":sum(f1.values())/len(labels) if labels else 0,"per_category":{k:{"precision":precision[k],"recall":recall[k]} for k in labels}}
def run(provider="fake",out="out"):
 path=Path("eval/labelled.csv")
 if not path.exists():
  path.parent.mkdir(exist_ok=True); rows=[]
  samples=[("SALARY ACME TECHNOLOGIES","SALARY",False),("NACH EMI HOME LOAN","EMI_LOAN_REPAYMENT",False),("NACH RETURN EMI BOUNCE","BOUNCE_RETURN",False),("NACH RETURN CHARGES","BOUNCE_CHARGE",False),("ATM CASH WITHDRAWAL","CASH_WITHDRAWAL",False),("RENT PAYMENT","RENT",False),("ELECTRICITY BILL BESCOM","UTILITIES",False),("UPI/RAHUL/PHONEPE","UPI_P2P",False),("NEFT OWN ACCOUNT TRANSFER","SELF_TRANSFER",False),("INTEREST CREDIT","INTEREST",False),("GROCERY MART POS","MERCHANT_SPEND",False),("UNKNOWN REF 123456789","OTHER",False),
           ("PAY CREDIT ACME 482910","SALARY",True),("NACH DR HOMEFIN 928311","EMI_LOAN_REPAYMENT",True),("LOAN INSTALMENT RETURN 991827","BOUNCE_RETURN",True),("ACH RTN FEE REF 821990","BOUNCE_CHARGE",True),("IMPS/MBK/RAHUL/771122","UPI_P2P",True),("NEFT OWN A/C 881122","SELF_TRANSFER",True),("MONTHLY REMUNERATION 882211","SALARY",True),("ACH DEBIT LOAN 991100","EMI_LOAN_REPAYMENT",True),("NACH RETN 552211","BOUNCE_RETURN",True),("NACH RETN CHG 661122","BOUNCE_CHARGE",True),("IMPS TRANSFER 772211","UPI_P2P",True),("TRANSFER BETWEEN OWN 993311","SELF_TRANSFER",True)]
  with path.open("w",newline="") as f:
   w=csv.writer(f);w.writerow(["description","label","hard"])
   for i in range(180):d,c,h=samples[i%len(samples)];w.writerow([d if i%2 else d+f" TXN {i}",c,h])
 rows=list(csv.DictReader(path.open())); y=[r["label"] for r in rows]; rule=RulesCategoriser(); rp=[rule.classify(r["description"])[0] for r in rows]; llm=LLMCategoriser(FakeLLMProvider()); lp=[x[0] for x in llm.classify([r["description"] for r in rows])]; hybrid=HybridCategoriser(FakeLLMProvider()); hp=[x[0] for x in hybrid.run([{"description":r["description"]} for r in rows])]
 hard=[i for i,r in enumerate(rows) if r["hard"].lower()=="true"]; report={"provider":"fake","model":"deterministic-rule-backed-fake-v1","llm_calls":llm.calls,"overall":{"rules":metrics(y,rp),"llm":metrics(y,lp),"hybrid":metrics(y,hp)},"hard_subset":{"rules":metrics([y[i] for i in hard],[rp[i] for i in hard]),"llm":metrics([y[i] for i in hard],[lp[i] for i in hard]),"hybrid":metrics([y[i] for i in hard],[hp[i] for i in hard])}}
 Path(out).mkdir(exist_ok=True);(Path(out)/"eval_report.json").write_text(json.dumps(report,indent=2));return report
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--provider",default="fake");ap.add_argument("--out",default="out");a=ap.parse_args();print(json.dumps(run(a.provider,a.out),indent=2))
