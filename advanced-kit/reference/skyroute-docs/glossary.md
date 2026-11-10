# SkyRoute glossary

**Status:** synthetic training material.

| Term | Meaning in SkyRoute |
|------|---------------------|
| AIRAC cycle | A four-digit data cycle label such as `2611`. SkyRoute prints it but does not check it. |
| Airport (`AP`) | SRN-1 record for an aerodrome. Positions in the training data come from public sources. |
| Amendment (`AMDT`) | A later record for the same ident. The last record in the file wins. |
| Bearing, initial | True course at the start of a great-circle leg, in degrees normalized to [0, 360). See SR-GEO-002. |
| Contingency fuel | Configured percentage (default 5) of trip fuel only. See the fuel policy, 4.2. |
| ETE | Estimated time enroute: total distance divided by ground speed, in hours. |
| Final reserve | Fuel for the configured minutes (default 30) at the burn rate. |
| Fix | Any point in navigation data: airport, waypoint, or navaid. Code type `navdata.Fix`. |
| Great-circle distance | Shortest distance on a sphere of radius 3440.065 NM (haversine). See SR-GEO-001. |
| Ground speed (GS) | Speed over the ground in knots. Must be greater than zero. |
| Ident | Identifier of a fix, up to 5 characters, for example `KDVT` or `ZUNIX`. |
| Leg | The segment between two consecutive fixes of a route. |
| Navaid (`NV`) | Radio navigation aid record with a frequency in MHz. |
| NM | Nautical mile, 1852 metres. |
| Route | Ordered list of at least two fixes, written `KDVT,ZUNIX,KMSP`. |
| SRN-1 | SkyRoute fixed-width navigation data format. See `srn1-format-spec.md`. |
| Trip fuel | Time enroute multiplied by the burn rate. |
| Waypoint (`WP`) | Named point with no facility. All waypoints in the training data are fictional. |
