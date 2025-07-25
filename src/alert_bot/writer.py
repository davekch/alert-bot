import argparse
from datetime import datetime
import json
import os
import sys

from alert_bot import load_config, make_fifo


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--subject")
    parser.add_argument("-b", "--body")
    parser.add_argument("-t", "--to")
    parser.add_argument("--handlers", nargs="*", default=[])
    return parser.parse_args()


def main() -> None:
    args = get_args()
    config = load_config()
    fifo_path = make_fifo(config)

    # check if invoked with pipe
    has_stdin = not os.isatty(sys.stdin.fileno())
    if has_stdin and args.body:
        print("ERROR: can only receive input from one source: either --body or pipe")
        return
    elif not has_stdin and not args.body:
        print("ERROR: must receive at least one input: either --body or pipe")
        return
    elif has_stdin:
        input = sys.stdin
    else:
        input = args.body.splitlines()

    common_message = {
        "subject": args.subject,
        "handlers": args.handlers,
    }
    with fifo_path.open("w") as fifo:
        for line in input:
            fifo.write(
                json.dumps(
                    common_message | {
                        "body": line.strip(),
                        "timestamp": datetime.now().isoformat()
                    }
                ) + "\n"
            )
            fifo.flush()


if __name__ == "__main__":
    main()
