import argparse
from pathlib import Path
from .engine import scan_local
from .report import write_json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Authorized local sandbox directory")
    ap.add_argument("--out", default="privacy_findings.json")
    args = ap.parse_args()
    findings = scan_local(Path(args.root))
    write_json(findings, Path(args.out))
    print(f"Wrote {len(findings)} findings to {args.out}")

if __name__ == "__main__":
    main()
