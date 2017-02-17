from pydetector.detector import detect
from pprint import pprint

def parse_args():
    # TODO: add arguments for python executables
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", type=int, default=0,
            help="increase output verbosity (0 to 2)")

    parser.add_argument("-d", "--defaultversion", type=int, default=0,
            help="Python version to return if there is a match. If not used "
                 "it will be just reported as a match (default=report matches)")

    parser.add_argument("-a", "--testast", action="store_true", default=True,
            help="Do the AST extraction test (default=enabled)")

    parser.add_argument("-o", "--asttestboth", dest='asttestboth', action='store_true',
            help="Do the AST test with the other version even if the first one works"
                 "(default=enabled)")
    parser.add_argument("-n", "--no-asttestboth", dest='asttestboth', action='store_false',
            help="Do the AST test with the other version even if the first one works"
                 "(default=enabled)")

    parser.add_argument("-m", "--testmodules", action="store_true", default=True,
            help="Test for version-specific modules (default=enabled)")

    parser.add_argument("-s", "--testmodulesyms", action="store_true", default=False,
            help="Test for version-specific module symbols (WARNING: SLOW!) (default=disabled)")

    parser.add_argument("files", nargs=argparse.REMAINDER, help="Files to parse")

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    returndict = detect(
            args.files,
            ast_checks=args.testast,
            modules_checks=args.testmodules,
            modsyms_checks=args.testmodulesyms,
            stop_on_ok_ast=not args.asttestboth,
            verbosity=args.verbosity
            )
    for fdata in returndict:
        del returndict[fdata]['py2ast'] # not json serializable in the current form
        del returndict[fdata]['py3ast'] # not json serializable in the current form

    pprint(returndict)

    if args.verbosity:
        py2_count = py3_count = pyany_count = 0
        for key in returndict:
            version = returndict[key]['version']

            if version == 2 or (version == 6 and args.defaultversion == 2):
                py2_count += 1
            elif version == 3 or (version == 6 and args.defaultversion == 3):
                py3_count += 1
            else:
                pyany_count += 1

        print('%d files parsed, py2: %d, py3: %d any: %d' %
                (len(returndict), py2_count, py3_count, pyany_count))


if __name__ == "__main__":
    main()
