---
name: quantitative-analysis-methodology
description: >
  Comprehensive methodology guidance for quantitative financial analysis. MUST be triggered
  BEFORE: (1) risk calculations (ES, VaR, volatility), (2) forecasting (exponential smoothing,
  moving averages), (3) currency conversion, (4) federal budget classification. Enforces
  MANDATORY validation checkpoints with PASS/FAIL output before computation. Prevents
  systematic errors from wrong data transformations, date misalignment, notation parsing,
  or classification mistakes.
---

# Quantitative Analysis Methodology Guide

**CRITICAL: Verify methodology BEFORE computation. Wrong methodology = wrong answer regardless of correct data extraction.**

This guide consolidates:
- Risk metric calculations (ES, VaR, volatility)
- Time series forecasting (exponential smoothing, moving averages)
- Currency conversion and date alignment
- Federal budget classification
- **Mandatory validation checkpoints**

---

## Part 1: Pre-Computation Validation Protocol

**This section enforces validation—rules exist below, but you must PROVE compliance before computing.**

### Mandatory Validation Output Format

**ALWAYS output this block before ANY multi-step financial calculation:**

```
VALIDATION CHECKPOINT
Task: [task type]
Check 1: [description]
  - Expected: [value]
  - Found: [value]
  - Status: [PASS/FAIL]
Check 2: [description]
  - Expected: [value]
  - Found: [value]
  - Status: [PASS/FAIL]
OVERALL: [PASS - proceed / FAIL - halt and resolve]
```

### Blocking Behavior

**When validation FAILS:**

1. Output: `VALIDATION FAILED: [specific reason]`
2. Output: `REQUIRED ACTION: [what must be obtained/corrected]`
3. **STOP** - Do not proceed with calculation
4. Attempt to resolve (find correct data, correct transformation)
5. Re-run validation checkpoint
6. Only proceed when all checks PASS

---

## Part 2: Risk Metric Methodology

### Pre-Flight Checklist

Before ANY quantitative financial analysis:

1. **Identify the metric type** - Determines required data form
2. **Check data form** - Is it levels or returns? Prices or yields?
3. **Apply required transformation** - Convert if needed
4. **Validate output sign/magnitude** - Sanity check results

### Expected Shortfall (ES / CVaR)

**CRITICAL: ES is calculated on RETURNS, not raw values.**

| Data Form | Required Action | Example |
|-----------|-----------------|---------|
| Yield levels (9.56%, 8.36%, ...) | Compute returns FIRST | r_t = (Y_t - Y_{t-1}) / Y_{t-1} |
| Price levels ($100, $98, ...) | Compute returns FIRST | r_t = (P_t - P_{t-1}) / P_{t-1} |
| Return series (-2.5%, 1.2%, ...) | Use directly | No transformation |

**Formula:**
```
ES_alpha = E[Loss | Loss > VaR_alpha]
```

At alpha = 5%, ES is the average of the worst 5% of returns.

**Correct workflow for yield data:**
1. Extract yield levels: [9.56%, 9.60%, 8.36%, 7.37%, 7.68%, 6.69%, 5.87%, 6.04%, 5.65%, 6.14%]
2. Compute period-over-period returns: [(9.60-9.56)/9.56, (8.36-9.60)/9.60, ...]
3. Sort returns, take worst alpha percentile
4. Average those worst returns - ES

**Common error:** Taking min/max of raw levels. This is NOT ES.

**Output validation:**
- ES representing losses should be negative (e.g., -18.51%)
- Magnitude should reflect plausible return movements
- If ES equals min(raw_values), methodology was wrong

### Value at Risk (VaR)

Same transformation rules as ES. VaR is the threshold loss at confidence level alpha.

```
VaR_alpha = quantile(returns, alpha)
```

At 95% confidence, VaR is the 5th percentile of returns.

### Risk Calculation Validation Checkpoint

**Before ES, VaR, or volatility calculations:**

```
VALIDATION CHECKPOINT - Risk Calculation
Check 1: Data Form
  - Required form: returns
  - Current form: [levels/returns]
  - Status: [PASS if returns / FAIL if levels]
Check 2: Return Calculation (if transformed)
  - Formula used: [e.g., (V_t - V_{t-1}) / V_{t-1}]
  - Sample calculation: [show one example]
  - Status: [PASS if verified / FAIL if not shown]
Check 3: Output Sign Convention
  - Loss representation: negative returns
  - Status: [PASS if convention documented]
OVERALL: [PASS/FAIL]
```

---

## Part 3: Forecasting Methodology

### Bond Price Notation Parsing

**CRITICAL: Treasury bond prices are quoted in 32nds, not decimals.**

| Notation | Meaning | Decimal Value |
|----------|---------|---------------|
| 76.18 | 76 + 18/32 | 76.5625 |
| 99.16 | 99 + 16/32 | 99.5000 |
| 100.08 | 100 + 8/32 | 100.2500 |
| 98.24+ | 98 + 24.5/32 | 98.765625 |

**Conversion formula:**
```
Decimal Price = Integer Part + (Fractional Part / 32)
```

**The "+" suffix:**
- 98.24+ means 98 + 24.5/32 (adds 0.5 to the numerator)
- Equivalent to adding 1/64 to the base price

**Validation checks:**
- Fractional part must be 00-31 (values >=32 are invalid)
- Treasury note prices typically range 90-110
- Treasury bond prices can range more widely

**Common error:** Treating 76.18 as 76.18 decimal instead of 76 + 18/32 = 76.5625.

### Exponential Smoothing

**Formula:**
```
F_{t+1} = alpha * Y_t + (1-alpha) * F_t
```

Where:
- F_{t+1} = Forecast for period t+1 (made at end of period t)
- Y_t = Actual value observed in period t
- F_t = Forecast that was made for period t
- alpha = Smoothing parameter (0 < alpha <= 1)

**Initialization Methods:**

| Method | When to Use | Formula |
|--------|-------------|---------|
| First observation | Short series (<20 obs), simple | F_1 = Y_1 |
| Average of first k | Longer series, more stable | F_1 = mean(Y_1...Y_k) |
| Backcast | Optimal but complex | Requires iterative fitting |

**Default:** Use first observation method (F_1 = Y_1) unless otherwise specified.

**Forecast Timing Convention:**

**CRITICAL: A forecast for period t is made at the END of period t-1.**

### Forecast Error Conventions

**CRITICAL: Error = Actual - Forecast (NOT Forecast - Actual)**

```
e_t = Y_t - F_t
```

| Error Sign | Interpretation |
|------------|----------------|
| Positive (+) | Under-forecast (actual exceeded forecast) |
| Negative (-) | Over-forecast (actual was below forecast) |

**Example:**
- Actual (Y_t) = 190.73
- Forecast (F_t) = 210.02
- Error = 190.73 - 210.02 = **-19.29** (over-forecast)

**WRONG:** e_t = F_t - Y_t (reverses sign interpretation)

### Forecasting Validation Checkpoint

**Before exponential smoothing or time-series forecasts:**

```
VALIDATION CHECKPOINT - Forecasting
Check 1: Notation Parsing
  - Raw value: [as appears in source]
  - Parsed value: [decimal equivalent]
  - Parsing method: [e.g., "32nds: 76 + 18/32 = 76.5625"]
  - Status: [PASS if shown / FAIL if assumed]
Check 2: Initialization Method
  - Method: [e.g., "F_1 = Y_1 (first observation)"]
  - Initial value: [numeric]
  - Status: [PASS if explicit]
Check 3: Error Convention
  - Formula: Error = Actual - Forecast
  - Status: [PASS if using standard convention]
OVERALL: [PASS/FAIL]
```

---

## Part 4: Currency Conversion

### Date Alignment Rule

**CRITICAL: Use the exchange rate from the SAME DATE as the price observation.**

| Price Date | Exchange Rate Date | Correct? |
|------------|-------------------|----------|
| End of March | End of March | Yes |
| End of March | March 1 | No |
| End of March | Beginning of April | No |

**End-of-Month Convention:**

For end-of-month price data:
- Use end-of-month exchange rates
- "End of month" typically means last business day
- Not "first of next month" or "average for month"

### Exchange Rate Direction

**Verify quote convention before applying:**

| Convention | Example | To convert USD to DEM |
|------------|---------|---------------------|
| DEM per USD | 1.85 DEM/USD | Multiply: USD * 1.85 |
| USD per DEM | 0.54 USD/DEM | Divide: USD / 0.54 |

### Currency Conversion Validation Checkpoint

**Before EACH conversion, validate:**

```
VALIDATION CHECKPOINT - Currency Conversion
Check 1: Date Alignment
  - Price observation date: [exact date from source]
  - Exchange rate date: [exact date from rate source]
  - Status: [PASS if identical / FAIL if different]
Check 2: Rate Direction
  - Quote convention: [e.g., "DEM per USD" or "USD per DEM"]
  - Operation to apply: [multiply/divide]
  - Status: [PASS if verified / FAIL if uncertain]
Check 3: Source Documentation
  - Price source: [document/table/cell reference]
  - Rate source: [document/API/reference]
  - Status: [PASS if documented / FAIL if assumed]
OVERALL: [PASS/FAIL]
```

**CRITICAL Date Alignment Rules:**
- "End of March" prices require "end of March" exchange rates
- "March 1" != "end of March" -> FAIL
- "April 1" != "end of March" -> FAIL
- Treasury Bulletin April edition contains END OF MARCH data

---

## Part 5: Government Accounting Classifications

**CRITICAL: Use OMB/Treasury definitions, not intuitive interpretation.**

For federal obligation classifications, see `references/federal-accounting.md`.

Key principle: "Service-related" in federal accounting has specific regulatory meaning per OMB Circular A-11 that differs from casual interpretation.

---

## Part 6: Data Transformation Rules

### When to Compute Returns

| Analysis Type | Requires Returns? | Why |
|---------------|-------------------|-----|
| ES / CVaR | YES | Risk metrics measure change, not level |
| VaR | YES | Same as ES |
| Volatility / Std Dev | Usually YES | Volatility of returns, not levels |
| Performance analysis | YES | Compare % gains/losses |
| Trend analysis | NO | Levels show trend direction |
| Point-in-time snapshot | NO | Current state, not change |

### Return Calculation Methods

**Simple returns** (default for most financial analysis):
```
r_t = (V_t - V_{t-1}) / V_{t-1}
```

**Log returns** (for compounding analysis):
```
r_t = ln(V_t / V_{t-1})
```

Use simple returns unless log returns are specifically required.

---

## Part 7: Multi-Source Data Combination

**Before combining time series from different sources:**

```
VALIDATION CHECKPOINT - Data Combination
Check 1: Frequency Match
  - Source A frequency: [monthly/quarterly/etc.]
  - Source B frequency: [monthly/quarterly/etc.]
  - Status: [PASS if identical / FAIL if different]
Check 2: Date Convention Match
  - Source A dates: [e.g., "end of month"]
  - Source B dates: [e.g., "end of month"]
  - Status: [PASS if identical / FAIL if different]
Check 3: Period Alignment
  - Sample period: [e.g., "March 1972"]
  - Source A date: [exact date]
  - Source B date: [exact date]
  - Status: [PASS if aligned / FAIL if misaligned]
OVERALL: [PASS/FAIL]
```

---

## Part 8: Validation Checks Summary

Before reporting any result, verify:

| Metric | Expected Characteristics | Red Flag |
|--------|-------------------------|----------|
| ES on returns | Negative value (for loss measurement) | Positive or equals raw data min |
| VaR on returns | Negative value at alpha < 50% | Positive or equals raw percentile of levels |
| Parsed 32nds price | Close to quoted integer | >1 point difference |
| Exponential smooth | Between min and max of data | Outside data range |
| Forecast error sign | Negative if over-forecast | Sign seems reversed |
| Currency conversion | Same order of magnitude | 10x or 0.1x original |
| Date alignment | Exact date match | Off by days |
| Percentage of total | Between 0% and 100% | Outside range or sum != 100% |
| Classification ratio | Matches expected category scope | Drastically different from reasonable range |

---

## Quick Decision Tree

```
Starting a financial analysis task?
|
+-- Calculating ES, VaR, or volatility?
|   +-- Is data already in return form?
|       +-- YES -> Proceed with calculation
|       +-- NO -> Compute returns first, then calculate
|
+-- Doing forecasting?
|   +-- Is price data in 32nds notation?
|   |   +-- YES -> Parse: Integer + Fractional/32
|   |   +-- NO -> Use as-is (verify it's decimal)
|   +-- Using exponential smoothing?
|   |   +-- Initialize: F_1 = Y_1 (first observation)
|   +-- Computing error?
|       +-- Error = Actual - Forecast (signed)
|
+-- Converting currencies?
|   +-- Match exchange rate date to price date exactly
|   +-- Verify rate direction (per USD or per foreign)
|   +-- Validate converted magnitude is reasonable
|
+-- Classification task?
    +-- Check references/federal-accounting.md for definitions
```
