import csv,json,shutil
from pathlib import Path
from inflow.generate import generate
from inflow.normalise import run as normalise
from inflow.categorise import mask_pii,RulesCategoriser,FakeLLMProvider,LLMCategoriser
from inflow.features import run as features

def test_full_pipeline(tmp_path):
 data=tmp_path/"data";out=tmp_path/"out";generate(42,data); rows,rep=normalise(data,out)
 assert len(rep)==6
 assert any(v["status"]=="fail" for v in rep.values())
 assert sum(v["status"]=="pass" for v in rep.values())>=3
 defects=__import__("json").loads((data/"defects.json").read_text())
 for defect in defects:
  assert rep[defect["account_id"]]["status"]=="fail"
 assert all(rep[a]["status"]=="pass" for a in ["ACC003","ACC004","ACC005","ACC006"])
 from inflow.categorise import run as cat
 cat(out); result=features(out)
 assert all("status" in v for v in result.values())

def test_pii_masking():
 assert "123456" not in mask_pii("UPI 1234567890 ref 123456")

def test_rules():
 assert RulesCategoriser().classify("SALARY ACME")[0]=="SALARY"

def test_fake_llm_offline():
 llm=LLMCategoriser(FakeLLMProvider()); assert llm.classify(["SALARY CREDIT"])[0][0]=="SALARY"
