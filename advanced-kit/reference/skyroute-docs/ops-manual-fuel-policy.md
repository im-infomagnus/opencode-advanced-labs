# SkyRoute operations manual, Chapter 4: Fuel policy (excerpt)

**Document:** SRN-OPS-004, revision B. **Status:** synthetic training material. Not an operational procedure.

This chapter states the fuel policy that SkyRoute flight plans implement. Requirement IDs in brackets link each rule to `requirements/requirements.json`. Units are pounds (lb) for fuel, pounds per hour (lb/h) for burn rate, and hours for time.

## 4.1 Fuel components

Every plan has three components. The planned total is their sum.

| Component | Rule | Default | Requirement |
|-----------|------|---------|-------------|
| Trip fuel | Time enroute multiplied by the burn rate | none | SR-FUEL-001 |
| Contingency fuel | Configured percentage of **trip fuel only** | 5 percent | SR-FUEL-002 |
| Final reserve | Configured minutes at the burn rate | 30 minutes | SR-FUEL-003 |
| Total | Trip plus contingency plus final reserve | none | SR-FUEL-003 |

## 4.2 Contingency fuel

Contingency covers deviations during the trip: routing changes, wind differences, and holding not in the plan. Because it covers the trip, it is a percentage of trip fuel. It is **not** a percentage of trip plus reserve, and it is not a percentage of the total. Applying the percentage to the reserve inflates the plan and hides errors in the trip estimate.

Operators may configure a different percentage. A negative percentage is rejected.

## 4.3 Final reserve

The final reserve is fuel for the configured number of minutes at the planned burn rate. It does not depend on the trip length. A negative number of minutes is rejected.

## 4.4 Input checks

- Time enroute below zero is rejected.
- A burn rate of zero or less is rejected.
- Time enroute comes from the route: total distance divided by ground speed (SR-RTE-003). A ground speed of zero or less is rejected.

## 4.5 Worked examples

**Example A.** Time enroute 2.0 h, burn 2400 lb/h, defaults.

| Component | Calculation | Fuel (lb) |
|-----------|-------------|-----------|
| Trip | 2.0 x 2400 | 4800 |
| Contingency | 5 percent of 4800 | 240 |
| Final reserve | 30 / 60 x 2400 | 1200 |
| Total | 4800 + 240 + 1200 | 6240 |

A plan that applies 5 percent to trip plus reserve shows contingency 300 and total 6300. That plan is wrong.

**Example B.** Same trip, contingency 10 percent, reserve 45 minutes.

| Component | Calculation | Fuel (lb) |
|-----------|-------------|-----------|
| Trip | 2.0 x 2400 | 4800 |
| Contingency | 10 percent of 4800 | 480 |
| Final reserve | 45 / 60 x 2400 | 1800 |
| Total | 4800 + 480 + 1800 | 7080 |

**Example C.** Route KDVT, ZUNIX, KMSP at 450 kt and 2400 lb/h. The SkyRoute plan report shows total distance 1101.5 NM, time enroute 2:27, trip 5875 lb, contingency 294 lb, reserve 1200 lb, and total 7368 lb (each value rounded for display).

## 4.6 Verification

Each rule in 4.1 has at least one unit test listed in the requirement's `tests` field. A change to a default value, or to what a percentage applies to, needs a requirement change and a review before the code changes.
