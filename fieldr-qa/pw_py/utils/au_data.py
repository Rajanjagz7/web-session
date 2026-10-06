"""Australian test-data constants, reused across specs. yopmail.com only — never example.com."""
import time

FIRST_NAMES = ["Olivia", "Noah", "Mia", "Jack", "Aria", "Liam", "Charlotte", "Zoe", "Ethan", "Amelia"]
LAST_NAMES = ["Nguyen", "Smith", "Collins", "Wilson", "Patel", "Brown", "Anderson", "Lee", "Khan", "White"]
ADDRESSES = [
    ("12 Macquarie Street", "Sydney", "NSW", "2000"),
    ("88 Bourke Street", "Melbourne", "VIC", "3000"),
    ("145 Eagle Street", "Brisbane", "QLD", "4000"),
]


def stamp() -> str:
    """A short, unique suffix so records from different test runs never collide."""
    return str(int(time.time()))[-6:]


def au_mobile_national(seed: int = 0) -> str:
    """A national-format AU mobile (04xx xxx xxx), unique per call via the epoch stamp."""
    return "04" + stamp()[:2] + str(seed % 10) + stamp()[-5:]


def yopmail(prefix: str) -> str:
    return f"{prefix}.{stamp()}@yopmail.com"
