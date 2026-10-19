"""Adds 25 realistic products to the Westpac lender on STAGE (re-runnable: products that already exist are skipped).
Needs the stage session in .auth/stage.json (see stage_lib.py)."""
import math, random, sys
sys.path.insert(0, ".")
from stage_lib import stage_session, call

random.seed(20261007)
st = stage_session()
lenders = {l["name"]: l for l in call(st, "GET", "/lenders", params={"limit": 100}).json()["data"]}
westpac = lenders["Westpac"]["_id"]
have = {p["name"] for p in call(st, "GET", "/products", params={"lenderId": westpac, "limit": 100}).json()["data"]}

def pmt(principal, rate_pct, months):
    r = rate_pct / 100 / 12
    return principal / months if r == 0 else principal * r / (1 - (1 + r) ** -months)

SPEC = {  # type: amount lows/highs ($), rate range (%), term options (months), income ($), debt-to-income, surplus floor ($)
    "pet_loan": dict(lo=(1000, 3000), hi=(15000, 30000), rate=(8.5, 13.0), terms=[12, 24, 36, 48, 60], inc=(30000, 45000), dti=6),
    "personal_loan": dict(lo=(2000, 5000), hi=(35000, 60000), rate=(7.0, 15.0), terms=[12, 24, 36, 48, 60, 84], inc=(35000, 60000), dti=6),
    "car_loan": dict(lo=(8000, 15000), hi=(80000, 160000), rate=(5.5, 10.0), terms=[12, 24, 36, 48, 60, 84], inc=(40000, 70000), dti=6),
    "home_loan": dict(lo=(50000, 150000), hi=(1000000, 2500000), rate=(5.3, 7.0), terms=[240, 300, 360], inc=(60000, 100000), dti=6.5),
    "investment_loan": dict(lo=(150000, 300000), hi=(1500000, 3500000), rate=(5.9, 7.5), terms=[240, 300, 360], inc=(90000, 150000), dti=7),
    "business_loan": dict(lo=(10000, 25000), hi=(300000, 1500000), rate=(7.0, 12.0), terms=[12, 24, 36, 48, 60, 84, 120], inc=(50000, 100000), dti=5),
}
PRODUCTS = [
    ("pet_loan", "Pet Wellness Loan", "Unsecured loan for routine vet care, dental work and pet insurance premiums."),
    ("pet_loan", "Emergency Vet Care Loan", "Fast-approval loan for urgent veterinary treatment and after-hours clinics."),
    ("pet_loan", "Pet Surgery Instalment Loan", "Spread the cost of planned surgery and specialist referrals over fixed instalments."),
    ("personal_loan", "Flexi Personal Loan", "Fixed-rate personal loan with free extra repayments for any worthwhile purpose."),
    ("personal_loan", "Debt Consolidation Plus", "Combine credit cards and personal loans into one repayment at a lower rate."),
    ("personal_loan", "Holiday Travel Loan", "Finance a trip with a fixed rate and a repayment plan that ends before your next holiday."),
    ("personal_loan", "Home Renovation Loan", "Unsecured loan for kitchens, bathrooms and landscaping up to $60,000."),
    ("personal_loan", "Wedding Day Loan", "Plan the big day without using a credit card."),
    ("car_loan", "New Car Fixed Rate Loan", "Secured fixed-rate loan for new vehicles with comprehensive insurance."),
    ("car_loan", "Used Car Loan Saver", "Secured loan for used vehicles up to 10 years old at the time of settlement."),
    ("car_loan", "Electric Vehicle Loan", "Discounted rate for fully electric and plug-in hybrid vehicles."),
    ("car_loan", "Caravan and Camper Loan", "Secured finance for caravans, campervans and trailers."),
    ("home_loan", "Fixed Rate Home Loan Saver", "Fixed-rate home loan for 1 to 5 years with repayment certainty."),
    ("home_loan", "Offset Home Loan Plus", "Variable home loan with a 100% offset account and redraw."),
    ("home_loan", "Low Deposit Home Loan", "Home loan for buyers with a deposit of 5% to 10%, subject to lenders mortgage insurance."),
    ("home_loan", "Construction Home Loan", "Progress-payment loan for building a new home."),
    ("home_loan", "Refinance Home Loan Special", "Switch your existing home loan and receive a refinance rate discount."),
    ("investment_loan", "Investor Interest-Only Loan", "Interest-only investment loan with a five-year interest-only period."),
    ("investment_loan", "Investor Principal and Interest Loan", "Principal and interest loan for residential investment property."),
    ("investment_loan", "Portfolio Growth Investor Loan", "Cross-collateralised finance for building a multi-property portfolio."),
    ("investment_loan", "Off-the-Plan Investor Loan", "Finance for off-the-plan apartments with a delayed settlement."),
    ("business_loan", "Small Business Growth Loan", "Term loan for expansion, fit-outs and new hires."),
    ("business_loan", "Business Overdraft Term Loan", "A fixed-term facility to smooth cash flow and pay suppliers."),
    ("business_loan", "Commercial Vehicle Finance", "Secured finance for vans, utes and trucks used in the business."),
    ("business_loan", "Seasonal Cash Flow Loan", "Short-term working capital for businesses with seasonal trade."),
]
FEES = [("Establishment fee", (150, 1200), "one_off"), ("Application fee", (100, 800), "one_off"), ("Account keeping fee", (5, 30), "monthly"),
        ("Annual package fee", (195, 495), "annual"), ("Settlement fee", (200, 500), "one_off")]

def money(r, step):
    return int(random.randint(r[0], r[1]) // step * step)

made, remaining = 0, None
for typ, name, desc in PRODUCTS:
    s = SPEC[typ]
    rate = round(random.uniform(*s["rate"]), 2)
    comp = round(rate + random.uniform(0.05, 0.9), 2)
    step = 5000 if typ in ("home_loan", "investment_loan") else 1000
    lo, hi = money(s["lo"], step), money(s["hi"], step)
    terms = sorted(random.sample(s["terms"], k=random.randint(2, len(s["terms"]))))
    surplus = math.ceil(pmt(lo, rate, max(terms)) * 1.10 / 50) * 50  # repayment on the smallest loan over the longest term + 10%
    crit = {"minAgeYears": 18, "maxAgeYears": random.choice([65, 70, 75]), "minIncomeCentsPerYear": money(s["inc"], 5000) * 100,
            "maxDebtToIncomeRatio": s["dti"], "minMonthlySurplusCents": surplus * 100}
    body = {"lenderId": westpac, "name": name, "type": typ, "description": desc, "eligibilityNotes": "Australian resident aged 18+, subject to credit assessment.",
            "interestRateBps": round(rate * 100), "comparisonRateBps": round(comp * 100), "minAmountCents": lo * 100, "maxAmountCents": hi * 100,
            "termMonths": terms, "criteria": crit}
    if random.random() < 0.7:
        body["fees"] = [{"name": n, "amountCents": random.randint(*rng) * 100, "frequency": f} for n, rng, f in random.sample(FEES, k=random.randint(1, 2))]
    if name in have:
        print("skip (exists):", name); continue
    r = call(st, "POST", "/products", json=body)
    remaining = r.headers.get("ratelimit-remaining", remaining)
    if r.status_code != 201:
        j = r.json(); d = (j.get("details") or [{}])[0]
        print(f"FAILED {name}: {r.status_code} {d.get('field', '')}: {d.get('message') or j.get('message')}"); break
    made += 1
print(f"created {made} products | stage writes remaining: {remaining}")
