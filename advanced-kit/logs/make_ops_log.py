"""Write a synthetic SkyRoute ops log (logs/ops.log) by running real plans.

Run from the root of a SkyRoute workspace:

    python3 path/to/make_ops_log.py

The output is deterministic for a given SkyRoute version: fixed seed, fixed
start time, standard library only. Each distinct case runs once and its
result is reused, so the 400 entries take about a second. Traceback paths are
written relative to the workspace.

For class, use the committed logs/ops.log. Tracebacks differ between Python
versions, so a regenerated log can have other error lines and counts than the
ones the labs and demos expect.
"""
import datetime
import os
import random
import subprocess
import sys

CASES = [("KDVT,KESTL,KPHX", "FL085"), ("KDVT,ZUNIX,MESAS,KMSP", "FL350"),
         ("KDVT,KPHX", "FL35O"), ("KPIE,NOPE1", "12500"), ("KBFI,KMSP", "12500")]


def main():
    if not os.path.isfile(os.path.join("skyroute", "cli.py")):
        sys.exit("run this from the root of a SkyRoute workspace")
    rng = random.Random(7)
    t = datetime.datetime(2026, 10, 21, 6, 0, tzinfo=datetime.timezone.utc)
    root = os.getcwd() + os.sep
    results = {}
    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", "ops.log"), "w", encoding="utf-8") as log:
        for _ in range(400):
            route, alt = rng.choice(CASES)
            t += datetime.timedelta(seconds=rng.randint(5, 90))
            ts = t.strftime("%Y-%m-%dT%H:%M:%SZ")
            if (route, alt) not in results:
                results[(route, alt)] = subprocess.run(
                    [sys.executable, "-m", "skyroute", "plan", "--route", route,
                     "--gs", "140", "--burn", "9", "--alt", alt],
                    capture_output=True, text=True)
            p = results[(route, alt)]
            level = "INFO" if p.returncode == 0 else "ERROR"
            log.write(f"{ts} {level} plan route={route} alt={alt} rc={p.returncode}\n")
            for line in p.stderr.splitlines():
                log.write(f"{ts} ERROR   {line.replace(root, '')}\n")
    print("wrote logs/ops.log")


if __name__ == "__main__":
    main()
