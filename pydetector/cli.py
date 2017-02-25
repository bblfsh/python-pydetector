import sys
import argparse
import subprocess
from pprint import pprint
from pydetector.detector import detect

def parse_args():
    # TODO: add arguments for python executables
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

    parser.add_argument("-A", "--showast", action="store_true", default=False,
            help="Include the parsed AST")

    parser.add_argument("files", nargs=argparse.REMAINDER, help="Files to parse")

    args = parser.parse_args()

    if not args.files:
        print('List of files to operate on missing')
        parser.print_help()
        exit(1)

    if args.testast and args.verbosity > 0:
        PYMAJOR_CURRENT = sys.version_info[0]
        PYMAJOR_OTHER = 2 if PYMAJOR_CURRENT == 3 else 3
        if args.verbosity:
            print('Running under Python%d, Python%d will be used for the '
                   % (PYMAJOR_CURRENT, PYMAJOR_OTHER) + 'alternative AST tests.')

        # Test that the other Python version have pydetect installed
        try:
            # TODO: change the python exec when I implement the option
            # to specify the interpreter paths
            subprocess.check_call(['python%d' % PYMAJOR_OTHER, '-c',
                'from pydetector import ast_checks'])
        except subprocess.CalledProcess:
            print('Error: AST checks enabled but pydetector is not installed for ' +
                    'Python%d.\nPlease install it and try again or disable AST checks'
                    % PYMAJOR_OTHER)

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

    if not args.showast:
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
