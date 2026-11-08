"""Step 1: clean the text and tag the language.

Scammers hide words from filters with tricks like:
  - look-alike letters from other alphabets ("Оrion" with a Cyrillic O)
  - hidden zero-width characters inside words
  - spaced-out letters ("C a l l  n o w")
  - leetspeak ("0rion B@nk", "acc0unt")
We undo these so the model and the rules see the real words.
"""
import re
import unicodedata

SINHALA = re.compile(r"[඀-෿]")
LATIN = re.compile(r"[A-Za-z]")

# Look-alike characters (Cyrillic and Greek) -> Latin.
HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d", "ɡ": "g", "ո": "n", "ս": "u",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O",
    "Р": "P", "С": "C", "Т": "T", "Х": "X", "І": "I",
    "Α": "A", "Β": "B", "Ε": "E", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M",
    "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Χ": "X", "ο": "o", "α": "a",
})

# Zero-width space, word joiner and BOM are always junk in an SMS.
ALWAYS_HIDDEN = re.compile("[​⁠﻿]")
# ZWJ / ZWNJ are REAL parts of Sinhala writing (e.g. yansaya, rakaransaya),
# so we only remove them when they are NOT next to a Sinhala letter.
JOINERS_OUTSIDE_SINHALA = re.compile(
    "(?<![඀-෿])[‌‍]|[‌‍](?![඀-෿])"
)

LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s",
                      "7": "t", "@": "a", "$": "s"})

# Romanised Sinhala words that show a message is Singlish.
SINGLISH_MARKERS = {
    "obage", "oyage", "oya", "oyata", "obata", "eka", "ekak", "ekata", "karanna",
    "karanne", "karala", "wenawa", "venawa", "wenna", "una", "nam", "ona", "oni",
    "kiyala", "thiyenawa", "tiyenawa", "mage", "mata", "api", "apita", "nadda",
    "nedda", "wahama", "ikmanin", "passe", "athule", "ate", "labuna", "labenawa",
    "ganna", "denna", "yawanna", "ewanna", "evanna", "hadanna", "meka", "mekata",
    "salli", "rupiyal", "ube", "issella", "dan", "ada", "heta", "kiyanna", "epa",
    "pahala", "uda", "block", "wela", "gana", "k", "shesaya", "hata", "ta",
}
SINGLISH_STRONG = SINGLISH_MARKERS - {"block", "k", "ta", "dan", "api", "ate", "una", "nam"}


def _remove_hidden(text):
    found = bool(ALWAYS_HIDDEN.search(text) or JOINERS_OUTSIDE_SINHALA.search(text))
    text = ALWAYS_HIDDEN.sub("", text)
    text = JOINERS_OUTSIDE_SINHALA.sub("", text)
    return text, found


def _fix_homoglyphs(text):
    fixed = text.translate(HOMOGLYPHS)
    return fixed, fixed != text


def _join_spaced_letters(text):
    """'C a l l  0 7 7' -> 'Call 077'. Needs 3+ single characters in a row."""
    pattern = re.compile(r"(?<!\S)(?:\S ){2,}\S(?!\S)")
    found = bool(pattern.search(text))
    text = pattern.sub(lambda m: m.group(0).replace(" ", ""), text)
    return re.sub(r"[ \t]{2,}", " ", text), found


def _looks_like_number_or_code(token):
    """Phone numbers, OTPs, masked accounts (xxxx4471) and '24hrs' / '5pm' style tokens."""
    if re.fullmatch(r"\W*\d+(?:hrs?|h|mins?|am|pm|st|nd|rd|th|k|gb|mb|kg|km|x)\W*", token, re.I):
        return True
    letters = [c for c in token if c.isalpha() and c.lower() != "x"]
    return len(letters) < 2


def _fix_leet(text):
    """'0rion B@nk' -> 'orion Bank'. Leaves phone numbers, amounts and OTPs alone."""
    found = False
    out = []
    for token in re.split(r"(\s+)", text):
        has_trick = re.search(r"[013457@$]", token) and LATIN.search(token)
        is_link = re.search(r"(https?|hxxps?|www\.|\[\.\]|\.[a-z]{2,}/?)", token, re.I)
        if has_trick and not is_link and not _looks_like_number_or_code(token):
            core = re.sub(r"[^\w@$]", "", token)
            digits = sum(c.isdigit() for c in core)
            if core and digits / len(core) < 0.5:
                token = token.translate(LEET)
                found = True
        out.append(token)
    return "".join(out), found


def detect_language(text):
    """Return 'si', 'singlish', 'mixed' or 'en'."""
    sinhala = len(SINHALA.findall(text))
    latin = len(LATIN.findall(text))
    words = re.findall(r"[a-z]+", text.lower())
    strong = sum(w in SINGLISH_STRONG for w in words)
    weak = sum(w in SINGLISH_MARKERS for w in words)

    if sinhala and sinhala >= latin:
        # Mostly Sinhala script. Many English words too -> mixed.
        return "mixed" if latin > 0.6 * sinhala and len(words) >= 4 else "si"
    if sinhala:
        return "mixed"
    if strong >= 2 or (strong >= 1 and weak >= 2):
        return "singlish"
    return "en"


def clean(text):
    """Return (normalized_text, language, tricks_found)."""
    text = unicodedata.normalize("NFC", text)
    tricks = []
    text, f = _remove_hidden(text)
    if f:
        tricks.append("zero_width")
    text, f = _fix_homoglyphs(text)
    if f:
        tricks.append("homoglyph")
    text, f = _join_spaced_letters(text)
    if f:
        tricks.append("spaced_letters")
    text, f = _fix_leet(text)
    if f:
        tricks.append("leetspeak")
    text = text.strip()
    return text, detect_language(text), tricks
