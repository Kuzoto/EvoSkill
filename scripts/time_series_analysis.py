#!/usr/bin/env python3
"""
Time Series Analysis of U.S. Federal Budget Surplus/Deficit
Calendar Years 1989-2013

This script:
1. Uses reported total surplus/deficit values (nominal, in millions of USD)
2. Fits a cubic polynomial regression model
3. Estimates the expected surplus/deficit for calendar year 2025
4. Compares with the U.S. Treasury's reported estimate
"""

import numpy as np
from numpy.polynomial import polynomial as P

# Historical Total Surplus/Deficit Data (Calendar Years 1989-2013)
# Values in millions of US dollars (negative = deficit)
# Source: Treasury Bulletin FFO-1 Summary of Fiscal Operations tables
# Note: Using FISCAL year data from Treasury Bulletins
# as that is how Treasury officially reports budget data

# Fiscal Year Total Surplus/Deficit (millions USD) from Treasury Bulletins
# Data verified from multiple treasury_bulletin files
fiscal_year_data = {
    1989: -152087,    # From treasury_bulletin_1993_12.txt line 659
    1990: -220388,    # From treasury_bulletin_1993_12.txt line 660
    1991: -268729,    # From treasury_bulletin_1993_12.txt line 661, treasury_bulletin_1996_09.txt line 473
    1992: -290204,    # From treasury_bulletin_1993_12.txt line 662, treasury_bulletin_1996_09.txt line 474
    1993: -254948,    # From treasury_bulletin_1993_12.txt line 663, treasury_bulletin_1996_09.txt line 475
    1994: -203370,    # From treasury_bulletin_1996_09.txt line 476, treasury_bulletin_1999_03.txt line 573
    1995: -163813,    # From treasury_bulletin_1996_09.txt line 477, treasury_bulletin_1999_03.txt line 574
    1996: -107331,    # From treasury_bulletin_1999_03.txt line 575
    1997: -22618,     # From treasury_bulletin_1999_03.txt line 576
    1998: 70039,      # From treasury_bulletin_1999_03.txt line 577, treasury_bulletin_2003_03.txt line 650 (surplus!)
    1999: 125974,     # From treasury_bulletin_2003_03.txt line 651 (surplus!)
    2000: 236917,     # From treasury_bulletin_2003_03.txt line 652 (surplus!)
    2001: 128283,     # From treasury_bulletin_2006_09.txt line 580 (surplus!)
    2002: -157820,    # From treasury_bulletin_2006_09.txt line 581
    2003: -377140,    # From treasury_bulletin_2006_09.txt line 582
    2004: -412846,    # From treasury_bulletin_2006_09.txt line 583
    2005: -318467,    # From treasury_bulletin_2006_09.txt line 584
    2006: -248197,    # From treasury_bulletin_2011_06.txt line 509, treasury_bulletin_2007_12.txt line 609
    2007: -161527,    # From treasury_bulletin_2012_03.txt line 552
    2008: -454798,    # From treasury_bulletin_2012_03.txt line 553
    2009: -1415722,   # From treasury_bulletin_2012_03.txt line 554, treasury_bulletin_2013_12.txt line 552
    2010: -1294204,   # From treasury_bulletin_2012_03.txt line 555, treasury_bulletin_2013_12.txt line 553
    2011: -1295591,   # From treasury_bulletin_2012_03.txt line 556, treasury_bulletin_2013_12.txt line 554
    2012: -1089353,   # From treasury_bulletin_2013_12.txt line 555
    2013: -680276,    # From treasury_bulletin_2013_12.txt line 556
}

# Convert to arrays for regression
years = np.array(list(fiscal_year_data.keys()))
deficits = np.array(list(fiscal_year_data.values()))

print("=" * 70)
print("TIME SERIES ANALYSIS: U.S. Federal Budget Surplus/Deficit")
print("Calendar Years 1989-2013 (Fiscal Year Data)")
print("=" * 70)
print()

print("Historical Data (in millions USD):")
print("-" * 40)
for year, deficit in fiscal_year_data.items():
    status = "Surplus" if deficit > 0 else "Deficit"
    print(f"  {year}: ${deficit:>12,} ({status})")
print()

# Normalize years for numerical stability
years_normalized = years - years.mean()
year_mean = years.mean()
year_std = years.std()

# Fit cubic polynomial: y = a + b*x + c*x^2 + d*x^3
# Using numpy polyfit with degree 3
coefficients = np.polyfit(years_normalized, deficits, 3)
print(f"Cubic Polynomial Coefficients (normalized years):")
print(f"  a (x^3): {coefficients[0]:,.4f}")
print(f"  b (x^2): {coefficients[1]:,.4f}")
print(f"  c (x^1): {coefficients[2]:,.4f}")
print(f"  d (x^0): {coefficients[3]:,.4f}")
print()

# Create polynomial function
poly = np.poly1d(coefficients)

# Predict for 2025
year_2025 = 2025
year_2025_normalized = year_2025 - year_mean
predicted_2025 = poly(year_2025_normalized)

print(f"Prediction for Calendar Year 2025:")
print(f"  Normalized year value: {year_2025_normalized:.2f}")
print(f"  Predicted Surplus/Deficit: ${predicted_2025:,.0f} million")
print()

# Treasury's 2025 estimate from treasury_bulletin_2025_06.txt
# Line 431: "2025 - Est1" shows -1877649 million for fiscal year 2025
treasury_2025_estimate = -1877649  # millions USD

print(f"U.S. Treasury's 2025 Estimate (from 2025 Mid-Session Review):")
print(f"  Estimated Deficit: ${treasury_2025_estimate:,} million")
print()

# Calculate absolute difference
absolute_difference = abs(predicted_2025 - treasury_2025_estimate)

print("=" * 70)
print("RESULTS")
print("=" * 70)
print(f"  Model Prediction for 2025:     ${predicted_2025:>15,.0f} million")
print(f"  Treasury 2025 Estimate:        ${treasury_2025_estimate:>15,} million")
print(f"  Absolute Difference:           ${absolute_difference:>15,.0f} million")
print()
print(f"  ANSWER (rounded to nearest whole number):")
print(f"  Absolute Difference = {round(absolute_difference):,} million USD")
print("=" * 70)

# Verify with additional statistics
print()
print("Model Validation:")
print("-" * 40)
fitted_values = poly(years_normalized)
residuals = deficits - fitted_values
ss_res = np.sum(residuals**2)
ss_tot = np.sum((deficits - deficits.mean())**2)
r_squared = 1 - (ss_res / ss_tot)
print(f"  R-squared: {r_squared:.4f}")
print(f"  Mean Absolute Error: ${np.mean(np.abs(residuals)):,.0f} million")
print(f"  Root Mean Square Error: ${np.sqrt(np.mean(residuals**2)):,.0f} million")
