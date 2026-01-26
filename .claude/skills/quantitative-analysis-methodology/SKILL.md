---
name: quantitative-analysis-methodology
description: >
  Comprehensive methodology guidance for quantitative financial analysis. MUST be triggered
  BEFORE: (1) risk calculations (ES, VaR, volatility), (2) forecasting (exponential smoothing,
  moving averages), (3) currency conversion, (4) federal budget classification, (5) statistical
  inference (Z-scores, hypothesis tests, standard deviation calculations). Enforces
  MANDATORY validation checkpoints with PASS/FAIL output before computation. Prevents
  systematic errors from wrong data transformations, date misalignment, notation parsing,
  classification mistakes, or sample vs population statistics confusion.
---

# Quantitative Analysis Methodology Guide

---

## ⚠️ MANDATORY FIRST OUTPUT — READ THIS BEFORE ANYTHING ELSE

**You MUST output a validation block as your VERY FIRST action, BEFORE extracting any data or performing any calculation.**

This is not optional. Skipping this step WILL result in wrong answers.

### Required First Output Format

**Immediately upon starting ANY quantitative task, output this block:**

```
═══════════════════════════════════════════════════════════
METHODOLOGY VERIFICATION - [Task Type: ES/VaR/Forecasting/Currency]
═══════════════════════════════════════════════════════════

Check 1 - Data Form (for ES/VaR tasks):
  Data form: Returns required.
  Will compute returns from levels before calculation: [YES/NO]
  Status: [PASS if YES / BLOCKED if NO]

Check 2 - Date Alignment (for currency conversion tasks):
  Price date: [exact date from source]
  Exchange rate date: [exact date from rate source]
  Match: [PASS if identical / BLOCKED if different]

VERIFICATION RESULT: [PROCEED / BLOCKED - must resolve before continuing]
═══════════════════════════════════════════════════════════
```

**You MUST output this validation block before any calculation. Skipping this step will result in wrong answers.**

---

## ⚠️ BLOCKING CONDITIONS — DO NOT PROCEED IF THESE APPLY

### BLOCKED: ES/VaR on Levels

**If you have yield/price LEVELS and will calculate ES/VaR directly on those levels, STOP.**

You MUST compute returns first. ES on levels is ALWAYS WRONG.

- ❌ WRONG: Extract yields [9.56%, 8.36%, 7.37%, 6.14%], sort them, return min (6.14%) as ES
- ✓ CORRECT: Extract yields, compute returns between periods, then calculate ES on returns

### BLOCKED: Date Misalignment

**If price date is "end of March" and exchange rate date is "March 1", STOP.**

These are NOT the same date. Find end-of-March exchange rates or document why they're unavailable.

- ❌ WRONG: Use March 1 exchange rate for end-of-March Treasury price
- ✓ CORRECT: Use end-of-March exchange rate for end-of-March Treasury price

### BLOCKED: Incomplete Multi-Period Data

**If computing ratios, growth rates, or year-over-year changes and you only have ONE data point, STOP.**

You MUST extract distinct values for EACH time period. Using the same value for multiple periods is ALWAYS WRONG.

- ❌ WRONG: Extract 1964 Treasury value ($209,344M), apply it to 1964, 1965, 1966
- ✓ CORRECT: Extract 1964 value from 1964 bulletin, 1965 value from 1965 bulletin, 1966 value from 1966 bulletin

### BLOCKED: Sample Statistics with Wrong Denominator

**If you are computing standard deviation for sample data (not full population) and using n as the denominator, STOP.**

The sample standard deviation REQUIRES dividing by (n-1), not n. This is called Bessel's correction.

**Example from failure:**
- Data points: [1.3, 1.4] (n=2)
- Mean: 1.35
- Sum of squared deviations: (1.3-1.35)² + (1.4-1.35)² = 0.0025 + 0.0025 = 0.005

**WRONG (population formula with n):**
- Variance = 0.005 / 2 = 0.0025
- Std = √0.0025 = 0.05
- Z-score = 2.65 / 0.05 = 53.0 ← WRONG

**CORRECT (sample formula with n-1):**
- Variance = 0.005 / 1 = 0.005
- Std = √0.005 ≈ 0.0707
- Z-score = 2.65 / 0.0707 ≈ 37.48 ← CORRECT

**The smaller the sample, the bigger the impact:** With n=2, using n instead of n-1 underestimates std by factor of √2 ≈ 1.41, making your Z-score 41% too high.

---

## ⚠️ MOST COMMON ERRORS — CHECK BEFORE PROCEEDING

| Error # | Wrong Approach | Why It's Wrong | Correct Approach |
|---------|---------------|----------------|------------------|
| 1 | Taking min(yield levels) as ES | ES requires RETURNS, not levels | Compute returns first, then ES on returns |
| 2 | Using March 1 exchange rates for end-of-March prices | Dates must match exactly | Use end-of-March exchange rates |
| 3 | Using single data point for all periods in time series | Ratios will be trivially 1.0 or wrong | Extract separate values for each year/period |
| 4 | Use n as divisor for variance when working with sample data | Underestimates variance by factor of n/(n-1); effect is large for small n | Use n-1 (Bessel's correction) for sample statistics |
| 5 | Compute std with n=2, variance = sum/2 | With only 2 data points, variance = sum/1, giving √2 times larger std | For n=2: variance = Σ(x-x̄)²/1, not /2 |

**If your approach matches any error pattern above, STOP and reconsider.**

---

## Validation Checkpoint Templates

**Output the appropriate checkpoint BEFORE any multi-step financial calculation:**

### For ES/VaR/Volatility Calculations

```
VALIDATION CHECKPOINT - Risk Calculation
Check 1: Data Form
  - Required form: returns
  - Current form: [levels/returns]
  - Status: [PASS if returns / BLOCKED if levels - must compute returns first]
Check 2: Return Calculation (if transformed)
  - Formula used: [e.g., (V_t - V_{t-1}) / V_{t-1}]
  - Sample calculation: [show one example]
  - Status: [PASS if verified / BLOCKED if not shown]
Check 3: Output Sign Convention
  - Loss representation: negative returns
  - Status: [PASS if convention documented]
OVERALL: [PASS - proceed / BLOCKED - halt and resolve]
```

### For Currency Conversion

```
VALIDATION CHECKPOINT - Currency Conversion
Check 1: Date Alignment
  - Price observation date: [exact date from source]
  - Exchange rate date: [exact date from rate source]
  - Status: [PASS if identical / BLOCKED if different]
Check 2: Rate Direction
  - Quote convention: [e.g., "DEM per USD" or "USD per DEM"]
  - Operation to apply: [multiply/divide]
  - Status: [PASS if verified / BLOCKED if uncertain]
Check 3: Source Documentation
  - Price source: [document/table/cell reference]
  - Rate source: [document/API/reference]
  - Status: [PASS if documented / BLOCKED if assumed]
OVERALL: [PASS - proceed / BLOCKED - halt and resolve]
```

### For Forecasting

```
VALIDATION CHECKPOINT - Forecasting
Check 1: Notation Parsing
  - Raw value: [as appears in source]
  - Parsed value: [decimal equivalent]
  - Parsing method: [e.g., "32nds: 76 + 18/32 = 76.5625"]
  - Status: [PASS if shown / BLOCKED if assumed]
Check 2: Initialization Method
  - Method: [e.g., "F_1 = Y_1 (first observation)"]
  - Initial value: [numeric]
  - Status: [PASS if explicit]
Check 3: Error Convention
  - Formula: Error = Actual - Forecast
  - Status: [PASS if using standard convention]
OVERALL: [PASS - proceed / BLOCKED - halt and resolve]
```

### For Multi-Period Time Series Calculations

```
VALIDATION CHECKPOINT - Multi-Period Data Completeness
Check 1: Periods Required
  - Question asks about years/periods: [list all periods, e.g., 1964, 1965, 1966]
  - Distinct data points needed: [N]
  - Status: [PASS if N >= 2 for ratios / BLOCKED if N < 2]
Check 2: Data Extracted for Each Period
  - Period 1: [year] → Value: [X] → Source: [document/line]
  - Period 2: [year] → Value: [Y] → Source: [document/line]
  - Period 3: [year] → Value: [Z] → Source: [document/line]
  - Are all values DISTINCT (not the same number repeated)?: [YES/NO]
  - Status: [PASS if distinct values / BLOCKED if same value repeated]
Check 3: Source Document Dates
  - Does each value come from a document dated to that period?: [YES/NO]
  - Status: [PASS if period-matched / FLAG if using single-period data for all]
OVERALL: [PASS - proceed / BLOCKED - must find data for each period]
```

---

## Part 9: Statistical Inference Methodology

### Pre-Calculation Verification

**TRIGGER: Question involves Z-score, statistical significance, "unusual", hypothesis testing, or standard deviation calculations**

```
═══════════════════════════════════════════════════════════
STATISTICAL CALCULATION VERIFICATION - BEFORE Z-SCORE/HYPOTHESIS TESTS
═══════════════════════════════════════════════════════════

Check 1 - Sample vs Population:
  Am I calculating statistics for a SAMPLE or the full POPULATION?: [SAMPLE/POPULATION]
  Sample size (n): [N]
  Status: [If n < 30, almost certainly use sample statistics with n-1]

Check 2 - Standard Deviation Formula Selection:
  Population std (σ): √(Σ(x-μ)² / n)       ← Use ONLY if you have the entire population
  Sample std (s):     √(Σ(x-x̄)² / (n-1))   ← Use for samples (DEFAULT)

  I am using: [sample/population] formula
  Denominator in variance calculation: [n / n-1]
  Status: [PASS if n-1 for sample / BLOCKED if using n for sample data]

Check 3 - Small Sample Warning (n ≤ 5):
  Sample size: [N]
  If n ≤ 5: Standard deviation estimates are highly unstable
  Consider: Document this limitation in output
  Status: [PASS with documented limitation / FLAG if not acknowledged]

STATISTICAL VERIFICATION RESULT: [PROCEED / BLOCKED]
═══════════════════════════════════════════════════════════
```

### Validation Checkpoint for Z-Score / Hypothesis Testing

```
VALIDATION CHECKPOINT - Statistical Inference
Check 1: Sample vs Population Determination
  - Data source: [sample from larger population / complete population]
  - Sample size (n): [N]
  - Status: [PASS if determination is explicit / BLOCKED if assumed]
Check 2: Standard Deviation Formula
  - Using formula: [sample s with n-1 / population σ with n]
  - Denominator value: [n-1 = X / n = X]
  - Status: [PASS if sample data uses n-1 / BLOCKED if sample data uses n]
Check 3: Calculation Verification (show work)
  - Sum of squared deviations: [show calculation]
  - Divided by: [n-1 or n]
  - Variance: [result]
  - Std: [√variance]
  - Status: [PASS if arithmetic verified / BLOCKED if not shown]
OVERALL: [PASS - proceed / BLOCKED - halt and resolve]
```

---

## Part 1: Risk Metric Methodology

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
4. Average those worst returns → ES

**Common error:** Taking min/max of raw levels. This is NOT ES.

### Value at Risk (VaR)

Same transformation rules as ES. VaR is the threshold loss at confidence level alpha.

```
VaR_alpha = quantile(returns, alpha)
```

At 95% confidence, VaR is the 5th percentile of returns.

---

## Part 2: Forecasting Methodology

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

---

## Part 3: Currency Conversion

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

**CRITICAL Date Alignment Rules:**
- "End of March" prices require "end of March" exchange rates
- "March 1" != "end of March" → BLOCKED
- "April 1" != "end of March" → BLOCKED
- Treasury Bulletin April edition contains END OF MARCH data

---

## Part 4: Government Accounting Classifications

**CRITICAL: Use OMB/Treasury definitions, not intuitive interpretation.**

For federal obligation classifications, see `references/federal-accounting.md`.

Key principle: "Service-related" in federal accounting has specific regulatory meaning per OMB Circular A-11 that differs from casual interpretation.

---

## Part 5: Data Transformation Rules

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

## Part 6: Multi-Source Data Combination

**Before combining time series from different sources:**

```
VALIDATION CHECKPOINT - Data Combination
Check 1: Frequency Match
  - Source A frequency: [monthly/quarterly/etc.]
  - Source B frequency: [monthly/quarterly/etc.]
  - Status: [PASS if identical / BLOCKED if different]
Check 2: Date Convention Match
  - Source A dates: [e.g., "end of month"]
  - Source B dates: [e.g., "end of month"]
  - Status: [PASS if identical / BLOCKED if different]
Check 3: Period Alignment
  - Sample period: [e.g., "March 1972"]
  - Source A date: [exact date]
  - Source B date: [exact date]
  - Status: [PASS if aligned / BLOCKED if misaligned]
OVERALL: [PASS - proceed / BLOCKED - halt and resolve]
```

---

## Part 7: Output Verification — BEFORE REPORTING RESULTS

### ES/VaR Output Check

**If your ES value equals the minimum of your raw data values, you made the levels-vs-returns error. Go back and compute returns.**

Example self-check:
- Raw yield values: [9.56, 9.60, 8.36, 7.37, 7.68, 6.69, 5.87, 6.04, 5.65, 6.14]
- Minimum raw value: 5.65
- Your ES answer: 5.65 ← **WRONG** — this equals min(raw), indicating ES was computed on levels
- Correct: Compute returns first, then ES on returns (will be a negative percentage)

### Forecasting Output Check

**If your forecast error is in the range of ±5 for DEM-converted bond prices, verify you used end-of-month exchange rates, not month-start rates.**

Systematic ±5 error often indicates exchange rate date misalignment when converting USD Treasury prices to DEM.

### Quick Verification Table

| Metric | Expected Characteristics | Red Flag |
|--------|-------------------------|----------|
| ES on returns | Negative value (for loss measurement) | Positive or equals raw data min |
| VaR on returns | Negative value at alpha < 50% | Positive or equals raw percentile of levels |
| Parsed 32nds price | Close to quoted integer | >1 point difference |
| Exponential smooth | Between min and max of data | Outside data range |
| Forecast error sign | Negative if over-forecast | Sign seems reversed |
| Currency conversion | Same order of magnitude | 10x or 0.1x original |
| Date alignment | Exact date match | Off by days |

---

## Part 8: Multi-Period Time Series Calculations

### Year-over-Year Ratio Calculations

**CRITICAL: Ratios require DISTINCT values for numerator and denominator periods.**

When computing:
- Year-over-year ratios: Y_t / Y_{t-1}
- Growth rates: (Y_t - Y_{t-1}) / Y_{t-1}
- Multi-year differences: |ratio_1 - ratio_2|

You MUST extract separate data for EACH time period.

**Example - Computing ratio difference across 3 years:**

Question: "What is the absolute difference between the 1965/1964 ratio and 1966/1965 ratio of Treasury securities in INR?"

Required data extraction:
- Treasury value for 1964: [from 1964 bulletin]
- Treasury value for 1965: [from 1965 bulletin]
- Treasury value for 1966: [from 1966 bulletin]
- Exchange rate for 1964
- Exchange rate for 1965
- Exchange rate for 1966

**Self-Check:** If your ratio calculation yields exactly 1.0, verify you didn't use the same underlying value for both periods.

### Data Extraction Strategy for Multi-Period Queries

1. **Identify all required periods** from the question (e.g., 1964, 1965, 1966)
2. **For each period**, locate the appropriate source document (e.g., Treasury Bulletin from that year)
3. **Extract and record** the value for each period with its source
4. **Verify distinctness** - if values are identical, confirm this is correct (unusual for multi-year Treasury data)
5. **Then proceed** with calculations

### Output Verification for Time Series

If computing year-over-year ratios and ANY ratio equals exactly 1.0000:
- Verify this reflects genuine data (same values across years is rare for Treasury data)
- If you used the same extracted value for multiple years, GO BACK and find period-specific values

---

## Quick Decision Tree

```
Starting a financial analysis task?
│
├── OUTPUT MANDATORY VERIFICATION BLOCK FIRST
│   └── If any check is BLOCKED → resolve before proceeding
│
├── Calculating ES, VaR, or volatility?
│   ├── Is data already in return form?
│   │   ├── YES → Proceed with calculation
│   │   └── NO → Compute returns first, then calculate
│   └── OUTPUT CHECK: Does ES equal min(raw_values)?
│       └── YES → WRONG — go back and compute returns
│
├── Doing forecasting?
│   ├── Is price data in 32nds notation?
│   │   ├── YES → Parse: Integer + Fractional/32
│   │   └── NO → Use as-is (verify it's decimal)
│   ├── Using exponential smoothing?
│   │   └── Initialize: F_1 = Y_1 (first observation)
│   └── Computing error?
│       └── Error = Actual - Forecast (signed)
│
├── Converting currencies?
│   ├── Match exchange rate date to price date exactly
│   │   └── "March 1" ≠ "end of March" → BLOCKED
│   ├── Verify rate direction (per USD or per foreign)
│   └── Validate converted magnitude is reasonable
│
├── Calculating year-over-year ratios or time series metrics?
│   ├── Do you have data extracted for EACH time period?
│   │   ├── YES → Proceed with calculation
│   │   └── NO → BLOCKED - find data for each required period
│   └── OUTPUT CHECK: Does any ratio equal exactly 1.0?
│       └── YES → Verify you didn't reuse same value for multiple periods
│
├── Computing Z-score, significance test, or standard deviation?
│   │
│   ├── FIRST: Determine if data is sample or population
│   │   ├── Is this ALL possible data points? → Population (use n)
│   │   └── Is this a SUBSET of observations? → Sample (use n-1)
│   │
│   ├── For SAMPLE standard deviation (the default case):
│   │   └── Variance = Σ(x-x̄)² / (n-1)  ← NOT divided by n
│   │   └── std = √variance
│   │
│   ├── For Z-score calculation:
│   │   └── Z = (x - mean) / std
│   │   └── Verify std calculation used correct formula before computing Z
│   │
│   └── OUTPUT CHECK: For small n, is your std suspiciously small?
│       └── Example: If n=2 and values differ by 0.1, std should be ≈ 0.07, not 0.05
│       └── If std seems too small, verify you used n-1, not n
│
└── Classification task?
    └── Check references/federal-accounting.md for definitions
```
