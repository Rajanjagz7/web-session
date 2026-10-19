# Rajan TradingView Indicator Pack --- Verified Chartink + Chat Rules

**Version:** 1.0\
**Platform:** TradingView Pine Script v6\
**Market focus:** NSE / NIFTY / BANKNIFTY / Indian equities\
**Purpose:** Convert the user's supplied trading notes and public
Chartink screener concepts into named TradingView indicators.

------------------------------------------------------------------------

## Important distinction

The supplied Chartink URLs are public screeners, but several of them do
not expose their current filter formula in the indexed page. I have
therefore divided the implementation into:

-   **Verified / directly translatable:** the public screener exposes
    the rule.
-   **Chat-derived:** the rule comes directly from the trading notes
    supplied by the user.
-   **Configurable interpretation:** the concept is clear, but the exact
    original screener formula is not exposed.
-   **Not translated:** a fundamental/data field cannot be reliably
    reproduced with Pine alone.

This prevents a guessed formula from being presented as the original
author's exact strategy.

------------------------------------------------------------------------

# Indicator 01 --- Rajan Uptrend Hammer Support Entry

## Source

Chat rule:

> Uptrend = Higher Highs + Higher Lows.\
> In an uptrend, price retraces to support and forms a Hammer.

## Logic

A signal requires:

1.  Price above the trend EMA.
2.  Trend EMA rising.
3.  A recent swing low acting as support.
4.  Price close to that support.
5.  Hammer candle structure.

### Pine Script

``` pine
//@version=6
indicator("Rajan - Uptrend Hammer Support Entry", overlay=true, max_labels_count=500)

groupTrend = "Trend"
emaLength = input.int(50, "Trend EMA", minval=1, group=groupTrend)
useStructure = input.bool(true, "Require HH/HL Structure", group=groupTrend)
pivotLeft = input.int(3, "Pivot Left", minval=1, group=groupTrend)
pivotRight = input.int(3, "Pivot Right", minval=1, group=groupTrend)

groupHammer = "Hammer"
maxBodyPct = input.float(0.35, "Maximum Body / Range", minval=0.05, maxval=0.8, step=0.05, group=groupHammer)
minLowerWickBody = input.float(2.0, "Minimum Lower Wick / Body", minval=1, step=0.25, group=groupHammer)
maxUpperWickBody = input.float(0.5, "Maximum Upper Wick / Body", minval=0, step=0.1, group=groupHammer)

groupSupport = "Support"
supportDistancePct = input.float(1.0, "Maximum Distance From Support %", minval=0.1, step=0.1, group=groupSupport)

emaTrend = ta.ema(close, emaLength)

ph = ta.pivothigh(high, pivotLeft, pivotRight)
pl = ta.pivotlow(low, pivotLeft, pivotRight)

var float previousSwingHigh = na
var float lastSwingHigh = na
var float previousSwingLow = na
var float lastSwingLow = na

if not na(ph)
    previousSwingHigh := lastSwingHigh
    lastSwingHigh := ph

if not na(pl)
    previousSwingLow := lastSwingLow
    lastSwingLow := pl

higherHigh = not na(previousSwingHigh) and not na(lastSwingHigh) and lastSwingHigh > previousSwingHigh
higherLow = not na(previousSwingLow) and not na(lastSwingLow) and lastSwingLow > previousSwingLow

emaUp = emaTrend > emaTrend[1]
trendFilter = close > emaTrend and emaUp
structureFilter = higherHigh and higherLow

uptrend = trendFilter and (not useStructure or structureFilter)

support = lastSwingLow
nearSupport = not na(support) and math.abs(close - support) / close * 100 <= supportDistancePct

body = math.abs(close - open)
range = high - low
upperWick = high - math.max(open, close)
lowerWick = math.min(open, close) - low

hammer =
     range > 0 and
     body > syminfo.mintick and
     body / range <= maxBodyPct and
     lowerWick / body >= minLowerWickBody and
     upperWick / body <= maxUpperWickBody

hammerEntry = uptrend and nearSupport and hammer and barstate.isconfirmed

plot(emaTrend, "Trend EMA", linewidth=2)
plot(support, "Swing Support", linewidth=2, style=plot.style_stepline)

plotshape(
     hammerEntry,
     title="Hammer Support Entry",
     style=shape.labelup,
     location=location.belowbar,
     text="HAMMER\nBUY",
     size=size.small
)

alertcondition(
     hammerEntry,
     title="Rajan Hammer Support Entry",
     message="Rajan Hammer Support Entry detected."
)
```

------------------------------------------------------------------------

# Indicator 02 --- Rajan W Pattern Support Entry

## Source

Chat rule:

> Stock is in an uptrend, pulls back near support, forms a W pattern and
> breaks the middle high.

## Logic

-   Two swing lows are approximately equal.
-   Price is near support.
-   The middle swing high becomes the neckline.
-   Signal occurs when price closes above the neckline.

### Pine Script

``` pine
//@version=6
indicator("Rajan - W Pattern Support Entry", overlay=true, max_labels_count=500)

pivotLeft = input.int(3, "Pivot Left", minval=1)
pivotRight = input.int(3, "Pivot Right", minval=1)

emaLength = input.int(50, "Trend EMA")
supportTolerancePct = input.float(1.0, "Low Similarity / Support Tolerance %", minval=0.1, step=0.1)

emaTrend = ta.ema(close, emaLength)

ph = ta.pivothigh(high, pivotLeft, pivotRight)
pl = ta.pivotlow(low, pivotLeft, pivotRight)

var float low1 = na
var float low2 = na
var float neckline = na

if not na(pl)
    low1 := low2
    low2 := pl

if not na(ph)
    neckline := ph

similarLows =
     not na(low1) and
     not na(low2) and
     math.abs(low1 - low2) / low1 * 100 <= supportTolerancePct

uptrend = close > emaTrend and emaTrend > emaTrend[1]

nearSupport =
     not na(low2) and
     math.abs(close - low2) / close * 100 <= supportTolerancePct

wSetup = uptrend and similarLows and nearSupport and not na(neckline)
wBreakout = wSetup and close > neckline and barstate.isconfirmed

plot(emaTrend, "Trend EMA", linewidth=2)
plot(low2, "W Support", linewidth=2, style=plot.style_stepline)
plot(neckline, "W Neckline", linewidth=2, style=plot.style_stepline)

plotshape(
     wBreakout,
     title="W Pattern BUY",
     style=shape.labelup,
     location=location.belowbar,
     text="W BUY",
     size=size.small
)

alertcondition(
     wBreakout,
     title="Rajan W Pattern Breakout",
     message="Rajan W Pattern support breakout detected."
)
```

------------------------------------------------------------------------

# Indicator 03 --- Rajan 9/15 EMA Intraday Setup

## Chartink connection

The supplied 9/15 EMA screeners are explicitly named around a 9 EMA / 15
EMA setup. Public TradingView descriptions also commonly use 9/15 EMA as
a momentum/trend confirmation pair. citeturn2search6turn2search11

## Core rules

### Bullish

-   EMA 9 \> EMA 15.
-   Optional crossover.
-   Price above both EMAs.
-   Optional volume confirmation.
-   Optional higher-timeframe trend confirmation.

### Bearish

-   EMA 9 \< EMA 15.
-   Price below both EMAs.
-   Optional volume confirmation.

### Pine Script

``` pine
//@version=6
indicator("Rajan - 9/15 EMA Intraday Setup", overlay=true, max_labels_count=500)

fastLength = input.int(9, "Fast EMA")
slowLength = input.int(15, "Slow EMA")

useTrend = input.bool(true, "Use Trend EMA")
trendLength = input.int(50, "Trend EMA")

useVolume = input.bool(true, "Use Volume Confirmation")
volumeLength = input.int(20, "Volume SMA")
volumeMultiplier = input.float(1.0, "Minimum Volume / Average", step=0.1)

signalMode = input.string(
     "Crossover",
     "Signal Mode",
     options=["Crossover", "Trend State"]
)

ema9 = ta.ema(close, fastLength)
ema15 = ta.ema(close, slowLength)
trendEma = ta.ema(close, trendLength)

avgVolume = ta.sma(volume, volumeLength)
volumeOK = not useVolume or volume >= avgVolume * volumeMultiplier

bullTrend = close > ema9 and ema9 > ema15
bearTrend = close < ema9 and ema9 < ema15

bullCross = ta.crossover(ema9, ema15)
bearCross = ta.crossunder(ema9, ema15)

bullSignal =
     signalMode == "Crossover" ?
     bullCross and volumeOK and (not useTrend or close > trendEma) :
     bullTrend and volumeOK and (not useTrend or close > trendEma)

bearSignal =
     signalMode == "Crossover" ?
     bearCross and volumeOK and (not useTrend or close < trendEma) :
     bearTrend and volumeOK and (not useTrend or close < trendEma)

plot(ema9, "EMA 9", linewidth=2)
plot(ema15, "EMA 15", linewidth=2)
plot(useTrend ? trendEma : na, "Trend EMA", linewidth=1)

plotshape(
     bullSignal and barstate.isconfirmed,
     title="9/15 BUY",
     style=shape.labelup,
     location=location.belowbar,
     text="9/15 BUY",
     size=size.small
)

plotshape(
     bearSignal and barstate.isconfirmed,
     title="9/15 SELL",
     style=shape.labeldown,
     location=location.abovebar,
     text="9/15 SELL",
     size=size.small
)

alertcondition(
     bullSignal and barstate.isconfirmed,
     title="9/15 EMA BUY",
     message="Rajan 9/15 EMA bullish signal."
)

alertcondition(
     bearSignal and barstate.isconfirmed,
     title="9/15 EMA SELL",
     message="Rajan 9/15 EMA bearish signal."
)
```

------------------------------------------------------------------------

# Indicator 04 --- Rajan Tight Range + EMA Compression

## Chartink source

Supplied:

`my-favourite-pattern-tight-range`

The Chartink profile associated with the copied screener identifies it
as **"My favourite pattern tight range with ema pattern"**, so this
indicator keeps that exact concept in the name. citeturn2search0

## Logic

-   Tight range / compression.
-   EMA compression.
-   Optional volume contraction.
-   Breakout after compression.

### Pine Script

``` pine
//@version=6
indicator("Rajan - Tight Range + EMA Compression", overlay=true)

rangeLength = input.int(7, "Range Lookback")
emaFastLength = input.int(9, "Fast EMA")
emaSlowLength = input.int(15, "Slow EMA")

volumeLength = input.int(20, "Volume Average")
volumeFactor = input.float(0.8, "Maximum Volume / Average", step=0.05)

emaDistancePct = input.float(1.0, "Maximum EMA Distance %", step=0.1)

range = high - low
lowestRange = ta.lowest(range, rangeLength)

nrSignal = range <= lowestRange

emaFast = ta.ema(close, emaFastLength)
emaSlow = ta.ema(close, emaSlowLength)

emaDistance =
     math.abs(emaFast - emaSlow) / close * 100

emaCompressed = emaDistance <= emaDistancePct

avgVolume = ta.sma(volume, volumeLength)
volumeContracted = volume <= avgVolume * volumeFactor

compression = nrSignal and emaCompressed and volumeContracted

breakoutHigh = ta.highest(high[1], rangeLength)
breakout = compression[1] and close > breakoutHigh

plot(emaFast, "EMA 9", linewidth=2)
plot(emaSlow, "EMA 15", linewidth=2)

plotshape(
     compression,
     title="Tight Compression",
     style=shape.labeldown,
     location=location.abovebar,
     text="TIGHT",
     size=size.tiny
)

plotshape(
     breakout and barstate.isconfirmed,
     title="Compression Breakout",
     style=shape.labelup,
     location=location.belowbar,
     text="BREAKOUT",
     size=size.small
)

alertcondition(
     breakout and barstate.isconfirmed,
     title="Tight Range EMA Breakout",
     message="Rajan Tight Range + EMA Compression breakout."
)
```

------------------------------------------------------------------------

# Indicator 05 --- Rajan 15-Minute Stock Breakout

## Verified Chartink rule

The accessible public 15-minute breakout screeners use a 15-minute close
breaking above a prior 20-bar maximum and 15-minute volume above its
20-period SMA. One public variant additionally contains liquidity/trend
filters, so the core version below implements the directly identifiable
breakout + volume rule. citeturn1search6

## Rule

``` text
15m Close > previous 20-bar maximum close
AND
15m Volume > 20-bar SMA(volume)
```

### Pine Script

``` pine
//@version=6
indicator("Rajan - 15 Minute Stock Breakout", overlay=true, max_labels_count=500)

lookback = input.int(20, "Breakout Lookback")
volumeLength = input.int(20, "Volume SMA")
volumeMultiplier = input.float(1.0, "Volume Multiplier", step=0.1)

useEMA = input.bool(false, "Use EMA Trend Filter")
emaLength = input.int(50, "EMA Length")

previousHigh = ta.highest(close[1], lookback)
avgVolume = ta.sma(volume, volumeLength)

breakout = close > previousHigh
volumeConfirmed = volume > avgVolume * volumeMultiplier

ema = ta.ema(close, emaLength)
trendOK = not useEMA or close > ema

buySignal = breakout and volumeConfirmed and trendOK and barstate.isconfirmed

plot(useEMA ? ema : na, "Trend EMA", linewidth=2)
plot(previousHigh, "20-Bar Breakout Level", linewidth=2, style=plot.style_stepline)

plotshape(
     buySignal,
     title="15m Breakout",
     style=shape.labelup,
     location=location.belowbar,
     text="15M\nBREAKOUT",
     size=size.small
)

alertcondition(
     buySignal,
     title="15 Minute Stock Breakout",
     message="Rajan 15-minute breakout with volume confirmation."
)
```

**Recommended chart:** 15-minute.

------------------------------------------------------------------------

# Indicator 06 --- Rajan 15-Minute Breakdown

## Verified public variant

A current public Chartink 15-minute breakdown variant contains:

-   15-minute close below previous 20-bar minimum.
-   15-minute volume greater than 20-period SMA(volume).

Another public variant adds RSI, MACD and SMA50 conditions,
demonstrating that multiple similarly named scans exist.
citeturn1search14turn1search5

The Pine indicator therefore makes the extra filters optional.

### Pine Script

``` pine
//@version=6
indicator("Rajan - 15 Minute Breakdown", overlay=true, max_labels_count=500)

lookback = input.int(20, "Breakdown Lookback")
volumeLength = input.int(20, "Volume SMA")
volumeMultiplier = input.float(1.0, "Volume Multiplier", step=0.1)

useRSI = input.bool(false, "Use RSI Filter")
rsiLength = input.int(14, "RSI Length")
rsiMax = input.float(40, "Maximum RSI")

useMACD = input.bool(false, "Use MACD Filter")

useSMA50 = input.bool(false, "Use SMA50 Filter")

previousLow = ta.lowest(close[1], lookback)

avgVolume = ta.sma(volume, volumeLength)
volumeConfirmed = volume > avgVolume * volumeMultiplier

rsi = ta.rsi(close, rsiLength)
rsiOK = not useRSI or rsi <= rsiMax

[macdLine, signalLine, _] = ta.macd(close, 12, 26, 9)
macdOK = not useMACD or macdLine < signalLine

sma50 = ta.sma(close, 50)
smaOK = not useSMA50 or close < sma50

breakdown =
     close < previousLow and
     volumeConfirmed and
     rsiOK and
     macdOK and
     smaOK and
     barstate.isconfirmed

plot(previousLow, "20-Bar Breakdown Level", linewidth=2, style=plot.style_stepline)
plot(useSMA50 ? sma50 : na, "SMA 50", linewidth=1)

plotshape(
     breakdown,
     title="15m Breakdown",
     style=shape.labeldown,
     location=location.abovebar,
     text="15M\nBREAKDOWN",
     size=size.small
)

alertcondition(
     breakdown,
     title="15 Minute Breakdown",
     message="Rajan 15-minute breakdown detected."
)
```

------------------------------------------------------------------------

# Indicator 07 --- Rajan 15-Minute Volume Buzzer

## Purpose

The supplied screener is intended to identify unusually active 15-minute
volume.

Because the exact current formula of the supplied URL is not exposed,
the cleanest configurable implementation is:

``` text
Current 15m Volume > Previous 15m Volume × multiplier
```

plus optional EMA/trend confirmation.

### Pine Script

``` pine
//@version=6
indicator("Rajan - 15 Minute Volume Buzzer", overlay=true)

volumeMultiplier = input.float(1.5, "Volume Spike Multiplier", minval=1.0, step=0.1)

useEMA = input.bool(true, "Require Price Above EMA")
emaLength = input.int(5, "EMA Length")

useWeeklyTrend = input.bool(false, "Require Weekly Close Above Weekly EMA")
weeklyEmaLength = input.int(30, "Weekly EMA Length")

volumeSpike = volume > volume[1] * volumeMultiplier

ema = ta.ema(close, emaLength)
priceTrendOK = not useEMA or close > ema

weeklyClose = request.security(
     syminfo.tickerid,
     "W",
     close,
     lookahead=barmerge.lookahead_off
)

weeklyEma = request.security(
     syminfo.tickerid,
     "W",
     ta.ema(close, weeklyEmaLength),
     lookahead=barmerge.lookahead_off
)

weeklyOK = not useWeeklyTrend or weeklyClose > weeklyEma

signal = volumeSpike and priceTrendOK and weeklyOK and barstate.isconfirmed

plot(useEMA ? ema : na, "EMA", linewidth=2)

plotshape(
     signal,
     title="Volume Buzzer",
     style=shape.labelup,
     location=location.belowbar,
     text="VOLUME\nBUZZ",
     size=size.small
)

alertcondition(
     signal,
     title="15 Minute Volume Buzzer",
     message="Rajan 15-minute volume buzzer detected."
)
```

------------------------------------------------------------------------

# Indicator 08 --- Rajan Daily Volume Buzzer

## Verified Chartink rule

The supplied `volume-buzzer` page currently exposes:

``` text
Daily Volume > Daily SMA(Volume, 10)

AND

Daily Close > Previous Day Close × 1.02
```

This is a direct translation. citeturn2search2

### Pine Script

``` pine
//@version=6
indicator("Rajan - Daily Volume Buzzer", overlay=true, max_labels_count=500)

volumeLength = input.int(10, "Volume SMA Length")
priceMovePct = input.float(2.0, "Minimum Price Increase %", step=0.1)

avgVolume = ta.sma(volume, volumeLength)

volumeCondition = volume > avgVolume
priceCondition = close > close[1] * (1 + priceMovePct / 100)

signal = volumeCondition and priceCondition and barstate.isconfirmed

plotshape(
     signal,
     title="Daily Volume Buzzer",
     style=shape.labelup,
     location=location.belowbar,
     text="VOL\nBUZZ",
     size=size.small
)

alertcondition(
     signal,
     title="Daily Volume Buzzer",
     message="Rajan Daily Volume Buzzer signal."
)
```

------------------------------------------------------------------------

# Indicator 09 --- Rajan RSI Divergence

## Source

Supplied:

`rsi-divergence-28042798`

The exact current filter formula was not exposed sufficiently to claim a
one-to-one copy.

This indicator implements the standard price/RSI divergence concept
represented by the screener name.

## Bullish divergence

``` text
Price = Lower Low
RSI   = Higher Low
```

## Bearish divergence

``` text
Price = Higher High
RSI   = Lower High
```

### Pine Script

``` pine
//@version=6
indicator("Rajan - RSI Divergence", overlay=true, max_labels_count=500)

rsiLength = input.int(14, "RSI Length")
pivotLeft = input.int(5, "Pivot Left")
pivotRight = input.int(5, "Pivot Right")

rsi = ta.rsi(close, rsiLength)

priceLow = ta.pivotlow(low, pivotLeft, pivotRight)
priceHigh = ta.pivothigh(high, pivotLeft, pivotRight)

var float previousPriceLow = na
var float previousRsiLow = na
var float previousPriceHigh = na
var float previousRsiHigh = na

bullishDivergence = false
bearishDivergence = false

if not na(priceLow)
    currentPriceLow = priceLow
    currentRsiLow = rsi[pivotRight]

    bullishDivergence :=
         not na(previousPriceLow) and
         currentPriceLow < previousPriceLow and
         currentRsiLow > previousRsiLow

    previousPriceLow := currentPriceLow
    previousRsiLow := currentRsiLow

if not na(priceHigh)
    currentPriceHigh = priceHigh
    currentRsiHigh = rsi[pivotRight]

    bearishDivergence :=
         not na(previousPriceHigh) and
         currentPriceHigh > previousPriceHigh and
         currentRsiHigh < previousRsiHigh

    previousPriceHigh := currentPriceHigh
    previousRsiHigh := currentRsiHigh

plotshape(
     bullishDivergence,
     title="Bullish RSI Divergence",
     style=shape.labelup,
     location=location.belowbar,
     text="RSI\nBULL DIV",
     size=size.small
)

plotshape(
     bearishDivergence,
     title="Bearish RSI Divergence",
     style=shape.labeldown,
     location=location.abovebar,
     text="RSI\nBEAR DIV",
     size=size.small
)

alertcondition(
     bullishDivergence,
     title="Bullish RSI Divergence",
     message="Rajan bullish RSI divergence detected."
)

alertcondition(
     bearishDivergence,
     title="Bearish RSI Divergence",
     message="Rajan bearish RSI divergence detected."
)
```

------------------------------------------------------------------------

# Indicator 10 --- Rajan NR-7 Breakout Setup

## Concept

NR-7 means the current candle has the narrowest high-low range over the
last seven bars. NR-7 is a recognised narrow-range setup and can be used
as a compression/breakout trigger. citeturn2search4

### Pine Script

``` pine
//@version=6
indicator("Rajan - NR7 Breakout Setup", overlay=true, max_labels_count=500)

nrLength = input.int(7, "NR Length", minval=2)
useVolume = input.bool(true, "Use Volume Confirmation")
volumeLength = input.int(20, "Volume SMA")
volumeMultiplier = input.float(1.0, "Volume Multiplier", step=0.1)

range = high - low
lowestRange = ta.lowest(range, nrLength)

nr7 = range <= lowestRange

nrHigh = ta.valuewhen(nr7, high, 0)
nrLow = ta.valuewhen(nr7, low, 0)

avgVolume = ta.sma(volume, volumeLength)
volumeOK = not useVolume or volume > avgVolume * volumeMultiplier

longBreakout =
     not na(nrHigh) and
     close > nrHigh and
     volumeOK and
     barstate.isconfirmed

shortBreakdown =
     not na(nrLow) and
     close < nrLow and
     volumeOK and
     barstate.isconfirmed

plotshape(
     nr7,
     title="NR7",
     style=shape.labeldown,
     location=location.abovebar,
     text="NR7",
     size=size.tiny
)

plotshape(
     longBreakout,
     title="NR7 Long Breakout",
     style=shape.labelup,
     location=location.belowbar,
     text="NR7\nBUY",
     size=size.small
)

plotshape(
     shortBreakdown,
     title="NR7 Breakdown",
     style=shape.labeldown,
     location=location.abovebar,
     text="NR7\nSELL",
     size=size.small
)

alertcondition(
     longBreakout,
     title="NR7 Long Breakout",
     message="Rajan NR7 bullish breakout."
)

alertcondition(
     shortBreakdown,
     title="NR7 Breakdown",
     message="Rajan NR7 bearish breakdown."
)
```

------------------------------------------------------------------------

# Indicator 11 --- Rajan Potential Breakout --- 200D High + 30D Consolidation

## Verified Chartink rule

The supplied `potential-breakouts` screener is described as stocks
nearing the 200-day high by 5%, consolidating over roughly 30 days, and
having volume above the 50-day average. The public rule also includes a
minimum closing-price filter in one current variant.
citeturn1search7turn1search9

## Core conditions

``` text
Close × 1.05 > 200-day High

30-day High <= 30-days-ago 200-day High

Volume > 50-day SMA(volume)
```

### Pine Script

``` pine
//@version=6
indicator("Rajan - Potential Breakout 200D High + 30D Consolidation", overlay=true)

nearHighPct = input.float(5.0, "Maximum Distance From 200D High %", step=0.5)
consolidationLength = input.int(30, "Consolidation Length")
volumeLength = input.int(50, "Volume SMA")
minimumClose = input.float(0.0, "Minimum Close", minval=0)

high200 = ta.highest(high, 200)

near200High =
     close >= high200 * (1 - nearHighPct / 100)

consolidationHigh = ta.highest(high, consolidationLength)
oldHigh200 = ta.highest(high[consolidationLength], 200)

consolidating =
     consolidationHigh <= oldHigh200

avgVolume = ta.sma(volume, volumeLength)
volumeConfirmed = volume > avgVolume

priceFilter = close > minimumClose

candidate =
     near200High and
     consolidating and
     volumeConfirmed and
     priceFilter and
     barstate.isconfirmed

plot(high200, "200D High", linewidth=2)

plotshape(
     candidate,
     title="Potential Breakout Candidate",
     style=shape.labelup,
     location=location.belowbar,
     text="POTENTIAL\nBREAKOUT",
     size=size.small
)

alertcondition(
     candidate,
     title="Potential Breakout Candidate",
     message="Rajan potential breakout candidate detected."
)
```

------------------------------------------------------------------------

# Indicator 12 --- Rajan Darvas + Supertrend Momentum

## Supplied source

`darvas-box-perfect`

The exact supplied page is not exposed clearly enough to reproduce the
original Darvas formula exactly.

A public copied scan associated with the same title uses:

-   Monthly low \>= monthly Supertrend
-   Weekly low \>= weekly Supertrend
-   Daily high \<= daily Supertrend
-   Daily RSI \> 40
-   Daily volume greater than previous day
-   Daily volume greater than two days ago

That public copy is therefore better treated as a **Darvas/Supertrend
momentum filter**, not a pure textbook Darvas Box. citeturn2search1

### Pine Script

``` pine
//@version=6
indicator("Rajan - Darvas Supertrend Momentum", overlay=true)

stAtr = input.int(7, "Supertrend ATR Length")
stFactor = input.float(3.0, "Supertrend Factor", step=0.1)

rsiLength = input.int(14, "RSI Length")
rsiMinimum = input.float(40, "Minimum RSI")

useVolume = input.bool(true, "Require Increasing Volume")

[st, direction] = ta.supertrend(stFactor, stAtr)

rsi = ta.rsi(close, rsiLength)

volumeOK =
     not useVolume or
     (volume > volume[1] and volume > volume[2])

dailyFilter =
     low >= st and
     rsi > rsiMinimum and
     volumeOK

weeklyLow = request.security(
     syminfo.tickerid,
     "W",
     low,
     lookahead=barmerge.lookahead_off
)

weeklyST = request.security(
     syminfo.tickerid,
     "W",
     ta.supertrend(stFactor, stAtr)[0],
     lookahead=barmerge.lookahead_off
)

monthlyLow = request.security(
     syminfo.tickerid,
     "M",
     low,
     lookahead=barmerge.lookahead_off
)

monthlyST = request.security(
     syminfo.tickerid,
     "M",
     ta.supertrend(stFactor, stAtr)[0],
     lookahead=barmerge.lookahead_off
)

higherTimeframeOK =
     weeklyLow >= weeklyST and
     monthlyLow >= monthlyST

signal =
     dailyFilter and
     higherTimeframeOK and
     barstate.isconfirmed

plot(st, "Daily Supertrend", linewidth=2)

plotshape(
     signal,
     title="Darvas Supertrend Momentum",
     style=shape.labelup,
     location=location.belowbar,
     text="DARVAS\nMOMENTUM",
     size=size.small
)

alertcondition(
     signal,
     title="Darvas Supertrend Momentum",
     message="Rajan Darvas/Supertrend momentum setup detected."
)
```

------------------------------------------------------------------------

# Indicator 13 --- Rajan Bottom Reversal Confluence

## Directly from the supplied chat

The user's bottom-sign rules were:

1.  Low-volume big red candle.
2.  Previous big-volume red candle rejected next day with approximately
    1.5× minimum volume and sustainability for 1--2 days.
3.  Long-term support at a previous long-term monthly breakout candle.
4.  Selling-climax contraction: tight candles with shrinking volume for
    3--5 days.
5.  Breadth divergence.
6.  Failed breakdown: price dips below support and closes back above it.

This indicator implements the price/volume parts that are available from
the chart itself. Breadth divergence is kept optional because it
requires a separate breadth data series.

### Pine Script

``` pine
//@version=6
indicator("Rajan - Bottom Reversal Confluence", overlay=true, max_labels_count=500)

volumeLength = input.int(20, "Volume Average")
bigVolumeMultiplier = input.float(1.5, "Big Volume Multiplier", step=0.1)
lowVolumeMultiplier = input.float(0.7, "Low Volume Multiplier", step=0.05)

supportLength = input.int(50, "Support Lookback")
supportTolerance = input.float(1.0, "Support Distance %", step=0.1)

contractionBars = input.int(4, "Contraction Bars", minval=3, maxval=5)

avgVolume = ta.sma(volume, volumeLength)
avgRange = ta.sma(high - low, volumeLength)

redCandle = close < open

bigRed =
     redCandle and
     (high - low) > avgRange * 1.5

lowVolumeRed =
     bigRed and
     volume < avgVolume * lowVolumeMultiplier

previousSellingClimax =
     redCandle[1] and
     (high[1] - low[1]) > avgRange[1] * 1.5 and
     volume[1] >= avgVolume[1] * bigVolumeMultiplier

rejection =
     previousSellingClimax and
     close > open and
     close > (high[1] + low[1]) / 2 and
     volume >= avgVolume * bigVolumeMultiplier

support = ta.lowest(low[1], supportLength)

nearSupport =
     math.abs(close - support) / close * 100 <= supportTolerance

tightRange = (high - low) < avgRange
shrinkingVolume = volume < avgVolume

contraction =
     ta.sum(tightRange ? 1 : 0, contractionBars) >= contractionBars - 1 and
     ta.sum(shrinkingVolume ? 1 : 0, contractionBars) >= contractionBars - 1

failedBreakdown =
     low < support and
     close > support and
     close > open

score = 0
score += lowVolumeRed ? 1 : 0
score += rejection ? 1 : 0
score += contraction ? 1 : 0
score += failedBreakdown ? 1 : 0
score += nearSupport ? 1 : 0

bottomSignal =
     score >= 3 and
     barstate.isconfirmed

plot(support, "Long-Term Support", linewidth=2, style=plot.style_stepline)

plotshape(
     lowVolumeRed,
     title="Low Volume Red",
     style=shape.circle,
     location=location.belowbar,
     text="LVR",
     size=size.tiny
)

plotshape(
     rejection,
     title="Selling Climax Rejection",
     style=shape.labelup,
     location=location.belowbar,
     text="REJECT",
     size=size.tiny
)

plotshape(
     contraction,
     title="Contraction",
     style=shape.labelup,
     location=location.belowbar,
     text="CONTRACT",
     size=size.tiny
)

plotshape(
     failedBreakdown,
     title="Failed Breakdown",
     style=shape.labelup,
     location=location.belowbar,
     text="FAIL BD",
     size=size.tiny
)

plotshape(
     bottomSignal,
     title="Bottom Confluence",
     style=shape.labelup,
     location=location.belowbar,
     text="BOTTOM\n" + str.tostring(score) + "/5",
     size=size.small
)

alertcondition(
     bottomSignal,
     title="Bottom Reversal Confluence",
     message="Rajan Bottom Reversal Confluence detected."
)
```

------------------------------------------------------------------------

# Indicator 14 --- Rajan India VIX Next-Day Indicative Range

## Chat formula

The supplied formula was:

``` text
Upper = NIFTY + NIFTY × (VIX / 16)
Lower = NIFTY - NIFTY × (VIX / 16)
```

When VIX is displayed as a number such as `27.88`, the equivalent
calculation is:

``` text
Upper = NIFTY + NIFTY × VIX / 1600
Lower = NIFTY - NIFTY × VIX / 1600
```

This is an indicative volatility range, not a prediction or guaranteed
trading range.

### Pine Script

``` pine
//@version=6
indicator("Rajan - India VIX Next-Day NIFTY Range", overlay=false)

vixSymbol = input.symbol("NSE:INDIAVIX", "India VIX Symbol")
niftySymbol = input.symbol("NSE:NIFTY", "NIFTY Symbol")

vixDivisor = input.float(1600.0, "VIX Divisor", step=100)

nifty = request.security(
     niftySymbol,
     "D",
     close,
     lookahead=barmerge.lookahead_off
)

vix = request.security(
     vixSymbol,
     "D",
     close,
     lookahead=barmerge.lookahead_off
)

expectedMove = nifty * vix / vixDivisor

upperRange = nifty + expectedMove
lowerRange = nifty - expectedMove

plot(upperRange, "Indicative Upper Range", linewidth=2)
plot(lowerRange, "Indicative Lower Range", linewidth=2)
plot(nifty, "NIFTY Reference", linewidth=1)

plot(vix, "India VIX", display=display.data_window)
plot(expectedMove, "Indicative Expected Move", display=display.data_window)
```

------------------------------------------------------------------------

# Indicator 15 --- Rajan 9/15 + Hammer + W Confluence

This is the **main entry indicator** derived from the user's chat rather
than a copy of one Chartink scanner.

## Long setup

``` text
Uptrend
AND
EMA 9 > EMA 15
AND
Price near support
AND
(
    Hammer
    OR
    W Pattern breakout
)
AND
optional volume confirmation
```

### Pine Script

``` pine
//@version=6
indicator("Rajan - 9/15 + Hammer + W Confluence", overlay=true, max_labels_count=500)

ema9 = ta.ema(close, 9)
ema15 = ta.ema(close, 15)

supportLookback = input.int(20, "Support Lookback")
supportTolerance = input.float(1.0, "Support Tolerance %", step=0.1)

volumeLength = input.int(20, "Volume SMA")
useVolume = input.bool(true, "Require Volume Confirmation")
volumeMultiplier = input.float(1.0, "Volume Multiplier", step=0.1)

pivotLeft = input.int(3, "Pivot Left")
pivotRight = input.int(3, "Pivot Right")

support = ta.lowest(low[1], supportLookback)
nearSupport = math.abs(close - support) / close * 100 <= supportTolerance

trend =
     close > ema9 and
     ema9 > ema15 and
     ema9 > ema9[1] and
     ema15 > ema15[1]

body = math.abs(close - open)
range = high - low
upperWick = high - math.max(open, close)
lowerWick = math.min(open, close) - low

hammer =
     range > 0 and
     body > syminfo.mintick and
     body / range <= 0.35 and
     lowerWick / body >= 2.0 and
     upperWick / body <= 0.5

ph = ta.pivothigh(high, pivotLeft, pivotRight)
pl = ta.pivotlow(low, pivotLeft, pivotRight)

var float firstLow = na
var float secondLow = na
var float neckline = na

if not na(pl)
    firstLow := secondLow
    secondLow := pl

if not na(ph)
    neckline := ph

similarLows =
     not na(firstLow) and
     not na(secondLow) and
     math.abs(firstLow - secondLow) / firstLow * 100 <= supportTolerance

wBreakout =
     similarLows and
     not na(neckline) and
     close > neckline

avgVolume = ta.sma(volume, volumeLength)
volumeOK = not useVolume or volume > avgVolume * volumeMultiplier

hammerSetup = trend and nearSupport and hammer
wSetup = trend and wBreakout

longSignal =
     trend and
     nearSupport and
     (hammerSetup or wSetup) and
     volumeOK and
     barstate.isconfirmed

plot(ema9, "EMA 9", linewidth=2)
plot(ema15, "EMA 15", linewidth=2)
plot(support, "Support", linewidth=2, style=plot.style_stepline)

plotshape(
     hammerSetup and barstate.isconfirmed,
     title="Hammer Setup",
     style=shape.labelup,
     location=location.belowbar,
     text="HAMMER",
     size=size.tiny
)

plotshape(
     wSetup and barstate.isconfirmed,
     title="W Setup",
     style=shape.labelup,
     location=location.belowbar,
     text="W",
     size=size.tiny
)

plotshape(
     longSignal,
     title="Rajan Long Confluence",
     style=shape.labelup,
     location=location.belowbar,
     text="RAJAN\nLONG",
     size=size.small
)

alertcondition(
     longSignal,
     title="Rajan Long Confluence",
     message="Rajan 9/15 + Hammer/W confluence detected."
)
```

------------------------------------------------------------------------

# Chartink Link Status

  ------------------------------------------------------------------------------------
  Supplied Link                        Indicator / Screener    Pine treatment
                                       Name                    
  ------------------------------------ ----------------------- -----------------------
  `my-favourite-pattern-tight-range`   My Favourite Pattern    **Translated concept**
                                       Tight Range with EMA    --- Tight Range + EMA
                                                               Compression

  `9-15-ema-strategy-intraday`         9 & 15 EMA Strategy     **Translated** --- 9/15
                                       Intraday                EMA

  `waiting-19`                         EMA Set-up              **Not claimed as
                                                               exact** --- formula not
                                                               exposed

  `stoxup-dinesh`                      StoxUp Dinesh           **Not claimed as
                                                               exact** --- formula not
                                                               exposed

  `9-15-ema-strategy-9`                9 & 15 EMA Strategy     **Translated** --- 9/15
                                                               EMA

  `copy-ankur-s-volume-scan-612`       Trader Dinesh Volume    **Not claimed as
                                       Scan                    exact** --- formula not
                                                               exposed

  `rsi-divergence-28042798`            RSI Divergence          **Concept translated**

  `stocks-below-book-value`            Stocks Below Book Value **Not converted to
                                                               price indicator** ---
                                                               fundamental data

  `daily`                              Daily                   **No exact rule
                                                               exposed**

  `volum`                              Volume                  **Covered by volume
                                                               indicators**

  `all-t`                              All-T                   **No exact rule
                                                               exposed**

  `15-minute-stock-breakouts`          15 Minute Stock         **Translated core
                                       Breakouts               breakout + volume**

  `15-min-breakdown`                   15 Min Breakdown        **Translated with
                                                               optional
                                                               RSI/MACD/SMA50**

  `15-min-volume-buzzer-1`             15 Min Volume Buzzer    **Configurable volume
                                                               buzzer**

  `potential-breakouts`                Potential Breakouts     **Translated 200D
                                                               high + 30D
                                                               consolidation +
                                                               volume**

  `volume-buzzer`                      Volume Buzzer           **Direct translation of
                                                               current public rule**

  `nr-7-14`                            NR 7                    **NR7 implementation**

  `darvas-box-perfect`                 Darvas Box Perfect      **Darvas/Supertrend
                                                               momentum
                                                               interpretation**

  `9-15-ema-strategy-intraday-setup`   9 & 15 EMA Intraday     **9/15 EMA core
                                       Setup FNO               implementation**
  ------------------------------------------------------------------------------------

------------------------------------------------------------------------

# How to use the indicators

## Intraday NIFTY / BANKNIFTY

Recommended starting charts:

-   5-minute
-   15-minute

Use:

1.  `Rajan - 9/15 EMA Intraday Setup`
2.  `Rajan - 15 Minute Stock Breakout`
3.  `Rajan - 15 Minute Volume Buzzer`
4.  `Rajan - 9/15 + Hammer + W Confluence`

------------------------------------------------------------------------

## Swing stocks

Use:

1.  `Rajan - Potential Breakout 200D High + 30D Consolidation`
2.  `Rajan - Tight Range + EMA Compression`
3.  `Rajan - NR7 Breakout Setup`
4.  `Rajan - RSI Divergence`
5.  `Rajan - Darvas Supertrend Momentum`

------------------------------------------------------------------------

## Bottom / reversal hunting

Use:

1.  `Rajan - Bottom Reversal Confluence`
2.  `Rajan - Uptrend Hammer Support Entry`
3.  `Rajan - W Pattern Support Entry`
4.  `Rajan - RSI Divergence`
5.  `Rajan - NR7 Breakout Setup`

------------------------------------------------------------------------

# Suggested TradingView alerts

Create alerts for:

### Entry

-   `Rajan Long Confluence`
-   `Rajan Hammer Support Entry`
-   `Rajan W Pattern Breakout`
-   `9/15 EMA BUY`
-   `15 Minute Stock Breakout`

### Reversal

-   `Bottom Reversal Confluence`
-   `Bullish RSI Divergence`
-   `Failed Breakdown` / bottom confluence

### Momentum

-   `Daily Volume Buzzer`
-   `15 Minute Volume Buzzer`
-   `Potential Breakout Candidate`

------------------------------------------------------------------------

# Repainting / confirmation

The scripts use confirmed-bar logic for trading signals where
appropriate.

For multi-timeframe calculations, Pine's `request.security()` should
use:

``` pine
lookahead=barmerge.lookahead_off
```

Do not judge an intraday signal while its current candle is still
forming if you want a non-flickering alert.

Chartink itself warns that some multi-timeframe backtests can repaint
because higher-timeframe bars overlap lower-timeframe bars. The same
general caution applies when reproducing multi-timeframe logic in Pine.

------------------------------------------------------------------------

# What is NOT included as an exact copy

I deliberately did not invent exact formulas for:

-   Waiting-19
-   StoxUp Dinesh
-   Trader Dinesh Volume Scan
-   All-T
-   Daily
-   Some versions of the RSI Divergence scanner
-   The exact original Darvas Box Perfect implementation

The reason is that the current public page for those particular URLs
does not expose enough of the filter definition to establish the exact
original formula.

If the user provides screenshots of the Chartink **filter conditions**
for those screeners, those can be converted line-by-line into Pine.

------------------------------------------------------------------------

# Recommended final master indicator

Once each individual indicator is validated, combine them into:

## `Rajan Trading System — Master Confluence`

Suggested dashboard:

``` text
RAJAN TRADING SYSTEM
────────────────────────────
Trend             BULLISH
EMA 9 / 15        BULLISH
Support            NEAR
Hammer             YES
W Pattern          YES
Volume             CONFIRMED
15m Breakout       YES
RSI Divergence     YES
NR7                YES
VIX                14.2
────────────────────────────
SETUP              LONG
```

The dashboard should show the conditions individually rather than
converting them into a claimed "accuracy %" or guaranteed probability.

------------------------------------------------------------------------

# Validation checklist

Before using any script with real money:

-   Test NIFTY.
-   Test BANKNIFTY.
-   Test liquid NSE stocks.
-   Test 5-minute and 15-minute charts.
-   Test trending markets.
-   Test sideways markets.
-   Test high-VIX sessions.
-   Test low-VIX sessions.
-   Check gap-up sessions.
-   Check gap-down sessions.
-   Check alert timing.
-   Check historical false signals.
-   Paper trade before live use.

**These indicators are technical-analysis tools, not guarantees of
future price movement or profitability.**
