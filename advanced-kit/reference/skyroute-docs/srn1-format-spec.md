# SRN-1 navigation data format specification

**Document:** SRN-DOC-001, revision C. **Status:** synthetic training material. Not for navigation.

This specification describes SRN-1, the fixed-width text format that SkyRoute reads from `data/navdata.srn`. It matches the behavior of `skyroute/navdata.py`, including the quirks in Section 5. A reader that changes any rule in this document is a behavior change and needs a requirement change first.

## 1. Files

- Encoding is ASCII. UTF-8 without non-ASCII characters is accepted.
- One record per line. Line endings may be LF or CRLF.
- A file covers one AIRAC-style cycle. The header comment names it, for example `CYCLE 2611`.

## 2. Line kinds

| Line starts with | Meaning | Reader action |
|------------------|---------|---------------|
| `*` | Comment | Ignored |
| Blank, or spaces only | Separator | Ignored |
| `AP` | Airport record | Loaded |
| `WP` | Waypoint (fix) record | Loaded |
| `NV` | Navaid record | Loaded |
| Any other text, including lowercase `wp` | Unknown kind | Ignored without a message |

Requirements: SR-NAV-001 (record kinds), SR-NAV-002 (comments and blank lines).

## 3. Record columns

Columns are zero-based character positions. One space separates fields.

| Columns | Field | Format | Example |
|---------|-------|--------|---------|
| 0 to 1 | Kind | `AP`, `WP`, or `NV` | `AP` |
| 3 to 7 | Ident | Up to 5 characters, left-justified, padded with spaces | `KDVT ` |
| 9 to 17 | Latitude | Hemisphere letter, then `DDMMSSss` | `N33411800` |
| 19 to 28 | Longitude | Hemisphere letter, then `DDDMMSSss` | `W112045700` |
| 30 to 34 | Elevation | Feet, right-justified. Optional. | ` 1478` |
| 36 to 41 | Frequency | MHz with two decimals. Optional, used by `NV`. | `113.90` |
| 43 to end | Name | Free text. Optional. Surrounding spaces are removed. | `PHOENIX DEER VALLEY` |

A record may end after the longitude. Waypoint records usually do.

## 4. Coordinates

`DDMMSSss` is degrees, minutes, seconds, and hundredths of a second. Decimal degrees are:

```
degrees + minutes / 60 + seconds / 3600 + hundredths / 360000
```

`N33411800` is 33 degrees, 41 minutes, 18.00 seconds north, which is 33.688333 decimal degrees. `S` and `W` make the value negative.

## 5. Reader rules and quirks

These rules are part of the format contract. The characterization tests in `tests/test_navdata_characterization.py` pin each one.

1. **Malformed records.** A record whose fields cannot be parsed (for example the letter `O` in place of the digit zero) is skipped. The rest of the file still loads. (SR-NAV-003)
2. **Duplicates.** When an ident appears more than once, the last record wins. Amendments use this: the amended record follows the original with a comment such as `AMDT 07`. (SR-NAV-004)
3. **Missing elevation** reads as `0`, not as unknown.
4. **Zero frequency.** A frequency of `0.00` reads as no frequency.
5. **Hemisphere letters.** Only uppercase `S` and `W` give negative values. Any other letter, including lowercase `s` and `w`, gives a positive value.
6. **Lookup case.** Idents are stored as written. Lookup converts the query to uppercase and strips spaces, so a lowercase ident in the file loads but cannot be found.
7. **Caching.** Each file is read once per process. Edits after the first load are not seen until `navdata.clear()` is called.

## 6. Example

```
* SRN-1 NAVIGATION DATA      CYCLE 2611      SYNTHETIC TRAINING SET
AP KDVT  N33411800 W112045700  1478        PHOENIX DEER VALLEY
NV SRV   N33373000 W111521200  1520 113.90 SAGUARO
WP ZUNIX N35300000 W109000000
```

## 7. Revision history

| Revision | Change |
|----------|--------|
| A | First issue: `AP` and `WP` records |
| B | Added `NV` records and the frequency field |
| C | Documented reader quirks 1 to 7 as part of the contract |
