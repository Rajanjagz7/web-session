"""Loan Products API: negative, edge and boundary tests (POST/GET/PUT/DELETE /products).

WRITE BUDGET: gusdev rate-limits every write (POST/PUT/DELETE, even ones that fail validation)
to 100 per hour per session. This module is designed to stay under WRITE_BUDGET (default 92)
including cleanup deletes. Tests skip, never fail, when the limiter answers 429. Reads are not limited.
All products created here use realistic names and are deleted at teardown.
"""
import copy
import os

import pytest

from api import config
from api.api_client import APIClient

OTHER_LENDER = "6ab119e3983eb386149dce1b"  # Preventive Health Review (active)
INACTIVE_LENDER = "6ab217c4983eb386149dce32"  # ANZ (isActive=false)
SEEDED_PRODUCT = "6abde76fe6b189801e58343a"  # existing product - read only, never modified
WRITE_BUDGET = int(os.getenv("WRITE_BUDGET", "92"))

VALID = {
    "lenderId": OTHER_LENDER,
    "name": "Everyday Personal Loan",
    "type": "personal_loan",
    "description": "Fixed-rate unsecured personal loan for approved Australian residents.",
    "interestRateBps": 749,
    "comparisonRateBps": 812,
    "minAmountCents": 500000,
    "maxAmountCents": 5000000,
    "termMonths": [36],
    "eligibilityNotes": "Must be an Australian citizen or permanent resident.",
    "criteria": {
        "minAgeYears": 18,
        "maxAgeYears": 65,
        "minIncomeCentsPerYear": 4500000,
        "maxDebtToIncomeRatio": 6,
        "minMonthlySurplusCents": 50000,
    },
}


class Writer:
    """Counts writes, skips on 429, and deletes everything it created."""

    def __init__(self, client: APIClient):
        self.client = client
        self.writes = 0
        self.created: list[str] = []
        self.seq = 0

    def send(self, method, endpoint, **kw):
        if self.writes >= WRITE_BUDGET:
            pytest.skip(f"write budget {WRITE_BUDGET} reached (rate limit is 100/hour)")
        self.writes += 1
        r = self.client.request(method, endpoint, **kw)
        if r.status_code == 429:
            pytest.skip("write rate limit (429) - rerun after the window resets")
        return r

    def body(self, **over):
        self.seq += 1
        b = copy.deepcopy(VALID)
        b["name"] = f"{b['name']} {self.seq:02d}"
        for k, v in over.items():
            if v is _DROP:
                b.pop(k, None)
            else:
                b[k] = v
        return b

    def crit(self, **kw):
        c = copy.deepcopy(VALID["criteria"])
        c.update(kw)
        return self.body(criteria=c)

    def post(self, body):
        r = self.send("POST", "/products", json=body)
        if r.status_code in (200, 201):
            self.created.append(r.json()["data"]["_id"])
        return r

    def cleanup(self):
        for pid in self.created:
            try:
                self.client.request("DELETE", f"/products/{pid}")
                self.writes += 1
            except Exception:
                pass
        self.created.clear()


_DROP = object()


def bug(fx, why):
    """Confirmed defect: expected to fail today; turns into a hard failure (XPASS strict) once fixed."""
    return pytest.mark.xfail(strict=True, reason=f"{fx}: {why}")


def pm(q, why):
    """Behaviour accepted today that probably should not be; waiting for a product decision."""
    return pytest.mark.xfail(strict=False, reason=f"{q}: {why}")

X = pytest.mark.extended  # run in a separate rate-limit window: pytest -m extended


def ext(*vals):
    return [pytest.param(v, marks=X) for v in vals]


def ext2(*pairs):
    return [pytest.param(*pr, marks=X) for pr in pairs]


@pytest.fixture(scope="module")
def w(admin_client):
    wr = Writer(admin_client)
    yield wr
    wr.cleanup()


def fields(r):
    return {d["field"] for d in r.json().get("details", [])}


def assert_422(r, field=None):
    assert r.status_code == 422, f"{r.status_code}: {r.text[:200]}"
    assert r.json()["code"] == "VALIDATION_ERROR"
    if field:
        assert any(f == field or f.startswith(field) for f in fields(r)), fields(r)


# ---------------------------------------------------------------- reads (free)
class TestListReadNegative:
    @pytest.mark.parametrize(
        "params,field",
        [
            ({"skip": -1}, "skip"),
            ({"skip": "abc"}, "skip"),
            ({"skip": 1.5}, "skip"),
            ({"limit": 0}, "limit"),
            ({"limit": 101}, "limit"),
            ({"limit": "abc"}, "limit"),
            ({"type": "bogus"}, "type"),
            ({"type": "Pet Loan"}, "type"),
            ({"lenderId": "bad"}, "lenderId"),
            ({"isActive": "maybe"}, "isActive"),
            ({"search": "a" * 101}, "search"),
        ],
    )
    def test_invalid_query_is_422(self, admin_client, params, field):
        assert_422(admin_client.request("GET", "/products", params=params), field)

    def test_unknown_lender_filter_404(self, admin_client):
        r = admin_client.request("GET", "/products", params={"lenderId": "0" * 24})
        assert r.status_code == 404 and r.json()["code"] == "LENDER_NOT_FOUND"

    @pytest.mark.parametrize("limit", [1, 100])
    def test_limit_boundaries(self, admin_client, limit):
        r = admin_client.request("GET", "/products", params={"limit": limit})
        assert r.status_code == 200 and len(r.json()["data"]) <= limit

    def test_skip_beyond_end_is_empty_not_error(self, admin_client):
        r = admin_client.request("GET", "/products", params={"skip": 999999})
        assert r.status_code == 200 and r.json()["data"] == []

    @pytest.mark.parametrize("term", ["%", ".*", "(", "[a-", "😀", '{"$ne":1}', "<script>alert(1)</script>", "' OR '1'='1"])
    def test_search_hostile_input_is_inert(self, admin_client, term):
        r = admin_client.request("GET", "/products", params={"search": term})
        assert r.status_code == 200 and r.json()["data"] == []

    def test_search_case_insensitive(self, admin_client):
        a = admin_client.request("GET", "/products", params={"search": "ang"}).json()["totalCount"]
        b = admin_client.request("GET", "/products", params={"search": "ANG"}).json()["totalCount"]
        assert a == b >= 1
    @pytest.mark.parametrize("params", [{"sortBy": "bogus"}, {"sortOrder": "sideways"}])
    def test_invalid_sort_is_rejected(self, admin_client, params):
        """GUS-FX-0004 (fixed 2026-10-07): invalid sort values return 422, as on the users list."""
        assert_422(admin_client.request("GET", "/products", params=params))
    @pytest.mark.parametrize("sort_by", ["interestRateBps", "name", "minAmountCents"])
    def test_sort_actually_sorts(self, admin_client, sort_by):
        asc = admin_client.request("GET", "/products", params={"limit": 100, "sortBy": sort_by, "sortOrder": "asc"}).json()["data"]
        desc = admin_client.request("GET", "/products", params={"limit": 100, "sortBy": sort_by, "sortOrder": "desc"}).json()["data"]
        key = lambda p: (p[sort_by].lower() if isinstance(p[sort_by], str) else p[sort_by])
        assert [key(p) for p in asc] == sorted(key(p) for p in asc), "ascending sort is not in ascending order"
        assert [p["_id"] for p in asc] != [p["_id"] for p in desc], "asc and desc return the same order"

    def test_filter_by_inactive_returns_only_inactive(self, admin_client):
        r = admin_client.request("GET", "/products", params={"isActive": "false"})
        assert all(p["isActive"] is False for p in r.json()["data"])

    def test_filter_by_type_returns_only_that_type(self, admin_client):
        r = admin_client.request("GET", "/products", params={"type": "pet_loan"})
        assert r.json()["data"] and all(p["type"] == "pet_loan" for p in r.json()["data"])


class TestDetailReadNegative:
    @pytest.mark.parametrize("pid", ["zzz", "6ac368a6408954367774c20", "6ac368a6408954367774c20bb", '{"$ne":1}'])
    def test_malformed_id_422(self, admin_client, pid):
        assert_422(admin_client.request("GET", f"/products/{pid}"), "id")

    def test_nonexistent_id_404(self, admin_client):
        r = admin_client.request("GET", f"/products/{'0' * 24}")
        assert r.status_code == 404 and r.json()["code"] == "PRODUCT_NOT_FOUND"

    def test_path_traversal_not_routable(self, admin_client):
        r = admin_client.request("GET", "/products/..")
        assert r.status_code in (400, 404)

    def test_money_and_rates_are_integers(self, admin_client):
        d = admin_client.request("GET", f"/products/{SEEDED_PRODUCT}").json()["data"]
        for k in ("interestRateBps", "comparisonRateBps", "minAmountCents", "maxAmountCents"):
            assert isinstance(d[k], int) and d[k] >= 0
        assert d["minAmountCents"] <= d["maxAmountCents"]

    def test_no_internal_fields_leak(self, admin_client):
        raw = admin_client.request("GET", f"/products/{SEEDED_PRODUCT}").text.lower()
        for bad in ("password", "token", "__v", "stack"):
            assert bad not in raw


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/products", None),
    ("GET", f"/products/{SEEDED_PRODUCT}", None),
    ("POST", "/products", {}),
    ("PUT", f"/products/{SEEDED_PRODUCT}", {}),
    ("DELETE", f"/products/{SEEDED_PRODUCT}", None),
])
def test_unauthenticated_is_401(anon_client, method, path, body):
    """Never sends a body that could modify data: the request is rejected before the handler."""
    r = anon_client.request(method, path, json=body) if body is not None else anon_client.request(method, path)
    assert r.status_code == 401 and r.json()["code"] == "ACCESS_TOKEN_MISSING"


def test_tampered_token_is_401(admin_client):
    bad = APIClient()
    bad.session.cookies.update({k: v + "x" for k, v in admin_client.session.cookies.items()})
    r = bad.request("GET", "/products")
    assert r.status_code == 401 and r.json()["code"] == "ACCESS_TOKEN_INVALID"


# ---------------------------------------------------- create: required + type checks
class TestCreateRequiredFields:
    @pytest.mark.parametrize("field", ["lenderId", "name", "type", "interestRateBps", "minAmountCents", "maxAmountCents"])
    def test_missing_required_field(self, w, field):
        assert_422(w.post(w.body(**{field: _DROP})), field)

    def test_empty_object(self, w):
        r = w.send("POST", "/products", json={})
        assert_422(r)
        assert {"lenderId", "name", "type"} <= fields(r)

    def test_body_is_array(self, w):
        assert_422(w.send("POST", "/products", json=[]))
    def test_body_is_string_json(self, w):
        """GUS-FX-0001 (fixed 2026-10-07)."""
        r = w.send("POST", "/products", json="x")
        assert r.status_code in (400, 422), f"{r.status_code}: {r.text[:120]}"
    def test_malformed_json(self, w):
        """GUS-FX-0002 (fixed 2026-10-07)."""
        r = w.send("POST", "/products", data="{bad json", headers={"content-type": "application/json"})
        assert r.status_code == 400, f"{r.status_code}: {r.text[:120]}"


class TestCreateName:
    @pytest.mark.parametrize("name", ["", *ext("   ", "A")])
    def test_too_short(self, w, name):
        assert_422(w.post(w.body(name=name)), "name")

    def test_121_chars_rejected(self, w):
        assert_422(w.post(w.body(name="N" * 121)), "name")

    @pytest.mark.parametrize("name", [12345, *ext(None, ["a"], {"$ne": 1})])
    def test_wrong_type(self, w, name):
        assert_422(w.post(w.body(name=name)), "name")

    @pytest.mark.parametrize("name", ["AB", "N" * 120])
    def test_length_boundaries_accepted(self, w, name):
        r = w.post(w.body(name=name))
        assert r.status_code == 201 and r.json()["data"]["name"] == name
    def test_null_byte_rejected_cleanly(self, w):
        """GUS-FX-0003: confirmed 500 INTERNAL on 2026-10-05."""
        r = w.post(w.body(name="Home Saver\u0000Plan"))
        assert r.status_code == 422, f"{r.status_code}: {r.text[:120]}"

    def test_surrounding_whitespace_is_trimmed(self, w):
        r = w.post(w.body(name="  Padded Home Loan  "))
        assert r.status_code == 201
        assert r.json()["data"]["name"] == "Padded Home Loan"

    @X
    def test_markup_is_stored_verbatim_not_executed(self, w):
        name = "<b>Home</b> Saver & Co's \"Plan\""
        r = w.post(w.body(name=name))
        assert r.status_code == 201 and r.json()["data"]["name"] == name  # escaping is the UI's job (see UI spec)


class TestCreateTypeAndLender:
    @pytest.mark.parametrize("type_", ["Personal Loan", "bogus", None, *ext("PERSONAL_LOAN", "", 1, ["personal_loan"])])
    def test_invalid_type(self, w, type_):
        assert_422(w.post(w.body(type=type_)), "type")

    @pytest.mark.parametrize("lender", ["abc", "z" * 24, *ext("", None, 1, {"$ne": None})])
    def test_invalid_lender_id(self, w, lender):
        assert_422(w.post(w.body(lenderId=lender)), "lenderId")

    def test_nonexistent_lender_404(self, w):
        r = w.post(w.body(lenderId="0" * 24))
        assert r.status_code == 404 and r.json()["code"] == "LENDER_NOT_FOUND"
    def test_inactive_lender_rejected(self, w):
        """Decision 2026-10-05: products may only be created under active lenders."""
        if w.client.request("GET", f"/lenders/{INACTIVE_LENDER}").json()["data"]["isActive"]:
            pytest.skip("no lender is deactivated on dev; GUS-FX-0005 was verified fixed on 2026-10-07 with a temporary lender (409 LENDER_INACTIVE on create and on move)")
        r = w.post(w.body(lenderId=INACTIVE_LENDER))
        assert r.status_code in (409, 422), f"{r.status_code}: product created under an inactive lender"


class TestCreateNumbers:
    @pytest.mark.parametrize("v", [-1, 10001, 749.5, *ext("749", None, True, [749])])
    def test_interest_rate_invalid(self, w, v):
        assert_422(w.post(w.body(interestRateBps=v)), "interestRateBps")

    @pytest.mark.parametrize("v", [0, 10000])
    def test_interest_rate_boundaries(self, w, v):
        assert w.post(w.body(interestRateBps=v)).status_code == 201

    @pytest.mark.parametrize("v", [-1, 10001, *ext(812.5, "812", None)])
    def test_comparison_rate_invalid(self, w, v):
        assert_422(w.post(w.body(comparisonRateBps=v)), "comparisonRateBps")

    def test_comparison_rate_below_interest_rate_is_allowed(self, w):
        """Decision 2026-10-05: no comparison-rate validation for now, so this must be accepted."""
        r = w.post(w.body(interestRateBps=749, comparisonRateBps=700))
        assert r.status_code == 201, f"{r.status_code}: {r.text[:160]}"
    def test_zero_amount_range_rejected(self, w):
        """Q3 (needs PM decision, report Q3): min=0,max=0 means a loan of $0 - accepted today."""
        r = w.post(w.body(minAmountCents=0, maxAmountCents=0))
        assert r.status_code == 422, "a $0.00 - $0.00 loan product was created"


class TestCreateTerms:
    @pytest.mark.parametrize("terms", [[0], [1000], [13.5], *ext([-12], ["12"], 12, [None])])
    def test_invalid_terms(self, w, terms):
        assert_422(w.post(w.body(termMonths=terms)), "termMonths")

    @pytest.mark.parametrize("terms", [[1], [600]])
    def test_term_boundaries(self, w, terms):
        r = w.post(w.body(termMonths=terms))
        assert r.status_code == 201 and r.json()["data"]["termMonths"] == terms

    @X
    def test_duplicates_collapsed_and_sorted(self, w):
        r = w.post(w.body(termMonths=[60, 12, 12, 36]))
        assert r.status_code == 201 and r.json()["data"]["termMonths"] == [12, 36, 60]

    def test_empty_terms_allowed(self, w):
        """Q4 (report): a loan with no term at all is accepted."""
        """Decision 2026-10-05: a product with no term is allowed."""
        assert w.post(w.body(termMonths=[])).status_code == 201

    def test_missing_terms_allowed(self, w):
        """Same question: the UI submits without termMonths when no chip is selected."""
        assert w.post(w.body(termMonths=_DROP)).status_code == 201


class TestCreateCriteria:
    @pytest.mark.parametrize("kw", [
        {"minAgeYears": -1}, {"maxAgeYears": 200}, {"minAgeYears": 70, "maxAgeYears": 30}, {"minAgeYears": 18.5},
        {"minIncomeCentsPerYear": -1}, {"maxDebtToIncomeRatio": -1}, {"minMonthlySurplusCents": -1},
        *ext({"minAgeYears": 150}, {"maxAgeYears": 0}, {"minAgeYears": "18"}, {"minIncomeCentsPerYear": 100.5},
             {"maxDebtToIncomeRatio": "six"}, {"minMonthlySurplusCents": 0.5}),
    ])
    def test_invalid_criteria(self, w, kw):
        r = w.post(w.crit(**kw))
        assert_422(r)

    def test_criteria_wrong_type(self, w):
        assert_422(w.post(w.body(criteria="x")), "criteria")

    @X
    def test_unknown_criteria_key_not_persisted(self, w):
        r = w.post(w.crit(creditScoreMin=700))
        assert r.status_code in (201, 422)
        if r.status_code == 201:
            assert "creditScoreMin" not in r.json()["data"]["criteria"]


class TestCreateMassAssignment:
    def test_server_controlled_fields_ignored(self, w):
        r = w.post(w.body(isActive=False, _id="111111111111111111111111", createdAt="2000-01-01T00:00:00Z",
                          lender={"name": "Fake Bank", "isActive": True}, role="admin"))
        if r.status_code == 201:
            d = r.json()["data"]
            assert d["_id"] != "111111111111111111111111"
            assert d["createdAt"].startswith("2026")
            assert d["lender"]["name"] == "Preventive Health Review"
            assert "role" not in d
        else:
            assert_422(r)

    def test_duplicate_same_lender_type_name(self, w):
        """Duplicate lender+type+name is rejected with 409 (verified 2026-10-05)."""
        b = w.body(name="Home Saver Variable Rate", type="home_loan")
        assert w.post(b).status_code == 201
        assert w.post(copy.deepcopy(b)).status_code == 409


# ------------------------------------------------------------ update / delete
@pytest.fixture(scope="module")
def prod(w):
    r = w.post(w.body(name="Fixed Rate Car Loan", type="car_loan"))
    assert r.status_code == 201
    return r.json()["data"]["_id"]


class TestUpdateNegative:
    @pytest.mark.parametrize("payload,field", [
        ({"name": ""}, "name"), ({"type": "bogus"}, "type"), ({"interestRateBps": -1}, "interestRateBps"),
        ({"termMonths": [0]}, "termMonths"),
        pytest.param({"name": "N" * 121}, "name", marks=X), pytest.param({"interestRateBps": 10001}, "interestRateBps", marks=X),
        pytest.param({"minAmountCents": -1}, "minAmountCents", marks=X), pytest.param({"lenderId": "bad"}, "lenderId", marks=X),
    ])
    def test_invalid_update(self, w, prod, payload, field):
        assert_422(w.send("PUT", f"/products/{prod}", json=payload), field)

    def test_partial_update_cannot_break_min_max(self, w, prod):
        """Cross-field rule on a partial update: current max is 5,000,000; raising only the minimum above it."""
        r = w.send("PUT", f"/products/{prod}", json={"minAmountCents": 9000000})
        assert r.status_code == 422, f"{r.status_code}: min now exceeds max"
        d = w.client.request("GET", f"/products/{prod}").json()["data"]
        assert d["minAmountCents"] <= d["maxAmountCents"]

    @X
    def test_empty_update(self, w, prod):
        r = w.send("PUT", f"/products/{prod}", json={})
        assert r.status_code in (200, 422)

    def test_unknown_product(self, w):
        r = w.send("PUT", f"/products/{'0' * 24}", json={"description": "Updated."})
        assert r.status_code == 404 and r.json()["code"] == "PRODUCT_NOT_FOUND"

    def test_malformed_id(self, w):
        assert_422(w.send("PUT", "/products/zzz", json={"description": "Updated."}), "id")

    @X
    def test_move_to_nonexistent_lender(self, w, prod):
        r = w.send("PUT", f"/products/{prod}", json={"lenderId": "0" * 24})
        assert r.status_code == 404

    def test_valid_update_round_trip(self, w, prod):
        r = w.send("PUT", f"/products/{prod}", json={"description": "Updated fixed-rate car loan.", "interestRateBps": 689})
        assert r.status_code == 200
        d = w.client.request("GET", f"/products/{prod}").json()["data"]
        assert d["description"] == "Updated fixed-rate car loan." and d["interestRateBps"] == 689
        assert d["updatedAt"] >= d["createdAt"]

    def test_deactivated_product_hidden_from_active_filter(self, w, prod):
        r = w.send("PUT", f"/products/{prod}", json={"isActive": False})
        assert r.status_code == 200
        active = w.client.request("GET", "/products", params={"isActive": "true", "limit": 100}).json()["data"]
        assert prod not in [p["_id"] for p in active]
        inactive = w.client.request("GET", "/products", params={"isActive": "false", "limit": 100}).json()["data"]
        assert prod in [p["_id"] for p in inactive]


class TestDeleteNegative:
    def test_unknown_product(self, w):
        r = w.send("DELETE", f"/products/{'0' * 24}")
        assert r.status_code == 404 and r.json()["code"] == "PRODUCT_NOT_FOUND"

    def test_malformed_id(self, w):
        assert_422(w.send("DELETE", "/products/zzz"), "id")

    def test_double_delete_second_is_404(self, w):
        r = w.post(w.body(name="Short Term Pet Loan", type="pet_loan"))
        pid = r.json()["data"]["_id"]
        w.created.remove(pid)
        assert w.send("DELETE", f"/products/{pid}").status_code == 200
        assert w.send("DELETE", f"/products/{pid}").status_code == 404
        assert w.client.request("GET", f"/products/{pid}").status_code == 404
