"""For testing stdout and stderr."""

import sys


def main() -> None:
    """For testing stdout and stderr."""
    count = 0
    total_number_of_std = 2
    while True:
        count = count + 1
        if count % 1 == 0:
            print("stdout")
        # On Windows with Python 3.9, it seems to block the output of stdout
        # when same amount of stderr is output.
        if count % total_number_of_std == 0:
            print("stderr", file=sys.stderr)
        if count >= total_number_of_std:
            count = 0


if __name__ == "__main__":
    main()
