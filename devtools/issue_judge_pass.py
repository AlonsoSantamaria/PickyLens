"""Operator-only pass issuance. Save the printed code privately; never commit it."""
import argparse
import os
from app.services.judge_access import JudgeAccess

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--operations', type=int, default=30)
    parser.add_argument('--hours', type=float, default=72)
    args = parser.parse_args()
    access = JudgeAccess(os.environ.get('PICKYLENS_ACCESS_DB','data/judge-access.sqlite3'),
                         int(os.environ.get('PICKYLENS_GLOBAL_OPERATIONS','200')))
    print(access.issue(args.operations, args.hours))
