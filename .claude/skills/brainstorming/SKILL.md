---
name: Brainstorming
description: IMMEDIATELY USE THIS SKILL when answering data analysis questions from treasury_bulletins_parsed - internal design thinking that identifies the question type, selects applicable skills, and converges on the best analytical approach before implementation
---

# Internal Design Thinking for Treasury Data Analysis

## Overview

Structured self-dialogue before answering treasury/fiscal data questions. Analyze the question, identify which skills apply, reason through the approach, then execute.

**Core principle:** Think first, execute second. Map the question to the right skill chain before acting.

## The Process

### Phase 1: Question Classification

Analyze the question to determine:

- **Data type**: Interest on debt, budget outlays, receipts, yields, international capital, savings bonds, securities ownership
- **Time scope**: Single point, time series, year-over-year comparison
- **Calculation type**: Raw extraction, inflation-adjusted, ratio, regression, risk metric (ES/VaR), forecast
- **Output format**: Percentage, absolute value, [slope, intercept], ratio

### Phase 2: Skill Selection

Review available skills and determine which apply:

| Question Pattern | Required Skills |
|-----------------|-----------------|
| Any Treasury/fiscal data lookup | `treasury-data-local-first-protocol` (ALWAYS FIRST) |
| Inflation adjustment, regression, trend | `economic-timeseries-analysis` |
| ES, VaR, forecasting, currency conversion | `quantitative-analysis-methodology` |
| Final numeric answer | `answer-output-normalizer` (ALWAYS LAST) |

**Skill chain reasoning:**
- "This question asks for [X], which requires [skill A] because..."
- "After getting raw data, I need [skill B] for [transformation]..."
- "Final output needs [skill C] to ensure [format requirement]..."

### Phase 3: Approach Design

For the selected skills, map out the execution path:

1. **Data retrieval**: Which treasury_bulletins_parsed files? What grep patterns?
2. **Transformations**: Inflation adjustment? Return calculation? Currency conversion?
3. **Analysis**: Regression? Risk metric? Ratio calculation?
4. **Validation**: What checkpoints from quantitative-analysis-methodology apply?
5. **Output**: What format does the question expect?

State assumptions explicitly:
- "Assuming fiscal year convention from Treasury Bulletins..."
- "Using CPI base period of [X] because..."
- "Interpreting 'rate' as percentage without symbol..."

### Phase 4: Design Summary

Before execution, articulate the plan:

```
## Analysis Plan

**Question type:** [classification]

**Skills to apply:**
1. treasury-data-local-first-protocol → [specific purpose]
2. [additional skills] → [specific purpose]
3. answer-output-normalizer → [output format]

**Data sources:** treasury_bulletins_parsed/[files]

**Key steps:**
1. [step]
2. [step]
...

**Assumptions:** [list any]

**Proceeding with analysis.**
```

### Phase 5: Execute

- Follow the skill chain in order
- Apply validation checkpoints from quantitative-analysis-methodology
- Format final output per answer-output-normalizer

## Quick Reference: Skill Triggers

| If question involves... | Trigger skill... |
|------------------------|------------------|
| Treasury, fiscal, budget, debt data | treasury-data-local-first-protocol |
| CPI, inflation adjustment, real values | economic-timeseries-analysis |
| Linear regression on time series | economic-timeseries-analysis |
| ES, VaR, volatility | quantitative-analysis-methodology |
| Bond price notation (32nds) | quantitative-analysis-methodology |
| Exponential smoothing, forecasting | quantitative-analysis-methodology |
| Currency conversion | quantitative-analysis-methodology |
| Year-over-year ratios, growth rates | quantitative-analysis-methodology |
| Any numeric answer | answer-output-normalizer |

## Remember

- This is internal reasoning - no questions, no waiting
- ALWAYS start with treasury-data-local-first-protocol for data retrieval
- ALWAYS end with answer-output-normalizer for final output
- State assumptions so errors are traceable
- The goal is selecting the right skill chain, not documenting
- Once the plan is clear, execute immediately
