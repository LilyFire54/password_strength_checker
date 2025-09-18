"""
Password Strength Checker with Color Output


Adds ANSI colors to the strength labels:
- Weak = Red
- Fair = Yellow
- Good = Cyan
- Strong = Green
"""
from __future__ import annotations
import re
import sys
import json
import math
from typing import Dict, List, Tuple

# ANSI colors
RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GREEN = "\033[92m"

COMMON_PASSWORDS = {"password", "123456", "123456789", "qwerty", "abc123", "letmein"}
DICTIONARY_WORDS = {"password", "welcome", "dragon", "princess", "football"}

SYMBOLS_RE = re.compile(r"[^A-Za-z0-9]")
LOWER_RE = re.compile(r"[a-z]")
UPPER_RE = re.compile(r"[A-Z]")
DIGIT_RE = re.compile(r"[0-9]")

def shannon_entropy(s: str) -> float:
if not s:
return 0.0
from collections import Counter
counts = Counter(s)
length = len(s)
return -sum((c/length) * math.log2(c/length) for c in counts.values())

def char_classes(s: str) -> Dict[str, bool]:
return {
"lower": bool(LOWER_RE.search(s)),
"upper": bool(UPPER_RE.search(s)),
"digit": bool(DIGIT_RE.search(s)),
"symbol": bool(SYMBOLS_RE.search(s)),
}

def evaluate_password(pw: str) -> Dict:
length = len(pw)
classes = char_classes(pw)
entropy = shannon_entropy(pw)

score = (length * 2) + (10 * sum(classes.values())) + int(entropy * 2)
penalties = []

if pw.lower() in COMMON_PASSWORDS:
score -= 40
penalties.append("Common password detected")
if any(word in pw.lower() for word in DICTIONARY_WORDS):
score -= 10
penalties.append("Dictionary word detected")

score = max(0, min(100, score))

if score < 25:
label, color = "Weak", RED
elif score < 50:
label, color = "Fair", YELLOW
elif score < 75:
label, color = "Good", CYAN
else:
label, color = "Strong", GREEN

return {
"password_length": length,
"score": score,
"label": f"{color}{label}{RESET}",
"penalties": penalties,
}

def _format_human(result: Dict) -> str:
pens = "\n - ".join(result["penalties"]) or "\n - None"
return (
f"Strength: {result['label']} ({result['score']}/100)\n"
f"Length: {result['password_length']}\n"
f"Penalties:{pens}\n"
)

def main() -> int:
if len(sys.argv) > 1:
pw = sys.argv[1]
else:
import getpass
pw = getpass.getpass("Enter password: ")

result = evaluate_password(pw)
print(_format_human(result))
return 0

if __name__ == "__main__":
raise SystemExit(main())
