# Federal Accounting Classification Guide

Reference for OMB Circular A-11 and Treasury reporting classifications.

## Object Class Classification (OMB A-11 Section 83)

Federal obligations are classified by object class codes that determine category membership.

### Service-Related Obligations (Object Classes 10-25)

Per OMB Circular A-11 Section 83, **service-related obligations** encompass:

| Object Class | Category | Description |
|--------------|----------|-------------|
| 11 | Personnel compensation | Full-time permanent, other than full-time permanent, other personnel compensation |
| 12 | Personnel benefits | Civilian personnel benefits, military personnel benefits |
| 13 | Benefits for former personnel | Pensions, annuities, other benefits |
| 21 | Travel | Transportation of persons |
| 22 | Transportation | Transportation of things |
| 23 | Rent, communications, utilities | Rental payments, communications, utilities |
| 24 | Printing and reproduction | Printing, binding, and reproduction |
| 25 | Other contractual services | Advisory services, other services, goods acquired by contract |

**Key insight:** Service-related includes contracted services (object class 25), not just personnel compensation (11-12).

### Non-Service-Related Obligations (Object Classes 26-99)

| Object Class | Category | Description |
|--------------|----------|-------------|
| 26 | Supplies and materials | Office supplies, equipment maintenance supplies |
| 31 | Equipment | Acquisition of equipment |
| 32 | Land and structures | Acquisition of land and structures |
| 33 | Investments and loans | Investments in non-Federal entities |
| 41 | Grants, subsidies, contributions | Grants, subsidies to state/local governments |
| 42 | Insurance claims and indemnities | Insurance claims, judgments |
| 43 | Interest and dividends | Interest, dividends, and finance charges |
| 44 | Refunds | Refunds of receipts |
| 91 | Undistributed | Amounts not allocable to specific object classes |
| 99 | Subtotal, obligations | Aggregation category |

## Classification Calculation

To determine service-related percentage:

```
Service-Related % = (Sum of Object Classes 10-25) / (Total Obligations) × 100
```

**Example:**
- Personnel services and benefits: $73,089M (Object classes 11-13)
- Contractual services: $120,000M (Object classes 21-25)
- Total service-related: $193,089M
- Total obligations: $614,968M
- Service-related %: 31.4%

**Common error:** Only counting personnel compensation as "service-related" yields ~12%, missing the contractual services component that significantly increases the ratio.

## Treasury Bulletin Table Mapping

| Table | Contains | Relevant Classifications |
|-------|----------|-------------------------|
| Budget Outlays by Agencies | Agency-level expenditures | Maps to object class aggregations |
| Budget Receipts | Revenue sources | Different classification system |
| Federal Obligations by Object Class | Direct object class breakdown | Authoritative for classification analysis |

## Terminology Precision

| Term | Incorrect Interpretation | Correct Definition |
|------|-------------------------|-------------------|
| Service-related | Personnel only | Personnel + all contracted services (obj 10-25) |
| Personal services | All service-related | Only compensation (obj 11) |
| Contractual services | Non-service | Part of service-related (obj 21-25) |
| Direct obligations | Current year only | May include multi-year obligations |

## Validation Heuristics

Expected ranges for federal budget classifications:

| Metric | Typical Range | Red Flag Range |
|--------|---------------|----------------|
| Service-related % | 25-45% | <15% or >60% |
| Personnel % of total | 10-20% | <5% or >35% |
| Contractual services % | 15-30% | <10% or >50% |

If calculated value falls outside typical range, verify:
1. All relevant object classes included
2. Using correct OMB definitions
3. Data source covers full scope
