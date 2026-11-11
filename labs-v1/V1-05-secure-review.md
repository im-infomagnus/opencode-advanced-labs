# Lab 5: Secure review

**Time:** 35 min  **You will:** review `skyroute/report.py` for security bugs, verify each one, and fix two test-first.

The token in `report.py` is fake. Practise the real habit anyway: report where a secret is, never its value.

## Steps

1. **Review.** `/new`, **Plan**. Send:

   ```text
   Security review of skyroute/report.py and how skyroute/cli.py calls it.
   Treat --name, --out, --alt, and any file read as untrusted. For each finding:
   file:line, CWE ID and name, how an attacker reaches it, smallest fix.
   Do not print secret values. Use only files under labs/skyroute. Do not edit.
   ```

2. **Classify.** Fill in the line for each:

   | CWE | Name | Line in `report.py` |
   |---|---|---|
   | CWE-22 | Path traversal | |
   | CWE-78 | OS command injection | |
   | CWE-502 | Deserialization of untrusted data | |
   | CWE-95 | Eval injection | |
   | CWE-798 | Hard-coded credentials | |

   **Check:** all five rows have a line from the agent's answer. If one is missing, ask: `Look again at the constants at the top of skyroute/report.py. Is any a credential? File and line only.`

3. **Verify two yourself** in T2:

   ```bash
   python -m skyroute plan --route KDVT,KPHX --gs 120 --burn 1000 --alt "1000*35"
   python -m skyroute export --route KDVT,KPHX --gs 120 --burn 1000 --name ../escaped
   rm escaped.txt
   ```

   **Check:** the first prints `Cruise: 35000 ft` (code was evaluated). The second writes `escaped.txt` outside `out/`.

4. **Failing tests.** **Tab** to **Build**. Send:

   ```text
   Create tests/test_report.py. Do not change skyroute/.
   1. CWE-22: export("x", "../escaped", out_dir) raises ValueError and creates
      nothing outside out_dir. Use a temporary directory.
   2. CWE-95: parse_altitude("FL350") is 35000, "12500" is 12500, and
      "FL350+1" and "1000*35" raise ValueError.
   Run python -m unittest tests.test_report and say which tests fail and why.
   ```

   **Check:** attack cases fail as `FAIL`, not `ERROR`. Commit: `git add . && git commit -m "Lab 5: failing security tests"`.

5. **Fix.** Send:

   ```text
   Make tests/test_report.py pass with the smallest change to skyroute/report.py.
   No eval. Keep exports inside the output directory. Do not edit tests/.
   Run python -m unittest and show the result line.
   ```

   **Check:** `python -m unittest` ends with `OK`; `git diff --stat tests/` prints nothing. Rerun step 3: both commands now print `skyroute: error:`. Commit.

## Stretch

Fix CWE-798 the same way: read the token from `SKYROUTE_UPLOAD_TOKEN`, with a test.
