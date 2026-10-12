#!/usr/bin/env python3
"""Resource and account naming helper implementing docs/adr/adr-0001.md.

Resource name: <region>-<account>-<env>-<service>-<id>
  region   eu-west-1 -> euw-1 (geo + direction code + "-" + number); "g" for global
  account  floor(sum of the account-id digits / number of accounts), default 3
  env      dev | lab | prod | shared
  service  main service plus optional sub-objects joined by "_", e.g. ec2_sg
  id       7 base36 characters from a full-period LCG, persisted in a state file

Subcommands: name, validate, account. Standard library only.

Keep a registry of issued names by appending the --json output:
  naming.py name ... --json >> scripts/registry.jsonl
"""
import argparse
import fcntl
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

ENVS = ("dev", "lab", "prod", "shared")
DIRECTIONS = {"north": "n", "south": "s", "east": "e", "west": "w", "central": "c",
              "northeast": "ne", "southeast": "se"}
NO_UNDERSCORE = ("s3", "rds", "alb", "nlb", "tg")  # services that forbid '_' in names
DEFAULT_ACCOUNTS = 3
ID_LEN = 7
BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"

# LCG over m = 36**ID_LEN. Hull-Dobell for full period: c coprime to m (odd, not a
# multiple of 3), a-1 divisible by every prime factor of m (2, 3) and by 4.
# Full period means no id repeats until all 36**ID_LEN values are used.
LCG_M = 36**ID_LEN
LCG_A = 148141
LCG_C = 1013904223
DEFAULT_STATE = Path(__file__).with_name(".naming-state.json")

REGION_RE = re.compile(r"^([a-z]{2})-(%s)-(\d+)$" % "|".join(DIRECTIONS))
NAME_RE = re.compile(
    r"^(?P<region>[a-z]{2}(?:ne|se|[nsewc])-\d+|g)-(?P<account>\d+)-(?P<env>dev|lab|prod|shared)"
    r"-(?P<service>[a-z0-9]+(?:_[a-z0-9]+)*)-(?P<id>[0-9a-z]{%d})$" % ID_LEN
)


def die(msg):
    sys.exit(f"error: {msg}")


def abbreviate_region(region):
    m = REGION_RE.match(region)
    if not m:
        die(f"cannot abbreviate region '{region}' (expected <geo>-<direction>-<n>)")
    geo, direction, num = m.groups()
    return f"{geo}{DIRECTIONS[direction]}-{num}"


def account_index(account_id, count):
    if not re.fullmatch(r"\d{12}", account_id):
        die("account id must be 12 digits")
    if count < 1:
        die("number of accounts must be >= 1")
    return sum(int(d) for d in account_id) // count


def to_base36(n):
    out = ""
    for _ in range(ID_LEN):
        n, r = divmod(n, 36)
        out = BASE36[r] + out
    return out


def next_id(state_path, advance=True):
    """Return the next LCG id. The state file is locked so parallel runs cannot collide."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        raw = fh.read().strip()
        value = json.loads(raw)["value"] if raw else 0
        value = (LCG_A * value + LCG_C) % LCG_M
        if advance:
            # Write in place while holding the lock. Replacing the file with a new
            # inode would let a waiting process read the old, stale value.
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps({"value": value}) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return to_base36(value)


def cmd_name(args):
    if args.service and not re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", args.service):
        die("service must be lowercase alphanumerics joined by '_', e.g. ec2_sg")
    if "_" in args.service and args.service.split("_")[0] in NO_UNDERSCORE:
        die(f"'{args.service.split('_')[0]}' forbids underscores: drop the '_' (see ADR 0001)")
    if args.is_global == bool(args.region):
        die("give exactly one of --region or --global")
    region = "g" if args.is_global else abbreviate_region(args.region)
    acct = account_index(args.account, args.accounts)
    uid = next_id(Path(args.state), advance=not args.dry_run)
    name = f"{region}-{acct}-{args.env}-{args.service}-{uid}"
    if args.json:
        print(json.dumps({"ResourceId": name, "id": uid}))
    else:
        print(name)


def cmd_validate(args):
    bad = 0
    for name in args.names:
        m = NAME_RE.match(name)
        print(("OK   " if m else "FAIL ") + name)
        bad += not m
    return 1 if bad else 0


def cmd_account(args):
    def clean(s):
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z]", "", s.lower())

    first, last = clean(args.first), clean(args.last)
    if not first or not last:
        die("first and last name must contain letters")
    prefix = "a" if args.role == "admin" else "s"
    print(f"{prefix}-{first[0]}{last[:6]}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("name", help="generate a resource name")
    n.add_argument("--region", help="e.g. eu-west-1")
    n.add_argument("--global", dest="is_global", action="store_true", help="global resource (region becomes 'g')")
    n.add_argument("--account", default=os.environ.get("AWS_ACCOUNT_ID", ""), help="12-digit account id (or AWS_ACCOUNT_ID)")
    n.add_argument("--accounts", type=int, default=DEFAULT_ACCOUNTS, help="number of accounts (default 3)")
    n.add_argument("--env", required=True, choices=ENVS)
    n.add_argument("--service", required=True, help="e.g. s3, ec2_sg")
    n.add_argument("--state", default=str(DEFAULT_STATE), help="LCG state file (commit it so ids stay unique)")
    n.add_argument("--dry-run", action="store_true", help="do not advance the id counter")
    n.add_argument("--json", action="store_true", help='print one JSON line {"ResourceId": name, "id": id} instead of the name')
    n.set_defaults(fn=cmd_name)

    v = sub.add_parser("validate", help="check names against the ADR pattern")
    v.add_argument("names", nargs="+")
    v.set_defaults(fn=cmd_validate)

    a = sub.add_parser("account", help="derive an account (user) name")
    a.add_argument("--first", required=True)
    a.add_argument("--last", required=True)
    a.add_argument("--role", required=True, choices=("admin", "standard"))
    a.set_defaults(fn=cmd_account)

    args = p.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
