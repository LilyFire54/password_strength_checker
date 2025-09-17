"""
Password Strength Checker

Quick, portfolio-friendly Python script that scores passwords 0–100,
labels them (Weak/Fair/Good/Strong), and gives concrete tips to improve.

Usage:
  1) Check a single password via arg:
       python password_strength_checker.py "MyS3cret!"
  2) Interactive (input hidden):
       python password_strength_checker.py

Optional flags:
  --show   Use visible input instead of hidden getpass
  --json   Output machine-readable JSON

This file is self-contained. No third-party packages required.
"""
from __future__ import annotations
import re
import sys
import json
import math
from typing import Dict, List, Tuple

COMMON_PASSWORDS = {
    # Short, illustrative set. In README, note this can be expanded.
    "password", "123456", "123456789", "qwerty", "abc123", "letmein",
    "welcome", "admin", "iloveyou", "monkey", "dragon", "sunshine",
}

DICTIONARY_WORDS = {
    # Minimal list for demo. Replace/expand from wordlists in production.
    "password", "welcome", "dragon", "princess", "football", "flower",
    "shadow", "hunter", "purple", "fire", "lily", "kaizen", "summer",
}

KEYBOARD_SEQUENCES = [
    "qwerty", "asdfgh", "zxcvbn", "qwertz", "azerty"
]

SEQUENTIAL_ASC = "abcdefghijklmnopqrstuvwxyz"
SEQUENTIAL_DESC = SEQUENTIAL_ASC[::-1]
DIGITS = "0123456789"

SYMBOLS_RE = re.compile(r"[^A-Za-z0-9]")
LOWER_RE = re.compile(r"[a-z]")
UPPER_RE = re.compile(r"[A-Z]")
DIGIT_RE = re.compile(r"[0-9]")
REPEAT_RE = re.compile(r"(.)\1{2,}")  # runs of >=3 of the same char
DATE_RE = re.compile(r"(?:(?:19|20)\d{2}|\d{2}[/-]\d{2}[/-](?:19|20)\d{2})")

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

def has_sequence(s: str, min_len: int = 4) -> bool:
    s_low = s.lower()
    # Check alphabetical ascending/descending
    for i in range(len(SEQUENTIAL_ASC) - min_len + 1):
        seq = SEQUENTIAL_ASC[i:i+min_len]
        if seq in s_low:
            return True
    for i in range(len(SEQUENTIAL_DESC) - min_len + 1):
        seq = SEQUENTIAL_DESC[i:i+min_len]
        if seq in s_low:
            return True
    # Check digit sequences
    for i in range(len(DIGITS) - min_len + 1):
        seq = DIGITS[i:i+min_len]
        if seq in s_low:
            return True
    return False

def has_keyboard_sequence(s: str) -> bool:
    s_low = s.lower()
    return any(k in s_low for k in KEYBOARD_SEQUENCES)


def looks_like_date(s: str) -> bool:
    return bool(DATE_RE.search(s))


def contains_dictionary_word(s: str) -> bool:
    s_low = s.lower()
    # Check direct words and leet-like simple variants
    variants: List[str] = [s_low]
    # Basic leetspeak reversal
    table = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "7": "t", "@": "a", "$": "s"})
    variants.append(s_low.translate(table))

    for word in DICTIONARY_WORDS:
        for v in variants:
            if word in v and len(word) >= 4:
                return True
    return False


def evaluate_password(pw: str) -> Dict:
    length = len(pw)
    classes = char_classes(pw)
    entropy = shannon_entropy(pw)

    # Base scores
    length_score = max(0, min(40, (length - 4) * 4))  # len 14 -> 40
    variety_score = 10 * sum(classes.values())  # 0..40, but cap at 30 below
    variety_score = min(30, variety_score)
    entropy_bonus = min(15, int(entropy * 2))  # rough, encourages mixed chars
    long_bonus = 5 if length >= 16 else 0

    score = length_score + variety_score + entropy_bonus + long_bonus

    # Penalties
    penalties = []
    if pw.lower() in COMMON_PASSWORDS:
        score -= 50
        penalties.append("Common password detected")
    if has_sequence(pw):
        score -= 15
        penalties.append("Sequential pattern present")
    if has_keyboard_sequence(pw):
        score -= 10
        penalties.append("Keyboard sequence present")
    if REPEAT_RE.search(pw):
        score -= 10
        penalties.append("Repeated characters run")
    if contains_dictionary_word(pw):
        score -= 10
        penalties.append("Dictionary word detected")
    if looks_like_date(pw):
        score -= 5
        penalties.append("Looks like a date")

    score = max(0, min(100, score))

    # Label
    if score < 25:
        label = "Weak"
    elif score < 50:
        label = "Fair"
    elif score < 75:
        label = "Good"
    else:
        label = "Strong"

    # Suggestions
    tips: List[str] = []
    if length < 12:
        tips.append("Use at least 12 characters; 16+ is better")
    if not classes["lower"]:
        tips.append("Add lowercase letters")
    if not classes["upper"]:
        tips.append("Add uppercase letters")
    if not classes["digit"]:
        tips.append("Include a digit")
    if not classes["symbol"]:
        tips.append("Include a symbol like !?%#")
    if has_sequence(pw):
        tips.append("Avoid sequences like abcd or 1234")
    if has_keyboard_sequence(pw):
        tips.append("Avoid keyboard patterns like qwerty")
    if REPEAT_RE.search(pw):
        tips.append("Avoid repeating the same character 3+ times")
    if contains_dictionary_word(pw):
        tips.append("Avoid common words or names, or break them up")
    if looks_like_date(pw):
        tips.append("Do not use dates or birthdays")
    if len(tips) == 0 and label != "Strong":
        tips.append("Add length and mix character types for a higher score")

    return {
        "password_length": length,
        "score": score,
        "label": label,
        "entropy_bits": round(entropy, 2),
        "penalties": penalties,
        "suggestions": tips,
    }

def _format_human(result: Dict) -> str:
    bullets = "\n  - ".join(result["suggestions"]) or "\n  - None"
    pens = "\n  - ".join(result["penalties"]) or "\n  - None"
    return (
        f"Strength: {result['label']} ({result['score']}/100)\n"
        f"Length: {result['password_length']}\n"
        f"Entropy (Shannon): {result['entropy_bits']} bits\n"
        f"Penalties:{pens}\n"
        f"Suggestions:{bullets}\n"
    )

def _parse_args(argv: List[str]) -> Tuple[bool, bool, str | None]:
    show = "--show" in argv
    json_flag = "--json" in argv
    pw_arg = None
    rest = [a for a in argv if a not in {"--show", "--json"}]
    if len(rest) >= 2:
        pw_arg = rest[1]
    return show, json_flag, pw_arg

def main() -> int:
    show, as_json, pw_arg = _parse_args(sys.argv)

    if pw_arg is None:
        try:
            if show:
                pw = input("Enter password (visible): ")
            else:
                import getpass
                pw = getpass.getpass("Enter password: ")
        except KeyboardInterrupt:
            print("\nCanceled.")
            return 1
    else:
        pw = pw_arg

    result = evaluate_password(pw)

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(_format_human(result))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
