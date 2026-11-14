from pathlib import Path
from .bank_a import parse_a
from .bank_b import parse_b
from .bank_c import parse_c

def detect_and_parse(path: Path):
    raw=path.read_bytes()
    if raw.startswith(b"PK\x03\x04"):
        return parse_b(path)
    text=raw.decode("utf-8",errors="replace")
    if "Opening Balance:" in text and "Withdrawal" in text:
        return parse_a(path)
    if "OPENING BALANCE" in text and "END OF PAGE" in text or "OPENING BALANCE" in text:
        return parse_c(path)
    raise ValueError(f"Unrecognised statement content: {path}")
