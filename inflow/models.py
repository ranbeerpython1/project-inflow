from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Any, Dict

@dataclass
class Transaction:
    account_id: str
    txn_id: str
    txn_date: str
    description: str
    amount: Decimal
    balance: Decimal
    source_file: str
    source_line: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["amount"] = format(self.amount, ".2f")
        d["balance"] = format(self.balance, ".2f")
        return d


def money(value: Any) -> Decimal:
    s = str(value).strip().replace(",", "")
    if s.endswith("Cr"):
        s = s[:-2].strip()
    elif s.endswith("Dr"):
        s = "-" + s[:-2].strip().lstrip("-")
    return Decimal(s or "0").quantize(Decimal("0.01"))
