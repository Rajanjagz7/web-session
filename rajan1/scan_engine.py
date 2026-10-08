from common import parse_bool, parse_float


def build_signal(open_, low, high, tol):
    is_ol = open_ is not None and low is not None and abs(open_ - low) <= tol
    is_oh = open_ is not None and high is not None and abs(open_ - high) <= tol
    if is_ol and is_oh:
        sig = "O=L=H"
    elif is_ol:
        sig = "O=L"
    elif is_oh:
        sig = "O=H"
    else:
        sig = ""
    return is_ol, is_oh, sig


def _near_spot_strikes(pool):
    """Given the pool of rows for ONE symbol+expiry, returns the set of strike
    values within roughly +-10 typical-strike-spacings of the ATM strike (the
    strike nearest the underlying's current spot) -- a normal broker-style
    default option-chain view (~21 strikes) instead of dumping every strike in
    the chain. Returns None when there isn't enough data to narrow safely
    (caller should then fall back to keeping everything).
    """
    spot = next((r.get("spot") for r in pool if r.get("spot") is not None), None)
    strikes = sorted({r["strike"] for r in pool if r.get("strike") is not None})
    if spot is None or len(strikes) < 3:
        return None
    diffs = sorted(b - a for a, b in zip(strikes, strikes[1:]) if b > a)
    if not diffs:
        return None
    spacing = diffs[len(diffs) // 2]  # median spacing -- robust to an odd missing strike
    if spacing <= 0:
        return None
    atm = min(strikes, key=lambda k: abs(k - spot))
    window = spacing * 10 + spacing / 2  # +-10 spacings, with half a spacing of slack
    return {k for k in strikes if abs(k - atm) <= window}


def scan(records, filters):
    sym_select = filters.get("symSelect", "__ALL__")
    inst_idx = parse_bool(filters.get("instIdx"), True)
    inst_stk = parse_bool(filters.get("instStk"), True)
    opt_type = filters.get("optType", "BOTH")
    exp_select = filters.get("expSelect", "nearest")
    low_on = parse_bool(filters.get("lowOn"), True)
    low_from = parse_float(filters.get("lowFrom"), 0)
    low_to = parse_float(filters.get("lowTo"), 0)
    prev_on = parse_bool(filters.get("prevOn"), True)
    prev_from = parse_float(filters.get("prevFrom"), 0)
    prev_to = parse_float(filters.get("prevTo"), 0)
    tol = parse_float(filters.get("tol"), 0.05)  # 1 NSE tick default
    min_oi = parse_float(filters.get("minOi"), 0)
    include_untraded = parse_bool(filters.get("includeUntraded"), False)
    show_mode = filters.get("showMode", "matches")
    cheap_on = parse_bool(filters.get("cheapOn"), False)
    cheap_from = parse_float(filters.get("cheapFrom"), 0.80)
    cheap_to = parse_float(filters.get("cheapTo"), 1.50)

    pool = records
    if sym_select and sym_select != "__ALL__":
        pool = [r for r in pool if r["symbol"] == sym_select]
    pool = [r for r in pool if (inst_idx and r["isIndex"]) or (inst_stk and not r["isIndex"])]
    if opt_type in ("CE", "PE"):
        pool = [r for r in pool if r["type"] == opt_type]

    if exp_select == "nearest":
        nearest = {}
        for r in pool:
            if r["expiry"] is None:
                continue
            cur = nearest.get(r["symbol"])
            if cur is None or r["expiry"] < cur:
                nearest[r["symbol"]] = r["expiry"]
        pool = [r for r in pool if r["expiry"] == nearest.get(r["symbol"])]

    total_contracts = len(pool)
    stat_ol = stat_oh = stat_match = 0
    results = []

    # When no range filter is active and Show mode is "all" (the truly
    # unfiltered state), a full option chain is a wall of irrelevant deep
    # ITM/OTM strikes -- default to a broker-style near-spot window instead.
    # This only narrows what's returned in `results`; totalContracts and the
    # stat counters below are computed from the full pool either way.
    near_spot_narrow = not low_on and not prev_on and show_mode == "all"
    near_spot_by_group = {}
    if near_spot_narrow:
        groups = {}
        for r in pool:
            groups.setdefault((r["symbol"], r["expiry"]), []).append(r)
        for group_key, group_rows in groups.items():
            near_spot_by_group[group_key] = _near_spot_strikes(group_rows)

    for r in pool:
        oi = r.get("oi") or 0
        vol = r.get("volume") or 0
        if oi < min_oi:
            continue
        if not include_untraded and oi == 0 and vol == 0:
            continue

        is_ol, is_oh, sig = build_signal(r.get("open"), r.get("low"), r.get("high"), tol)

        if is_ol:
            stat_ol += 1
        if is_oh:
            stat_oh += 1

        low = r.get("low")
        prev_close = r.get("prevCloseUsed")
        low_ok = (not low_on) or (low is not None and low_from <= low <= low_to)
        prev_ok = (not prev_on) or (prev_close is not None and prev_from <= prev_close <= prev_to)
        # "no range filter enabled" should never silently count as a match.
        is_match = (low_on or prev_on) and low_ok and prev_ok
        if is_match:
            stat_match += 1

        # An enabled range filter is a hard requirement, independent of Show
        # mode below — previously "All strikes" ignored these checkboxes
        # entirely, so turning a filter on had no visible effect unless Show
        # was also switched to "Matches only".
        if not (low_ok and prev_ok):
            continue

        # Cheap-option guard: checked ("cheapOn") shows contracts priced in
        # this band on EITHER LTP or Day Low -- unchecked instead actively
        # hides near-worthless junk where EITHER LTP or Day Low is at or
        # below the band's upper bound, so it doesn't clutter the default
        # view. This is a hard filter like the range filters above, applied
        # regardless of Show mode.
        ltp = r.get("close")
        ltp_in_band = ltp is not None and cheap_from <= ltp <= cheap_to
        low_in_band = low is not None and cheap_from <= low <= cheap_to
        ltp_junk = ltp is not None and ltp <= cheap_to
        low_junk = low is not None and low <= cheap_to
        if cheap_on:
            if not (ltp_in_band or low_in_band):
                continue
        else:
            if ltp_junk or low_junk:
                continue

        if show_mode == "ol":
            keep = is_ol
        elif show_mode == "oh":
            keep = is_oh
        elif show_mode == "any":
            keep = is_match or is_ol or is_oh
        elif show_mode == "matches":
            keep = is_match
        else:
            keep = True  # "all" — everything that passed the range filters above

        if keep and near_spot_narrow:
            allowed = near_spot_by_group.get((r["symbol"], r["expiry"]))
            if allowed is not None and r["strike"] not in allowed:
                keep = False

        if not keep:
            continue

        results.append({
            "symbol": r["symbol"],
            "expiry": r["expiry"],
            "strike": r["strike"],
            "type": r["type"],
            "sig": sig,
            "oi": r.get("oi"),
            "oiPct": r.get("oiPct"),
            "prevCloseUsed": prev_close,
            "open": r.get("open"),
            "high": r.get("high"),
            "low": low,
            "close": r.get("close"),
            "spot": r.get("spot"),
            "isMatch": is_match,
        })

    return {
        "results": results,
        "totalContracts": total_contracts,
        "statMatch": stat_match,
        "statOL": stat_ol,
        "statOH": stat_oh,
        # Number of contracts in the filtered pool (segment/symbol/expiry applied).
        # Frontend can show storeTotal separately to avoid "0 loaded" confusion
        # when Stocks Only is selected but only index data is cached.
        "poolSize": total_contracts,
    }
