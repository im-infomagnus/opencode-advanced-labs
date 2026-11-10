# SRN-1 navigation data format

This note is the expected result of exploring `skyroute/navdata.py` and `data/navdata.srn` with an agent. It describes the format as the reader actually handles it, quirks included.

## Lines

- One record per line. Line endings may be LF or CRLF.
- A line that starts with `*` is a comment. Blank lines and lines of only spaces are ignored.
- Columns 0 and 1 hold the record kind. Only `AP` (airport), `WP` (waypoint), and `NV` (navaid) are read. Any other kind, including lowercase `wp`, is ignored without a message.

## Columns

Columns are zero-based character positions. Fields are separated by one space.

| Columns | Field | Format | Example |
|---------|-------|--------|---------|
| 0 to 1 | Kind | `AP`, `WP`, or `NV` | `AP` |
| 3 to 7 | Ident | Up to 5 characters, left-justified | `KDVT ` |
| 9 to 17 | Latitude | Hemisphere letter, then `DDMMSSss` (degrees, minutes, seconds, hundredths of seconds) | `N33411800` |
| 19 to 28 | Longitude | Hemisphere letter, then `DDDMMSSss` | `W112045700` |
| 30 to 34 | Elevation | Feet, right-justified. Optional. | ` 1478` |
| 36 to 41 | Frequency | MHz, for example `113.90`. Optional, used by `NV` records. | `113.90` |
| 43 to end | Name | Free text. Optional. Surrounding spaces are removed. | `PHOENIX DEER VALLEY` |

A record can end after the longitude. Waypoints usually do.

## Quirks the reader preserves

- A malformed record (for example the letter `O` in place of a zero) is skipped without an error. The rest of the file still loads.
- When an ident appears more than once, the last record wins. The data file uses this for amendments.
- A missing elevation reads as `0`, not as "unknown".
- A frequency of `0.00` reads as no frequency (`None`).
- Only uppercase `S` and `W` give negative coordinates. Any other hemisphere letter, including lowercase `s` and `w`, gives a positive value.
- Idents are stored exactly as written, but lookup converts the query to uppercase. A lowercase ident in the file loads but cannot be found with `lookup`.
- Each file is read once per process and then cached. Edits to the file after the first load are not seen until `navdata.clear()` is called.
