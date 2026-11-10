# Test conventions (tests/)

- Use `unittest` from the standard library. One behavior per test method.
- Name tests `test_<behavior>`. Assert exact expected values and show the hand calculation in a comment.
- Start every test docstring with the requirement ID it verifies, for example `"""SR-FUEL-002: contingency is a percentage of trip fuel only."""`.
- Run one module with `python3 -m unittest tests.<module>`, then the full suite with `python3 -m unittest`.
