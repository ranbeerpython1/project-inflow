import json
from inflow.categorise import LLMCategoriser

class SequenceProvider:
    def __init__(self, answers): self.answers=list(answers); self.received=[]
    def classify(self, descriptions):
        self.received.extend(descriptions)
        return self.answers.pop(0)

def test_malformed_json_then_valid_retries_once():
    p=SequenceProvider(["not-json",json.dumps([{"category":"SALARY","confidence":.9}])])
    result=LLMCategoriser(p).classify(["SALARY 123456789"])
    assert result[0][0]=="SALARY"
    assert len(p.received)==2

def test_out_of_taxonomy_then_retry_then_other_review():
    p=SequenceProvider([json.dumps([{"category":"CREDIT","confidence":.9}]),json.dumps([{"category":"NOPE","confidence":.8}])])
    result=LLMCategoriser(p).classify(["unknown narration"])
    assert result==[("OTHER",0.0,True)]

def test_provider_never_receives_unmasked_six_digit_runs():
    p=SequenceProvider([json.dumps([{"category":"OTHER","confidence":.4}])])
    LLMCategoriser(p).classify(["UPI 9876543210 ref 123456"])
    assert all(not any(len(token)>5 and token.isdigit() for token in text.split()) for text in p.received)
