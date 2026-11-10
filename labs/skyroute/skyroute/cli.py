"""Command line interface: python -m skyroute plan|export ..."""

import argparse
import sys

from skyroute.fuel import DEFAULT_CONTINGENCY_PCT, DEFAULT_RESERVE_MIN, plan_fuel
from skyroute.report import DEFAULT_OUT, archive, export, format_plan, parse_altitude
from skyroute.route import Route


def _add_plan_args(parser):
    parser.add_argument("--route", required=True,
                        help="comma-separated fix idents, for example KDVT,ZUNIX,KMSP")
    parser.add_argument("--gs", type=float, required=True, help="ground speed in knots")
    parser.add_argument("--burn", type=float, required=True, help="fuel burn in lb per hour")
    parser.add_argument("--alt", help="cruise altitude, for example FL350 or 12500")
    parser.add_argument("--contingency", type=float, default=DEFAULT_CONTINGENCY_PCT,
                        help="contingency fuel percent (default %(default)s)")
    parser.add_argument("--reserve-min", type=float, default=DEFAULT_RESERVE_MIN,
                        help="final reserve in minutes (default %(default)s)")
    parser.add_argument("--navdata", help="path to an SRN-1 file (default: data/navdata.srn)")


def build_parser():
    parser = argparse.ArgumentParser(prog="skyroute", description="SkyRoute flight planner")
    sub = parser.add_subparsers(dest="command", required=True)

    _add_plan_args(sub.add_parser("plan", help="print a flight plan"))

    exp = sub.add_parser("export", help="write a flight plan to a file")
    _add_plan_args(exp)
    exp.add_argument("--name", required=True, help="report name, written as <name>.txt")
    exp.add_argument("--out", default=DEFAULT_OUT, help="output directory (default %(default)s)")
    exp.add_argument("--archive", action="store_true", help="also write <name>.tar.gz")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        route = Route.from_idents(args.route.split(","), args.navdata)
        fuel = plan_fuel(route.ete_hours(args.gs), args.burn,
                         args.contingency, args.reserve_min)
        altitude = parse_altitude(args.alt) if args.alt else None
        text = format_plan(route, fuel, args.gs, altitude)

        if args.command == "plan":
            print(text, end="")
            return 0

        print("wrote " + export(text, args.name, args.out))
        if args.archive:
            print("wrote " + archive(args.name, args.out))
        return 0
    except (OSError, ValueError) as exc:
        print(f"skyroute: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
