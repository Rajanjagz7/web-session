"""Generate per-field AU CSVs (>=100 rows each). Deterministic: no randomness, no clock."""
import csv, datetime, os, re

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv")
os.makedirs(OUT, exist_ok=True)
HDR = ["field_name", "value_as_user_typed", "value_normalised", "expected_validator_result", "reason"]
OBS = "OBSERVED"
ASM = "ASSUMPTION-needs-UI-inspection"
MIN_ROWS = 100
COUNTS = {}


def write(field, rows):
    seen, uniq = set(), []
    for r in rows:  # de-duplicate on typed value so every row is a distinct test value
        if r[0] not in seen:
            seen.add(r[0])
            uniq.append(r)
    assert len(uniq) >= MIN_ROWS, f"{field}: only {len(uniq)} rows"
    with open(os.path.join(OUT, f"{field}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(HDR)
        for typed, norm, exp, why in uniq:
            w.writerow([field, typed, norm, exp, why])
    COUNTS[field] = len(uniq)


def lcg(seed):
    x = seed
    while True:
        x = (x * 1103515245 + 12345) % 2147483648
        yield x


FIRST = ["Olivia", "Noah", "Mia", "Jack", "Aria", "Liam", "Charlotte", "William", "Zoe", "Ethan"]
LAST = ["Nguyen", "Smith", "Collins", "Wilson", "Patel", "Brown", "Anderson", "Lee", "Khan", "White"]
INJECT = ["<script>alert(1)</script>", "\"><img src=x onerror=alert(1)>", "'; DROP TABLE users;--", "' OR '1'='1", "1; SELECT pg_sleep(5)--",
          "{{7*7}}", "${7*7}", "../../etc/passwd", "%00", "<svg/onload=alert(1)>"]

# ---------- mobile_number (observed: +61 prefix, mask "+61 (04) XXXX XXXX", placeholder "04xx xxx xxx")
def mob_norm(s):
    d = re.sub(r"\D", "", s)
    if d.startswith("61"):
        d = d[2:]
    if d.startswith("0"):
        d = d[1:]
    return "+61" + d


def mob_valid(s):
    return bool(re.fullmatch(r"\+614\d{8}", mob_norm(s))) and not re.search(r"[A-Za-z]", s)


mobile = []
for v, why in [("+61 412 345 678", "AU library valid, E.164"), ("+61 423 456 789", "AU library valid"), ("+61 434 567 890", "AU library valid"),
               ("+61 458 901 234", "AU library valid"), ("+61 401 234 567", "AU library valid"), ("0412 345 678", "national format"),
               ("0423 456 789", "national format"), ("0444124222", "owned QA number; UI mask -> +61 (04) 4412 4222 (" + OBS + ")"),
               ("  0444124222 ", "leading/trailing whitespace trimmed")]:
    mobile.append((v, mob_norm(v), "ACCEPT" if mob_valid(v) else "REJECT", why))
for v, why in [("+61 12 345 6789", "library negative: 10 digits but no mobile prefix 4 (register C-01)"), ("+1 412 345 6789", "US country code in AU field"),
               ("+61 4", "prefix only"), ("0412ABC678", "letters mixed in"), (" ", "single whitespace"), ("   ", "whitespace only"),
               ("\U0001F642", "emoji"), ("", "empty")]:
    mobile.append((v, mob_norm(v) if v.strip() else "", "ACCEPT" if mob_valid(v) else "REJECT", why))
for n in (9, 10, 11, 12, 15):
    v = ("04" + "12345678901234")[:n]
    mobile.append((v, mob_norm(v), "ACCEPT" if n == 10 else "REJECT", f"boundary: {n} digits national"))
g = lcg(61)
fmts = ["0{a}{b} {c}{d} {e}{f}", "+61 4{a}{b} {c}{d}{e} {f}", "04{a}{b}-{c}{d}{e}-{f}", "614{a}{b}{c}{d}{e}{f}", "(04) {a}{b}{c}{d} {e}{f}"]
for i in range(55):  # positive: varied formats, second digit 0-9 (4x)
    r = next(g)
    ds = [str((r >> (3 * k)) % 10) for k in range(7)]
    core = "4" + str(i % 10) + "".join(ds[:6])
    style = i % 5
    v = ["0" + core[:3] + " " + core[3:6] + " " + core[6:], "+61 " + core[:3] + " " + core[3:6] + " " + core[6:], "0" + core, "+61" + core,
         "(0" + core[:1] + ") " + core[1:5] + " " + core[5:]][style]
    mobile.append((v, mob_norm(v), "ACCEPT", f"positive #{i + 1}: style {style}, generated 04xx"))
for i, p in enumerate(["02", "03", "05", "07", "08", "01", "00", "09", "06", "13", "18", "19"]):
    v = f"{p}12 345 678"
    mobile.append((v, mob_norm(v), "REJECT", f"landline/other prefix {p} (not 04)"))
for n in range(1, 9):
    v = "0412345678"[:n]
    mobile.append((v, mob_norm(v), "REJECT", f"too short: {n} digits"))
for i, s in enumerate(["0412 345 67x", "04l2 345 678", "0412.345.678", "0412/345/678", "+61+412345678", "++61412345678", "0412 345 678 90", "04１2 345 678",
                       "0412\t345678", "0412 345 678\n", "+61 (0)412 345 678", "0412 345 6.8"]):
    mobile.append((s, mob_norm(s), "ACCEPT_IF_NORMALISED" if mob_valid(s) else "REJECT", f"malformed/odd separators #{i + 1}"))
write("mobile_number", mobile)

# ---------- email_address
def email_valid(s):
    e = s
    if len(e) > 254 or e.count("@") != 1 or e != e.strip() or not e.isascii():
        return False
    local, dom = e.split("@")
    if not local or len(local) > 64 or ".." in e or local.startswith(".") or local.endswith("."):
        return False
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+", local):
        return False
    labels = dom.split(".")
    return len(labels) >= 2 and all(re.fullmatch(r"[A-Za-z0-9-]{1,63}", l) and not l.startswith("-") and not l.endswith("-") for l in labels) and len(labels[-1]) >= 2


def long_email(total):
    local, suffix = "a" * 64, "bigpond.net.au"
    L, prefix = total - 65 - len(suffix), ""
    while L > 0:
        seg = min(64, L)
        if L - seg == 1:
            seg -= 1
        prefix += "a" * (seg - 1) + "."
        L -= seg
    return local + "@" + prefix + suffix


DOMS = ["example.com.au", "bigpond.net.au", "aussie.com.au", "gmail.com"]
emails = []
for v, why in [("olivia.nguyen@example.com.au", "AU library"), ("noah.smith@bigpond.net.au", "AU library"), ("mia.collins@aussie.com.au", "AU library"),
               ("jack.wilson+invoices@gmail.com", "plus-addressing"), ("a@b.com.au", "boundary: local 1 char"), ("a" * 64 + "@bigpond.net.au", "boundary: local 64 (max)")]:
    emails.append((v, v.lower(), "ACCEPT", why))
for i in range(60):
    f, l, d = FIRST[i % 10], LAST[(i * 3 + i // 10) % 10], DOMS[i % 4]
    v = [f"{f}.{l}@{d}", f"{f}_{l}@{d}", f"{f}{l}{i}@{d}", f"{f}-{l}@{d}", f"{f}.{l}+qa{i}@{d}", f"{f[0]}{l}@{d}"][i % 6].lower()
    v = v if i % 7 else v.upper()  # every 7th uppercase: normalises to lowercase
    emails.append((v, v.lower(), "ACCEPT", f"positive #{i + 1}: AU name x AU domain"))
NEG = [("noah.smithbigpond.net.au", "no @"), ("noah.smith@bigpond", "missing TLD"), ("noah.smith@bigpond.c", ".c minimal TLD"), ("noah..smith@bigpond.net.au", "double dot"),
       ("@bigpond.net.au", "empty local"), ("noah.smith@", "empty domain"), ("noah@@bigpond.net.au", "double @"), ("noah smith@bigpond.net.au", "space in local"),
       (".noah@bigpond.net.au", "leading dot"), ("noah.@bigpond.net.au", "trailing dot"), ("noah@-bigpond.net.au", "label starts with hyphen"),
       ("noah@bigpond..net.au", "double dot in domain"), ("noah@bigpond.net.au.", "trailing dot domain"), ("noah@big pond.net.au", "space in domain"),
       ("noah,smith@bigpond.net.au", "comma"), ("noah(smith)@bigpond.net.au", "parentheses"), ("olivia.nguyen@еxample.com.au", "IDN homoglyph (Cyrillic e)"),
       ("a" * 65 + "@bigpond.net.au", "local 65 (max+1)"), (" ", "whitespace only"), ("", "empty"), ("\U0001F642@bigpond.net.au", "emoji local"),
       ("olivia.nguyen@example.com.au​", "hidden zero-width space")]
for v, why in NEG:
    emails.append((v, v.strip().lower(), "REJECT", why))
emails += [("noah.smith@bigpond.con", "noah.smith@bigpond.con", "ACCEPT_OR_WARN", ".con typo: syntactically valid (ASSUMPTION: no typo hint)"),
           (" olivia.nguyen@example.com.au", "olivia.nguyen@example.com.au", "ACCEPT_AFTER_TRIM", "leading space"),
           ("olivia.nguyen@example.com.au ", "olivia.nguyen@example.com.au", "ACCEPT_AFTER_TRIM", "trailing space")]
for p in INJECT:
    emails.append((p, "", "REJECT", "injection probe in email field"))
for t in (253, 254, 255, 256):
    v = long_email(t)
    assert len(v) == t
    emails.append((v, v, "ACCEPT" if t <= 254 else "REJECT", f"boundary: total length {t}"))
write("email_address", emails)

# ---------- otp_code (observed: 6 boxes "Digit 1".."Digit 6"; "Verify & Login" disabled until 6 digits)
otp = [("<FLDR_OTP>", "<6 digits>", "ACCEPT_FORMAT", "QA bypass OTP from .env for the QA number (" + OBS + ": login succeeded); value not stored in this file")]
for v, why in [("100000", "library valid format"), ("999999", "boundary all nines"), ("482913", "library valid format"), ("000000", "all zeroes / replay"),
               ("011111", "leading zero kept (string, not number)"), ("111111", "weak code")]:
    otp.append((v, v, "ACCEPT_FORMAT", why + "; server REJECT unless issued"))
g = lcg(6)
for i in range(75):
    v = f"{next(g) % 1000000:06d}"
    otp.append((v, v, "ACCEPT_FORMAT", f"random-looking 6-digit #{i + 1}; server REJECT unless issued"))
for n in range(0, 6):
    v = "123456"[:n]
    otp.append((v, v, "REJECT_VERIFY_DISABLED", f"{n} digits (min-1 or less); " + OBS + " Verify & Login disabled"))
otp.append(("45678", "45678", "REJECT_VERIFY_DISABLED", "5-digit bypass first supplied by requester; UI has 6 boxes"))
for n in range(7, 13):
    v = "1234567890123"[:n]
    otp.append((v, v[:6], "TRUNCATE_TO_6", f"{n} digits: extra chars must not be accepted"))
for v, exp, why in [("abcdef", "REJECT_INPUT", "letters"), ("12 34 56", "ACCEPT_IF_SPACES_STRIPPED", "spaces in pasted code"), (" <FLDR_OTP>", "ACCEPT_IF_TRIMMED", "leading space before the QA OTP"),
                    ("48956 ", "REJECT_VERIFY_DISABLED", "5 digits + trailing space"), ("12345a", "REJECT_INPUT", "5 digits + letter"), ("1234５6", "REJECT_INPUT", "full-width digit"),
                    ("12-345", "REJECT_INPUT", "hyphen"), ("١٢٣٤٥٦", "REJECT_INPUT", "Arabic-Indic digits"), ("\U0001F642" * 6, "REJECT_INPUT", "6 emoji"), ("1.2345", "REJECT_INPUT", "decimal point"),
                    ("+12345", "REJECT_INPUT", "plus sign"), ("1e5000", "REJECT_INPUT", "exponent notation"), ("0x1234", "REJECT_INPUT", "hex prefix")]:
    otp.append((v, re.sub(r"\s", "", v)[:6], exp, why))
write("otp_code", otp)

# ---------- postcode / state (ASSUMPTION: on Customer/Job address forms)
RNG = [(200, 299, "ACT"), (800, 999, "NT"), (1000, 1999, "NSW"), (2000, 2599, "NSW"), (2600, 2618, "ACT"), (2619, 2898, "NSW"), (2900, 2920, "ACT"),
       (2921, 2999, "NSW"), (3000, 3999, "VIC"), (4000, 4999, "QLD"), (5000, 5999, "SA"), (6000, 6999, "WA"), (7000, 7999, "TAS"), (8000, 8999, "VIC"), (9000, 9999, "QLD")]


def pc_state(pc):
    for a, b, s in RNG:
        if a <= int(pc) <= b:
            return s
    return None


pcs = []
NOTES = {"0200": "library says NT-min; real 0200-0299 is ACT (register C-02)", "7999": "library says invalid; TAS range is 7000-7999 (register C-03)",
         "9999": "library says invalid; 9000-9999 is QLD PO Box (register C-03)", "0800": "NT Darwin; leading zero must be preserved"}
cands = ["2000", "2601", "3000", "4000", "5000", "6000", "7000", "0800", "0820", "0200", "7999", "9999", "0199", "0300", "0799", "1000", "0999"]
for a, b, s in RNG:
    cands += [f"{a:04d}", f"{b:04d}", f"{max(a - 1, 0):04d}", f"{min(b + 1, 9999):04d}"]
for k in range(0, 10000, 100):
    cands.append(f"{k:04d}")
for v in cands:
    s = pc_state(v)
    pcs.append((v, v, f"ACCEPT_FORMAT state={s}" if s else "REJECT_UNALLOCATED", NOTES.get(v, "range boundary / sample")))
for v, why in [("200", "3 digits"), ("20000", "5 digits"), ("200 0", "internal space"), ("N/A", "text"), ("abcd", "letters"), ("", "empty"), (" ", "whitespace"), ("\U0001F642", "emoji"),
               ("-200", "negative"), ("2.00", "decimal"), ("2000​", "hidden char"), ("２０００", "full-width digits")]:
    pcs.append((v, "", "REJECT", why))
write("postcode", pcs)

STATES = [("NSW", "New South Wales"), ("VIC", "Victoria"), ("QLD", "Queensland"), ("WA", "Western Australia"), ("SA", "South Australia"), ("TAS", "Tasmania"),
          ("ACT", "Australian Capital Territory"), ("NT", "Northern Territory")]
st = []
for a, b in STATES:
    st += [(a, a, "ACCEPT", f"library state: {b}"), (b, a, "ACCEPT_IF_FREE_TEXT_OR_LABEL", f"full name of {a}"), (a.lower(), a, "ACCEPT_CASE_INSENSITIVE", f"lowercase {a}"),
           (f" {a} ", a, "ACCEPT_AFTER_TRIM", f"whitespace {a}"), (a.title() if len(a) > 2 else a[0] + a[1:].lower(), a, "ACCEPT_CASE_INSENSITIVE", f"mixed case {a}")]
for v in ["CA", "NY", "TX", "FL", "WA-US", "AKL", "Auckland", "Ontario", "BC", "Bavaria", "NZ", "XX", "N/A", "", " ", "\U0001F642", "NSW VIC", "N S W", "0", "12"] + INJECT:
    st.append((v, "", "REJECT", "foreign/invalid state must not be offered/accepted"))
for i in range(30):
    st.append((f"{STATES[i % 8][0]}{i}", "", "REJECT", f"state code + digit suffix #{i + 1}"))
write("state", st)

# ---------- ABN / TFN
def abn_ok(s):
    d = re.sub(r"\s", "", s)
    if not re.fullmatch(r"\d{11}", d):
        return False
    x = [int(c) for c in d]
    x[0] -= 1
    return sum(a * b for a, b in zip(x, [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19])) % 89 == 0


def tfn_ok(s):
    d = re.sub(r"\s", "", s)
    return bool(re.fullmatch(r"\d{9}", d)) and sum(int(c) * k for c, k in zip(d, [1, 4, 3, 7, 5, 8, 6, 9, 10])) % 11 == 0


def fmt_abn(d):
    return f"{d[:2]} {d[2:5]} {d[5:8]} {d[8:]}"


abn = [("33 102 417 032", "33102417032", "ACCEPT", "library valid; mod-89 verified"), ("33102417032", "33102417032", "ACCEPT", "no spaces"),
       ("12 345 678 901", "12345678901", "REJECT", "library invalid checksum")]
found, n = [], 10000000000
while len(found) < 60:  # deterministic scan for checksum-valid ABNs
    n += 7919
    if abn_ok(str(n)):
        found.append(str(n))
for d in found:
    abn.append((fmt_abn(d), d, "ACCEPT", "generated checksum-valid ABN (mod-89)"))
for d in found[:35]:
    bad = d[:-1] + str((int(d[-1]) + 1) % 10)
    abn.append((fmt_abn(bad), bad, "REJECT", "valid ABN with last digit changed: checksum fail"))
for i, (v, why) in enumerate([("1234567890", "10 digits (min-1)"), ("123456789012", "12 digits (max+1)"), ("", "empty"), ("   ", "whitespace"), ("33 102 417 03A", "letter"),
                              ("\U0001F642", "emoji"), ("00 000 000 000", "all zeroes"), ("33-102-417-032", "hyphens"), ("33.102.417.032", "dots"), ("ABN 33 102 417 032", "prefix text"),
                              ("33 102 417 032 ", "trailing space"), ("33​102417032", "hidden char")] + [(p, "injection probe") for p in INJECT[:6]]):
    abn.append((v, re.sub(r"\s", "", v), "REJECT" if not abn_ok(v) else "ACCEPT_AFTER_TRIM", why))
write("abn", abn)

tfn = [("123 456 782", "123456782", "ACCEPT", "library valid; mod-11 verified"), ("123 456 789", "123456789", "REJECT", "library invalid mod-11")]
found, n = [], 100000000
while len(found) < 60:
    n += 7919
    if tfn_ok(str(n)):
        found.append(str(n))
for d in found:
    tfn.append((f"{d[:3]} {d[3:6]} {d[6:]}", d, "ACCEPT", "generated mod-11-valid TFN"))
for d in found[:40]:
    bad = d[:-1] + str((int(d[-1]) + 1) % 10)
    tfn.append((f"{bad[:3]} {bad[3:6]} {bad[6:]}", bad, "REJECT", "valid TFN with last digit changed"))
for v, why in [("12345678", "8 digits (min-1)"), ("1234567", "7 digits"), ("1234567890", "10 digits (max+1)"), ("", "empty"), ("   ", "whitespace"), ("123 456 78A", "letter"),
               ("000 000 000", "all zeroes"), ("123-456-782", "hyphens"), ("123456782 ", "trailing space"), ("\U0001F642", "emoji")]:
    tfn.append((v, re.sub(r"\s", "", v), "ACCEPT_AFTER_TRIM" if tfn_ok(v) else "REJECT", why))
write("tfn", tfn)

# ---------- BSB / account number
bsb = [("062-000", "062-000", "ACCEPT", "library valid"), ("123-456", "123-456", "ACCEPT", "library valid"), ("032-198", "032-198", "ACCEPT", "library valid")]
g = lcg(32)
for i in range(90):
    d = f"{next(g) % 1000000:06d}"
    bsb.append((f"{d[:3]}-{d[3:]}", f"{d[:3]}-{d[3:]}", "ACCEPT", f"generated XXX-XXX #{i + 1}"))
for v, why in [("062000", "no hyphen"), ("062 000", "space separator"), ("06-2000", "hyphen misplaced"), ("062-00", "5 digits (min-1)"), ("062-0000", "7 digits (max+1)"),
               ("ABC-DEF", "letters"), ("", "empty"), (" ", "whitespace"), ("062--000", "double hyphen"), ("-062000", "leading hyphen"), ("062-000-", "trailing hyphen"),
               ("062_000", "underscore"), ("062–000", "en dash"), ("0", "single digit"), ("0620000000", "10 digits"), ("\U0001F642", "emoji"), ("BSB 062-000", "prefix text"),
               ("062-00O", "letter O for zero"), ("62-000", "5 digits")] + [(p, "injection probe") for p in INJECT[:6]]:
    d = re.sub(r"\D", "", v)
    if re.fullmatch(r"\d{3}-\d{3}", v):
        exp = "ACCEPT"
    elif len(d) == 6 and re.fullmatch(r"[\d\s-]+", v):
        exp = "ACCEPT_IF_NORMALISED"
    else:
        exp = "REJECT"
    bsb.append((v, d[:3] + "-" + d[3:] if len(d) == 6 else "", exp, why))
write("bsb", bsb)

acct = []
for n in range(1, 13):
    v = "".join(str((i + 1) % 10) for i in range(n))
    acct.append((v, v, "ACCEPT" if 6 <= n <= 9 else "REJECT", f"length {n} ({'in range 6-9' if 6 <= n <= 9 else 'out of range'})"))
g = lcg(9)
for i in range(80):
    v = str(100000 + next(g) % 899999)[: 6 + i % 4]
    acct.append((v, v, "ACCEPT", f"generated numeric #{i + 1}, {len(v)} digits"))
for v, exp, why in [("000012345", "ACCEPT", "4 leading zeros (allowed)"), ("00000123456", "REJECT", "leading zeros > 4 (library negative)"), ("00000012", "REJECT", "6 leading zeros"),
                    ("12345A", "REJECT", "letter"), ("12 3456", "REJECT", "internal space"), ("12-3456", "REJECT", "hyphen"), ("", "REJECT", "empty"), ("   ", "REJECT", "whitespace"),
                    ("\U0001F642", "REJECT", "emoji"), ("123456.0", "REJECT", "decimal"), ("-123456", "REJECT", "negative"), ("+123456", "REJECT", "plus sign"), ("1e6", "REJECT", "exponent"),
                    (" 123456", "ACCEPT_AFTER_TRIM", "leading space"), ("123456 ", "ACCEPT_AFTER_TRIM", "trailing space"), ("１２３４５６", "REJECT", "full-width digits")] + [(p, "REJECT", "injection probe") for p in INJECT[:6]]:
    acct.append((v, v.strip() if exp.startswith("ACCEPT") else "", exp, why))
write("account_number", acct)

# ---------- names
def name_rows(kind, pool):
    rows = [(n, n, "ACCEPT", f"AU library {kind}") for n in pool]
    rows += [(n.upper(), n.upper(), "ACCEPT", "uppercase") for n in pool] + [(n.lower(), n.lower(), "ACCEPT", "lowercase") for n in pool]
    rows += [(f"  {n} ", n, "ACCEPT_AFTER_TRIM", "surrounding whitespace") for n in pool]
    rows += [(f"{pool[i]}-{pool[(i + 3) % 10]}", f"{pool[i]}-{pool[(i + 3) % 10]}", "ACCEPT", "double-barrel") for i in range(10)]
    rows += [(f"{pool[i]} {pool[(i + 1) % 10]}", f"{pool[i]} {pool[(i + 1) % 10]}", "ACCEPT", "two-part name") for i in range(10)]
    rows += [(f"{pool[i]}{i + 1}", "", "REJECT_OR_WARN", "digit suffix") for i in range(10)]
    rows += [("O'Brien", "O'Brien", "ACCEPT", "apostrophe"), ("Smith-Jones", "Smith-Jones", "ACCEPT", "hyphen"), ("Mary Anne", "Mary Anne", "ACCEPT", "space"),
             ("D’Souza", "D’Souza", "ACCEPT", "typographic apostrophe"), ("Nguyễn", "Nguyễn", "ACCEPT", "Vietnamese diacritic (AU-common)"), ("José", "José", "ACCEPT", "accent")]
    for k in (1, 2, 50, 99, 100, 101, 150, 200, 254, 255):
        rows.append(("N" * k, "N" * k if k <= 100 else "", "ACCEPT" if k <= 100 else "REJECT", f"boundary: {k} chars (max=100 ASSUMPTION - {ASM})"))
    rows += [("", "", "REJECT", "empty"), ("   ", "", "REJECT", "spaces only"), ("User1234", "", "REJECT_OR_WARN", "digits (library negative)"), ("\U0001F642", "", "REJECT", "emoji only"),
             ("123", "", "REJECT_OR_WARN", "digits only"), ("!@#$%", "", "REJECT", "symbols only"), ("-", "", "REJECT", "single hyphen"), ("'", "", "REJECT", "single apostrophe")]
    rows += [(p, "", "REJECT_OR_ESCAPED", "XSS/SQLi/template probe (stored & reflected)") for p in INJECT]
    return rows


write("first_name", name_rows("first name", FIRST))
write("last_name", name_rows("last name", LAST))

# ---------- date_of_birth dd/mm/yyyy
def dob(s):
    try:
        return datetime.datetime.strptime(s, "%d/%m/%Y").date() if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s) else None
    except ValueError:
        return None


dobs = []
for v, why in [("14/02/1990", "valid"), ("29/02/2000", "leap day (div by 400)"), ("01/01/1900", "boundary: min (ASSUMPTION)"), ("31/12/2025", "valid past date"),
               ("31/12/1899", "min-1 (ASSUMPTION)"), ("29/02/1900", "NOT leap (div by 100 not 400)"), ("31/04/2024", "April has 30 days"), ("32/01/2024", "day 32"),
               ("00/01/2024", "day 0"), ("13/13/2024", "month 13"), ("02/14/1990", "US mm/dd order"), ("1990-02-14", "ISO in dd/mm/yyyy field"), ("", "empty"), ("   ", "whitespace"),
               ("14/02/90", "2-digit year"), ("1/1/2000", "no zero padding"), ("14-02-1990", "hyphens"), ("14.02.1990", "dots"), ("14/02/1990 ", "trailing space"), ("aa/bb/cccc", "letters")]:
    d = dob(v)
    dobs.append((v, d.isoformat() if d else "", "ACCEPT" if d and d >= datetime.date(1900, 1, 1) else "REJECT", why))
for y in range(1900, 2101, 4):  # every 4th year: 29 Feb leap logic (1900/2100 are NOT leap)
    v = f"29/02/{y}"
    d = dob(v)
    dobs.append((v, d.isoformat() if d else "", "ACCEPT" if d else "REJECT", f"29 Feb {y}: {'leap' if d else 'not a leap year'}"))
for m, dd in enumerate([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], 1):
    v = f"{dd:02d}/{m:02d}/2024"
    dobs.append((v, dob(v).isoformat(), "ACCEPT", f"last day of month {m} (2024 leap)"))
    v2 = f"{dd + 1:02d}/{m:02d}/2024"
    d2 = dob(v2)
    dobs.append((v2, d2.isoformat() if d2 else "", "ACCEPT" if d2 else "REJECT", f"last day + 1, month {m}"))
for y in range(1900, 2026, 5):
    v = f"14/02/{y}"
    dobs.append((v, dob(v).isoformat(), "ACCEPT", f"valid DOB sweep {y}"))
write("date_of_birth", dobs)

# ---------- amount_aud (Invoices / Items; GST 10% - ASSUMPTION)
amt = []
def amt_row(v, why):
    d = re.sub(r"[$]", "", v)
    ok = bool(re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d{1,2})?|\d+(\.\d{1,2})?", d))
    n = d.replace(",", "")
    gst = round(float(n) * 0.10 + 1e-9, 2) if ok else None
    tot = f"${float(n) + gst:,.2f}" if ok else "n/a"
    amt.append((v, f"{float(n):.2f}" if ok else "", "ACCEPT" if ok else "REJECT", f"{why}; GST={('%.2f' % gst) if ok else 'n/a'}; total={tot}"))


for v, why in [("0.00", "zero"), ("0.01", "min positive"), ("1100.00", "subtotal 1,100.00 -> total 1,210.00"), ("$1,100.00", "typed with $ and comma"), ("1100", "no decimals"),
               ("99999999.99", "large (ASSUMPTION max)"), ("-0.01", "negative"), ("1100.005", "3 decimals"), ("abc", "letters"), ("", "empty"), ("   ", "whitespace"),
               ("1,10,0.00", "bad grouping"), (".5", "no leading digit"), ("5.", "trailing dot"), ("1e3", "exponent"), ("$", "symbol only"), ("$$5", "double symbol")]:
    amt_row(v, why)
for i in range(1, 91):
    amt_row(f"{i * 137 % 9973 + i * 0.05:.2f}" if i % 3 else f"{i * 1000 + 0.99:,.2f}", f"generated amount #{i}")
write("amount_aud", amt)

# ---------- street_address
ADDR = [("12 Macquarie Street", "Sydney", "NSW", "2000"), ("88 Bourke Street", "Melbourne", "VIC", "3000"), ("145 Eagle Street", "Brisbane", "QLD", "4000"),
        ("27 Adelaide Terrace", "Perth", "WA", "6000"), ("101 Rundle Mall", "Adelaide", "SA", "5000"), ("9 Brisbane Street", "Hobart", "TAS", "7000"),
        ("21 London Circuit", "Canberra", "ACT", "2601"), ("76 Mitchell Street", "Darwin", "NT", "0800")]
rows = []
for a, c, s, p in ADDR:
    full = f"{a}, {c} {s} {p}"
    rows += [(full, full, "ACCEPT", f"AU library {s}"), (full.upper(), full.upper(), "ACCEPT", "uppercase"), (f"  {full} ", full, "ACCEPT_AFTER_TRIM", "whitespace"),
             (f"Unit {3 + len(c)}/{full}", f"Unit {3 + len(c)}/{full}", "ACCEPT", "unit prefix"), (f"Level 2, {full}", f"Level 2, {full}", "ACCEPT", "level prefix"),
             (full.replace("Street", "St").replace("Terrace", "Tce").replace("Circuit", "Cct"), "", "ACCEPT", "abbreviated street type"),
             (full + "​", full, "ACCEPT_AFTER_CLEAN", "hidden zero-width char")]
for i in range(1, 41):
    a, c, s, p = ADDR[i % 8]
    rows.append((f"{i * 7} {a.split(' ', 1)[1]}, {c} {s} {p}", "", "ACCEPT", f"street number sweep #{i}"))
for k in (1, 2, 100, 254, 255, 256):
    rows.append(("1" * k, "1" * k if k <= 254 else "", "ACCEPT" if k <= 254 else "REJECT_OR_TRUNCATE", f"boundary: {k} chars (max=254 ASSUMPTION)"))
rows += [("", "", "REJECT", "empty (if required)"), ("   ", "", "REJECT", "whitespace")] + [(p, "", "REJECT_OR_ESCAPED", "injection probe") for p in INJECT]
write("street_address", rows)

for k, v in sorted(COUNTS.items()):
    print(f"{k}.csv: {v} rows")
