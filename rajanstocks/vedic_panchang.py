"""Sidereal (Lahiri) Panchang calculations for the Daily NIFTY 50 Vedic Astro report.

Real ephemeris math via Skyfield (JPL DE421), not fabricated. Degrees given are
geocentric apparent ecliptic longitudes with the Lahiri ayanamsa subtracted.

Honesty note: Rahu/Ketu here are the MEAN lunar node (a standard closed-form
IAU formula), not the true/osculating node. True-node longitude needs the
Moon's instantaneous orbital-plane geometry (position x velocity vectors),
which isn't implemented here - don't present this as "true node" output.
"""
from datetime import datetime, timedelta
from skyfield.api import load, wgs84

MUMBAI_LAT = 18.96
MUMBAI_LON = 72.82

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
TITHI_NAMES_SHUKLA = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
]
TITHI_NAMES_KRISHNA = TITHI_NAMES_SHUKLA[:-1] + ["Amavasya"]
YOGAS = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti",
    "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
    "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]
RASHIS = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrischika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
]
WEEKDAY_SANSKRIT = {
    0: "Somavara", 1: "Mangalavara", 2: "Budhavara", 3: "Guruvara",
    4: "Shukravara", 5: "Shanivara", 6: "Ravivara",
}
# Rahu Kaal is the N-th eighth of the daylight period (sunrise->sunset), N keyed by Python weekday() (Mon=0).
RAHU_KAAL_SEGMENT = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}

_PLANETS = [
    ("Sun", "sun"), ("Moon", "moon"), ("Mars", "mars"), ("Mercury", "mercury"),
    ("Jupiter", "jupiter barycenter"), ("Venus", "venus"), ("Saturn", "saturn barycenter"),
]


def lahiri_ayanamsa(julian_year: float) -> float:
    """Standard linear approximation around J2000.0 - arcsecond-level/year accuracy, fine for daily Panchang."""
    return 23.85 + (julian_year - 2000.0) * 50.2388 / 3600.0


def mean_lunar_node_longitude(t) -> float:
    """IAU mean ascending node of the Moon's orbit (degrees, tropical). This is the MEAN node, not the true node."""
    jd_tt = t.tt
    T = (jd_tt - 2451545.0) / 36525.0
    omega = 125.0445222 - 1934.1362608 * T + 0.0020708 * T ** 2 + T ** 3 / 450000.0
    return omega % 360.0


def _sidereal_lon(eph, earth, body, t, ayanamsa):
    apparent = earth.at(t).observe(eph[body]).apparent()
    lon, _, _ = apparent.ecliptic_latlon()
    return (lon.degrees - ayanamsa) % 360.0


def compute_panchang(dt_utc: datetime, lat: float = MUMBAI_LAT, lon: float = MUMBAI_LON) -> dict:
    """Full Panchang + sidereal planetary snapshot for the given UTC instant."""
    eph = load('de421.bsp')
    ts = load.timescale()
    earth = eph['earth']
    t = ts.from_datetime(dt_utc)
    ayanamsa = lahiri_ayanamsa(t.J)

    sun_lon = _sidereal_lon(eph, earth, 'sun', t, ayanamsa)
    moon_lon = _sidereal_lon(eph, earth, 'moon', t, ayanamsa)

    tithi_raw = ((moon_lon - sun_lon) % 360) / 12.0
    tithi_num = int(tithi_raw) + 1  # 1..30
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    tithi_idx = (tithi_num - 1) if paksha == "Shukla" else (tithi_num - 16)
    tithi_name = (TITHI_NAMES_SHUKLA if paksha == "Shukla" else TITHI_NAMES_KRISHNA)[tithi_idx]
    tithi_pct_remaining = 1.0 - (tithi_raw - int(tithi_raw))

    nak_span = 360.0 / 27.0
    nak_idx = int(moon_lon / nak_span)
    nakshatra = NAKSHATRAS[nak_idx % 27]
    nak_pct_remaining = 1.0 - ((moon_lon % nak_span) / nak_span)

    yoga_idx = int(((sun_lon + moon_lon) % 360) / nak_span)
    yoga = YOGAS[yoga_idx % 27]

    rashi = RASHIS[int(moon_lon / 30.0) % 12]

    rahu_mean = mean_lunar_node_longitude(t)
    ketu_mean = (rahu_mean + 180.0) % 360.0

    planets = {}
    for name, key in _PLANETS:
        planets[name] = round(_sidereal_lon(eph, earth, key, t, ayanamsa), 2)
    planets["Rahu (mean node)"] = round(rahu_mean, 2)
    planets["Ketu (mean node)"] = round(ketu_mean, 2)

    topos = wgs84.latlon(lat, lon)
    observer = earth + topos
    t0 = ts.from_datetime(dt_utc.replace(hour=0, minute=0, second=0, microsecond=0))
    t1 = ts.from_datetime(dt_utc.replace(hour=23, minute=59, second=0, microsecond=0))
    from skyfield import almanac
    f = almanac.sunrise_sunset(eph, topos)
    times, events = almanac.find_discrete(t0, t1, f)
    sunrise = next((ti for ti, ev in zip(times, events) if ev == 1), None)
    sunset = next((ti for ti, ev in zip(times, events) if ev == 0), None)

    return {
        "ayanamsa_lahiri_deg": round(ayanamsa, 4),
        "sun_sidereal_lon": round(sun_lon, 2),
        "moon_sidereal_lon": round(moon_lon, 2),
        "tithi_number": tithi_num,
        "tithi_name": tithi_name,
        "paksha": paksha,
        "tithi_ends_fraction_of_day_remaining": round(tithi_pct_remaining, 3),
        "nakshatra": nakshatra,
        "nakshatra_ends_fraction_remaining": round(nak_pct_remaining, 3),
        "yoga": yoga,
        "moon_rashi": rashi,
        "weekday_sanskrit": WEEKDAY_SANSKRIT[dt_utc.weekday()],
        "planets_sidereal_deg": planets,
        "node_type": "mean",  # honesty flag - NOT true node
        "sunrise_utc": sunrise.utc_iso() if sunrise else None,
        "sunset_utc": sunset.utc_iso() if sunset else None,
    }


def rahu_kaal_window(sunrise_utc_iso: str, sunset_utc_iso: str, weekday_py: int):
    """Rahu Kaal = the Nth eighth of (sunrise, sunset) for this weekday. Returns (start_iso, end_iso) in UTC."""
    if not sunrise_utc_iso or not sunset_utc_iso:
        return None, None
    sunrise = datetime.fromisoformat(sunrise_utc_iso.replace("Z", "+00:00"))
    sunset = datetime.fromisoformat(sunset_utc_iso.replace("Z", "+00:00"))
    segment = RAHU_KAAL_SEGMENT[weekday_py]
    eighth = (sunset - sunrise) / 8
    start = sunrise + eighth * (segment - 1)
    end = start + eighth
    return start.isoformat(), end.isoformat()
