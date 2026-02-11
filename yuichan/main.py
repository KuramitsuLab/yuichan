import sys

from yuichan import __version__


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(f"Yui {__version__}")
        print("Usage: yui <file>")
        return
    if argv[0] in ("-V", "--version"):
        print(f"Yui {__version__}")
        return
    filename = argv[0]
    print(f"Yui {__version__}: {filename}")


if __name__ == "__main__":
    main()
