"""For testing stdout and stderr."""
import sys


def main() -> None:
    """For testing stdout and stderr."""
    count = 0
    while True:
        count = count + 1
        if count % 1 == 0:
            print("stdout")
        # On Windows with Python 3.9, it seems to block the output of stdout
        # when same amount of stderr is output.
        if count % 2 == 0:
            print("stderr", file=sys.stderr)
        if count >= 2:
            count = 0


if __name__ == "__main__":
    main()
