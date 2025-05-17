import argparse
import sys

import first_run
import second_run


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compute statistics or remodel SWC files"
    )
    sub = parser.add_subparsers(dest="command")

    analyze = sub.add_parser("analyze", help="Compute morphometric statistics")
    analyze.add_argument("directory", help="Directory containing SWC files")
    analyze.add_argument("files", help="Comma separated list of file names")

    edit = sub.add_parser("edit", help="Remodel a morphology")
    edit.add_argument("--directory", required=True, help="Base directory for the SWC file")
    edit.add_argument("--file-name", required=True, help="SWC filename")
    edit.add_argument("--who", required=True, help="Target dendrite selection")
    edit.add_argument("--random-ratio", type=float, default=0.0,
                      help="Ratio for random selection (percent)")
    edit.add_argument("--who-manual-variable", default="none",
                      help="Comma separated manual dendrite ids")
    edit.add_argument("--action", required=True, help="Remodeling action")
    edit.add_argument("--hm-choice", required=True,
                      help="percent or micrometers for extent")
    edit.add_argument("--amount", type=float, default=None,
                      help="Extent of the action")
    edit.add_argument("--var-choice", required=True,
                      help="percent or micrometers for diameter change")
    edit.add_argument("--diam-change", type=float, default=None,
                      help="Extent of diameter change")

    args = parser.parse_args(argv)

    if args.command == "analyze":
        first_run.main([args.directory, args.files])
    elif args.command == "edit":
        arglist = [
            "--directory", args.directory,
            "--file-name", args.file_name,
            "--who", args.who,
            "--random-ratio", str(args.random_ratio),
            "--who-manual-variable", args.who_manual_variable,
            "--action", args.action,
            "--hm-choice", args.hm_choice,
            "--var-choice", args.var_choice,
        ]
        if args.amount is not None:
            arglist.extend(["--amount", str(args.amount)])
        if args.diam_change is not None:
            arglist.extend(["--diam-change", str(args.diam_change)])
        second_run.main(arglist)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
