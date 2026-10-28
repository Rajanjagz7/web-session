"""Industry labels for the cash universe (every listed NSE equity), which the exchange instrument list does not carry.
1) EXPLICIT: symbol -> industry, for names we know. Edit freely - this table wins over everything else.
2) KEYWORDS: the company name decides the rest (first match wins), e.g. any "... Cement ..." is Cement & Cement Products.
Anything that matches neither stays unlabelled ('') rather than guessed."""
import re

CEMENT = "Cement & Cement Products"

EXPLICIT = {s: CEMENT for s in (
    "ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "DALBHARAT", "JKCEMENT", "JKLAKSHMI", "RAMCOCEM", "INDIACEM", "STARCEMENT", "NUVOCO",
    "HEIDELBERG", "ORIENTCEM", "SAGCEM", "KCP", "NCLIND", "BIRLACORPN", "DECCANCEM", "VISAKAIND", "JSWCEMENT", "SHREDIGCEM",
    "PRISMJOHN", "MANGLMCEM", "KESORAMIND", "HIL", "EVERESTIND", "SANGHIIND", "ANDHRACEMT", "BARAKCEM", "CEMPRO")}

KEYWORDS = [
    (r"\bcements?\b|\bcemt\b", CEMENT),
    (r"pharma|drug|laborator|\blabs?\b|life ?science|biotech|remed|medi(?:cal|care)|health|hospital|diagnos", "Pharma & Healthcare"),
    (r"\bbank\b|bancorp", "Banks"),
    (r"insurance|assurance", "Insurance"),
    (r"financ|capital|credit|fincorp|leasing|housing fin|securities|broking|wealth|asset man", "Finance"),
    (r"textile|spinning|weav|yarn|fabric|cotton|garment|apparel|denim|fibre|fiber|silk|mills?\b", "Textiles"),
    (r"sugar|distiller|ethanol", "Sugar & Distilleries"),
    (r"steel|ispat|alloy|iron|metal|forg|casting|wire|tubes|pipes?\b|aluminium|copper|zinc|ferro", "Metals & Steel"),
    (r"power|energy|solar|wind|renew|electric(?:ity)?\b|thermal|hydro|transmission", "Power & Energy"),
    (r"oil|gas|petro|refiner|lubric", "Oil & Gas"),
    (r"chemical|chem\b|fertili[sz]|agro|pesticide|agri|dyes|pigment|polymer|plastic|rubber|paints?|coatings?|adhesive", "Chemicals & Agro"),
    (r"software|infotech|information tech|technolog|systems|digital|data|cyber|computer|\bit\b|infosys|solutions|cloud|\bai\b", "IT & Software"),
    (r"motor|auto|tyre|tire|vehicle|bearing|wheel|\bcars?\b|scooter|tractor", "Auto & Ancillaries"),
    (r"real ?estate|realty|developers|properties|infra ?struct|construct|housing|township|buildcon|engineers|projects", "Realty & Construction"),
    (r"hotel|resort|restaurant|tourism|travel|leisure|holiday|cinema|entertainment|media|broadcast|television|music|film|publish|print", "Hotels, Travel & Media"),
    (r"food|beverage|bever|tea|coffee|dairy|milk|biscuit|snack|spice|edible|rice|wheat|flour|agri ?product|consumer|retail|stores|mart\b|brands?", "FMCG & Consumer"),
    (r"paper|packag|glass|ceramic|tiles|sanitary|furnitur|wood|board|laminat", "Paper, Glass & Building"),
    (r"telecom|communication|broadband|network|tower|satellite", "Telecom"),
    (r"shipping|logistic|port|transport|cargo|airline|aviation|railway|rail\b|freight|courier", "Transport & Logistics"),
    (r"defence|aero|ammunition|shipyard|marine", "Defence & Shipbuilding"),
    (r"electronic|electrical|cable|switchgear|transformer|battery|semicon|appliance", "Electricals & Electronics"),
    (r"engineering|machine|industries|industrial|tools|pumps?|compressor|valves?|capital goods|equipment|turbine|boiler", "Capital Goods"),
    (r"education|school|university|learning|training", "Education"),
]
_RX = [(re.compile(p, re.I), lab) for p, lab in KEYWORDS]


def of(sym, name=""):
    """Industry for a symbol: explicit table first, then the company-name keywords, else ''."""
    sym = (sym or "").upper()
    if sym in EXPLICIT:
        return EXPLICIT[sym]
    nm = name or ""
    for rx, lab in _RX:
        if rx.search(nm):
            return lab
    return ""
