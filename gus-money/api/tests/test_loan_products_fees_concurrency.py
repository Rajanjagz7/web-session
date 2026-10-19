"""Loan Products: fees (API) and concurrency/race tests.

Closes two gaps from LOAN_PRODUCTS_QA_REPORT.md. Fee payload shape captured from the UI (2026-10-05):
    fees: [{"name": str, "amountCents": int, "frequency": "one_off" | "monthly" | "annual"}]
Same write budget rules as test_loan_products_api.py (100 writes/hour). Run: WRITE_BUDGET=38 pytest -m extended <this file>
"""
import copy
from concurrent.futures import ThreadPoolExecutor

import pytest

from api.api_client import APIClient
from api.tests.test_loan_products_api import VALID, Writer, assert_422, bug, fields, pm

pytestmark = pytest.mark.extended


@pytest.fixture(scope="module")
def w(admin_client):
    wr = Writer(admin_client)
    yield wr
    wr.cleanup()


def fee(name="Establishment fee", amount=25050, frequency="one_off"):
    return {"name": name, "amountCents": amount, "frequency": frequency}


def clone_client(src: APIClient) -> APIClient:
    c = APIClient()
    c.session.cookies.update(src.session.cookies)
    return c


# ------------------------------------------------------------------ fees
class TestFees:
    def test_all_frequencies_round_trip(self, w):
        fees = [fee("Establishment fee", 25050, "one_off"), fee("Monthly account fee", 1000, "monthly"), fee("Annual package fee", 39500, "annual")]
        r = w.post(w.body(name="Fee Round Trip Loan", fees=fees))
        assert r.status_code == 201, r.text[:200]
        stored = w.client.request("GET", f"/products/{r.json()['data']['_id']}").json()["data"]["fees"]
        assert [(f["name"], f["amountCents"], f["frequency"]) for f in stored] == [(f["name"], f["amountCents"], f["frequency"]) for f in fees]

    @pytest.mark.parametrize("bad,field", [
        ([fee(frequency="weekly")], "fees"),
        ([fee(amount=-1)], "fees"),
        ([fee(amount=250.5)], "fees"),
        ([fee(name="")], "fees"),
        ([fee(name="F" * 121)], "fees"),
        ("x", "fees"),
        (["x"], "fees"),
        ([{}], "fees"),
    ])
    def test_invalid_fee_rejected(self, w, bad, field):
        assert_422(w.post(w.body(name="Fee Validation Loan", fees=bad)), field)

    @pm("Q9", "a $0.00 fee is accepted")
    def test_zero_amount_fee_rejected(self, w):
        assert w.post(w.body(name="Zero Fee Loan", fees=[fee(amount=0)])).status_code == 422

    def test_fee_count_is_capped(self, w):
        """51 fees are rejected (verified 2026-10-05); the exact cap was not measured. The UI only allows 1 fee."""
        many = [fee(f"Fee number {i}", 100) for i in range(51)]
        assert w.post(w.body(name="Many Fees Loan", fees=many)).status_code == 422

    def test_duplicate_fee_names_do_not_crash(self, w):
        r = w.post(w.body(name="Duplicate Fee Loan", fees=[fee("Account fee", 500, "monthly"), fee("Account fee", 500, "monthly")]))
        assert r.status_code in (201, 409, 422), r.text[:200]


# ----------------------------------------------------------- concurrency
class TestConcurrency:
    def test_parallel_identical_creates_yield_one_product(self, w):
        """Race: 3 identical creates at once. Sequential duplicates are rejected with 409 (see core suite)."""
        body = w.body(name="Race Create Home Loan", type="home_loan")
        n = 3
        w.writes += n
        clients = [clone_client(w.client) for _ in range(n)]
        with ThreadPoolExecutor(n) as ex:
            res = list(ex.map(lambda c: c.request("POST", "/products", json=copy.deepcopy(body)), clients))
        codes = sorted(r.status_code for r in res)
        w.created += [r.json()["data"]["_id"] for r in res if r.status_code == 201]
        assert 429 not in codes or pytest.skip("rate limited")
        assert codes.count(201) == 1, f"duplicate products created by a race: {codes}"
        assert all(c in (201, 409) for c in codes), codes

    def test_parallel_updates_leave_a_consistent_record(self, w):
        r = w.post(w.body(name="Race Update Car Loan", type="car_loan"))
        pid = r.json()["data"]["_id"]
        texts = [f"Concurrent edit {i}" for i in range(3)]
        w.writes += len(texts)
        clients = [clone_client(w.client) for _ in texts]
        with ThreadPoolExecutor(len(texts)) as ex:
            res = list(ex.map(lambda a: a[0].request("PUT", f"/products/{pid}", json={"description": a[1]}), zip(clients, texts)))
        codes = [x.status_code for x in res]
        assert 429 not in codes or pytest.skip("rate limited")
        assert all(c == 200 for c in codes), codes
        d = w.client.request("GET", f"/products/{pid}").json()["data"]
        assert d["description"] in texts
        assert d["name"] == "Race Update Car Loan" and d["interestRateBps"] == VALID["interestRateBps"]

    @pm("GUS-FX-0026", "intermittent: two simultaneous DELETEs of one product sometimes both return 200 (2 of 5 runs)")
    def test_parallel_deletes_one_wins(self, w):
        r = w.post(w.body(name="Race Delete Pet Loan", type="pet_loan"))
        pid = r.json()["data"]["_id"]
        w.created.remove(pid)
        w.writes += 2
        clients = [clone_client(w.client) for _ in range(2)]
        with ThreadPoolExecutor(2) as ex:
            res = list(ex.map(lambda c: c.request("DELETE", f"/products/{pid}"), clients))
        codes = sorted(x.status_code for x in res)
        assert 429 not in codes or pytest.skip("rate limited")
        assert codes == [200, 404], codes
        assert w.client.request("GET", f"/products/{pid}").status_code == 404


# ------------------------------------------------- lender product count
class TestLenderProductCount:
    @bug("GUS-FX-0017", "lender productCount includes deactivated products (lists/detail show 6 when only 4 are live)")
    def test_product_count_excludes_deactivated_products(self, w):
        """Create 3 products under one lender, deactivate 1: the lender must count 2 live products more than before."""
        lenders = w.client.request("GET", "/lenders", params={"limit": 100}).json()["data"]
        lender = next(l for l in lenders if l["name"] == "AMP Bank")
        before = lender["productCount"]
        made = [w.post(w.body(lenderId=lender["_id"], name=f"AMP Count Check Loan {i}")).json()["data"]["_id"] for i in range(3)]
        assert w.send("PUT", f"/products/{made[0]}", json={"isActive": False}).status_code == 200
        after = next(l for l in w.client.request("GET", "/lenders", params={"limit": 100}).json()["data"] if l["_id"] == lender["_id"])["productCount"]
        assert after == before + 2, f"productCount {after}; expected {before + 2} (3 created, 1 deactivated)"


# ------------------------------------------------------------ terms (months)
class TestTermRules:
    """PUT /products/:id termMonths rules (verified 2026-10-06). About 15 writes."""

    @pytest.fixture(scope="class")
    def pid(self, w):
        r = w.post(w.body(name="Term Rules Personal Loan", termMonths=[12, 24]))
        assert r.status_code == 201
        return r.json()["data"]["_id"]

    def stored(self, w, pid):
        return w.client.request("GET", f"/products/{pid}").json()["data"]["termMonths"]

    @pytest.mark.parametrize("sent,expected", [
        ([24], [24]),                              # replaced, not merged with [12, 24]
        ([60, 12, 36, 12], [12, 36, 60]),          # de-duplicated and sorted
        ([1], [1]),                                # lower boundary
        ([600], [600]),                            # upper boundary
        ([], []),                                  # clearing is allowed (decision 2026-10-05)
        (list(range(1, 25)), list(range(1, 25))),  # 24 terms is the maximum
    ])
    def test_valid_term_updates(self, w, pid, sent, expected):
        assert w.send("PUT", f"/products/{pid}", json={"termMonths": sent}).status_code == 200
        assert self.stored(w, pid) == expected

    @pytest.mark.parametrize("bad", [[0], [601], [13.5], ["12"], 12, None, list(range(1, 26))])
    def test_invalid_terms_are_rejected_and_nothing_changes(self, w, pid, bad):
        before = self.stored(w, pid)
        assert_422(w.send("PUT", f"/products/{pid}", json={"termMonths": bad}), "termMonths")
        assert self.stored(w, pid) == before


# ------------------------------------------------------------ lender contact phone (country rules)
class TestLenderPhone:
    """POST /lenders contactPhone. Needs a logo (presign + S3 PUT from Python) and a unique valid ABN per record.
    About 11 writes; every accepted record is deleted."""

    @staticmethod
    def _abns(client, count):
        import random
        weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
        used = {l["abn"] for l in client.request("GET", "/lenders", params={"limit": 100}).json()["data"]}
        rnd, out = random.Random(11), []
        while len(out) < count:
            c = "".join(str(rnd.randint(0, 9)) for _ in range(11))
            d = [int(x) for x in c]
            d[0] -= 1
            if c[0] != "0" and c not in used and sum(a * b for a, b in zip(d, weights)) % 89 == 0:
                out.append(f"{c[:2]} {c[2:5]} {c[5:8]} {c[8:]}")
        return out

    @pytest.fixture(scope="class")
    def lender_env(self, admin_client):
        import requests
        pres = admin_client.request("POST", "/uploads/presign", json={"target": "profiles", "files": [{"fileName": "phone-test-logo.png", "contentType": "image/png", "fileType": "image"}]})
        if pres.status_code == 429:
            pytest.skip("write rate limit (429)")
        u = pres.json()["data"]["uploads"][0]
        png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc0f01f0005000201a53a6fc20000000049454e44ae426082")
        assert requests.put(u["uploadUrl"], data=png, headers={"Content-Type": "image/png"}, timeout=30).status_code == 200
        env = {"logo": u["publicUrl"], "abns": self._abns(admin_client, 8), "made": [], "n": 0}
        yield env
        for lid in env["made"]:
            admin_client.request("DELETE", f"/lenders/{lid}")

    def _create(self, admin_client, env, phone):
        i = env["n"]
        env["n"] += 1
        names = ["Harbour Credit Partners", "Southern Cross Finance", "Capital Trust Lending", "Pioneer Mutual Finance", "Riverbend Credit Union", "Coastal Lending Group", "Summit Finance Australia", "Evergreen Credit"]
        body = {"name": names[i], "legalName": names[i] + " Pty Ltd", "abn": env["abns"][i], "website": "https://www." + names[i].lower().replace(" ", "") + ".com.au",
                "contactName": "Aarav Mehta", "contactEmail": f"phone.check{i + 1}@yopmail.com", "contactPhone": phone, "logo": env["logo"]}
        r = admin_client.request("POST", "/lenders", json=body)
        if r.status_code == 201:
            env["made"].append(r.json()["data"]["_id"])
        return r

    @pytest.mark.parametrize("phone", ["+919876543210", "+61412345678"])
    def test_valid_numbers_are_accepted(self, admin_client, lender_env, phone):
        assert self._create(admin_client, lender_env, phone).status_code == 201

    @pytest.mark.parametrize("phone", ["9876543210", "+6112345"])
    def test_generic_format_errors_are_rejected(self, admin_client, lender_env, phone):
        r = self._create(admin_client, lender_env, phone)
        assert r.status_code == 422 and r.json()["details"][0]["field"] == "contactPhone"

    @pytest.mark.xfail(strict=True, reason="GUS-FX-0023: backend only checks generic international format, not country rules (India: 10 digits starting 6-9)")
    @pytest.mark.parametrize("phone", ["+91123456789", "+911234567890", "+9198765432101", "+915876543210"])
    def test_invalid_indian_numbers_are_rejected(self, admin_client, lender_env, phone):
        r = self._create(admin_client, lender_env, phone)
        assert r.status_code == 422, f"{phone} was accepted ({r.status_code})"
