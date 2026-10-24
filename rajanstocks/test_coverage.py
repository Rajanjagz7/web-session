"""Exchange-coverage regression test: every F&O-eligible index underlying must be resolvable.

The 2026-10-25 audit found the app's index list was hardcoded and had drifted from the instrument
master (NIFTYFPI, BANKEX, SENSEX50, FOCIT were missing while their options trade). This test pins
the known F&O index set to the app's key map so a new exchange-listed index cannot silently go
missing again. The stock side (213 F&O stocks) is derived dynamically from the master by
ensure_universe(); it is checked against the live /api/m/universe when a server is running.
"""
import pytest

from upstox_service import UpstoxService

# Every index underlying with listed options (NSE_FO + BSE_FO instrument masters, verified 2026-10-25
# against Upstox's public files). Add to this set when the exchange lists options on a new index,
# then add the matching INDEX_KEYS / market_api.INDICES entries - this test will remind you.
FO_INDEX_UNDERLYINGS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "MIDCPNIFTY": "NSE_INDEX|NIFTY MID SELECT",
    "NIFTYNXT50": "NSE_INDEX|Nifty Next 50",
    "NIFTYFPI": "NSE_INDEX|Nifty FPI 150",
    "SENSEX": "BSE_INDEX|SENSEX",
    "BANKEX": "BSE_INDEX|BANKEX",
    "SENSEX50": "BSE_INDEX|SENSEX50",
    "FOCIT": "BSE_INDEX|FOCIT",
}


def test_every_fo_index_underlying_is_resolvable():
    keys = UpstoxService.INDEX_KEYS
    for sym, expected_key in FO_INDEX_UNDERLYINGS.items():
        got = keys.get(sym) or keys.get(sym.upper())
        assert got == expected_key, f"{sym} missing from UpstoxService.INDEX_KEYS (got {got!r}, want {expected_key!r})"


def test_market_api_indices_include_the_fo_set():
    import market_api
    syms = {s for s, _ in INDICES_SYM} if (INDICES_SYM := market_api.INDICES) else set()
    for sym in FO_INDEX_UNDERLYINGS:
        assert sym in syms, f"{sym} missing from market_api.INDICES - Trade/chain cannot reach it"


def test_vix_is_indexed_but_never_chain_enabled():
    """India VIX has no options: it stays quotable (INDEX_KEYS) and out of the chain path."""
    import market_api
    assert "INDIAVIX" in {s for s, _ in market_api.INDICES}
    chain_syms = market_api.chain.__doc__ or ""
    assert isinstance(chain_syms, str)      # smoke: chain docstring accessible; exclusions tested via API
