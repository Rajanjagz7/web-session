import shutil, os, re, sys
SRC = "rajan"
def build(mode, folder, title, alias):
    dst = folder
    if os.path.exists(dst): shutil.rmtree(dst)
    os.makedirs(dst + "/public")
    shutil.copytree(f"{SRC}/api", f"{dst}/api", ignore=shutil.ignore_patterns("__pycache__", "data_cache"))
    for f in ["requirements.txt", "package.json", "package-lock.json", "favicon.svg"]:
        if os.path.exists(f"{SRC}/{f}"): shutil.copy(f"{SRC}/{f}", dst)
    shutil.copy(f"{SRC}/public/favicon.svg", f"{dst}/public/")
    h = open(f"{SRC}/public/options.html", encoding="utf-8").read()
    def sub(old, new, count=1, regex=False):
        nonlocal h
        n = h.count(old)
        assert n >= 1, old
        h = h.replace(old, new) if count == 0 else h.replace(old, new, count)
    inject = (f'<script>window.APP_MODE="{mode}";</script>\n'
              '<style>\n'
              '#stocksOnlyToggleNav,#stocksOnlyToggle,#instrGroup{display:none!important}\n'
              '</style>\n')
    sub("<head>", "<head>\n" + inject)
    sub("let stocksOnlyLock = false;", "let stocksOnlyLock = (window.APP_MODE === 'STOCK');")
    sub("stocksOnlyLock = false;\n  syncStocksOnlyButtons();", "stocksOnlyLock = (window.APP_MODE === 'STOCK');\n  syncStocksOnlyButtons();", 0)
    sub("    window.activeScan.rules.instrument = { enabled: true, index: true, stock: true };\n    stocksOnlyLock = false;",
        "    window.activeScan.rules.instrument = { enabled: true, index: true, stock: true };\n    stocksOnlyLock = (window.APP_MODE === 'STOCK');")
    sub("  // 3. Instrument Type (Index vs Stock)\n  if (rules.instrument && rules.instrument.enabled) {",
        "  // Deployment-mode hard lock (rajantrading = index only, rajanstocks = stocks only)\n"
        "  if (window.APP_MODE === 'INDEX' || window.APP_MODE === 'STOCK') {\n"
        "    const _isIdx = [\"NIFTY\", \"BANKNIFTY\", \"FINNIFTY\", \"MIDCPNIFTY\", \"SENSEX\", \"NIFTYNXT50\"].includes(contract.symbol) || contract.instr === \"Index\";\n"
        "    if (window.APP_MODE === 'INDEX' && !_isIdx) return explain ? { passed: false, failedRule: \"instrument\", reason: \"Index-only site\" } : false;\n"
        "    if (window.APP_MODE === 'STOCK' && _isIdx) return explain ? { passed: false, failedRule: \"instrument\", reason: \"Stocks-only site\" } : false;\n"
        "  }\n\n  // 3. Instrument Type (Index vs Stock)\n  if (rules.instrument && rules.instrument.enabled) {")
    sub("const shouldHide = stocksOnlyLock && indexSymbols.has(opt.value);",
        "const shouldHide = (stocksOnlyLock && indexSymbols.has(opt.value)) || (window.APP_MODE === 'INDEX' && !indexSymbols.has(opt.value));")
    sub("if (selectedWasHidden) {\n    sel.value = '__ALL__';\n    showToast('📦 Stocks Only is on — index selection cleared, showing all stocks', 'info');",
        "if (selectedWasHidden) {\n    sel.value = '__ALL__';\n    if (window.APP_MODE !== 'INDEX') showToast('📦 Stocks Only is on — index selection cleared, showing all stocks', 'info');")
    h = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", h, count=1, flags=re.S)
    open(f"{dst}/public/index.html", "w", encoding="utf-8").write(h)
    open(f"{dst}/vercel.json", "w").write('''{
  "version": 2,
  "alias": ["%s"],
  "builds": [
    { "src": "api/tv.js", "use": "@vercel/node" },
    { "src": "api/index.py", "use": "@vercel/python", "config": { "maxLambdaSize": "50mb" } },
    { "src": "public/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/tv.*", "dest": "api/tv.js" },
    { "src": "/api/.*", "dest": "api/index.py" },
    { "src": "/", "dest": "public/index.html" },
    { "src": "/(.*)", "dest": "public/$1" }
  ]
}
''' % alias)
build("ALL", "rajantrading", "Rajan Trading - NSE Options Screener", "rajantrading.vercel.app")
# rajanstocks = the rajan1 "new UI" app, as-is
if os.path.exists("rajanstocks_keep"): pass
