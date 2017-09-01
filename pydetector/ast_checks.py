import os
import ast
import sys
import subprocess
from traceback import format_exc
sys.path.insert(0, os.path.abspath(os.pardir))
from pydetector.ast2dict import ast2dict  # noqa: E402

__all__ = ['check_ast']

# This will store the AST to use for the "other" Python. It will be
# loaded the first time its tested by getOtherPythonAstEngine
OTHERPYTHON_AST = None

if sys.version_info[0] not in (2, 3):
    raise Exception('Sorry, only python 2 and 3 is supported')
PYMAJOR_CURRENT = sys.version_info[0]
PYMAJOR_OTHER = 2 if PYMAJOR_CURRENT == 3 else 3


def check_ast(code, try_other_on_sucess=False, verbosity=0,
              py2_exec='python2', py3_exec='python3'):
    """
    Try with the ast.parse of both Python 2 and 3 and then
    iterate over the retrieved AST to find specific syntax elements.

    Args:
        code (str) the source code to extract the AST for.

        try_other_on_sucess (bool): if the AST parser of the Python version that is
            running this script work try anyway with the other interpreter (True) or
            not (False). Please note that enabling this will usually increase a lot
            the "detection" rate of files as the version of the current interpreter.

        verbosity (int): level from 0 to 2. > 1 will show exceptions when parsing
            the AST.

        py2_exec (str): path or name (if in PATH) of the Python 2 interpreter when running
            this under Python 3.

        py3_exec (str): path or name (if in PATH) of the Python 3 interpreter to use when
            running this under Python 2.
    """

    current_ok = other_ok = False
    current_ast = other_ast = None
    py2_error = py3_error = current_error = other_error = ""

    pyexec_other = py2_exec if PYMAJOR_OTHER == 2 else py3_exec

    try:
        current_ast = ast2dict(code)
        current_ok = True
    except:
        # current_ok remains false
        current_error = format_exc()
        if verbosity > 1:
            print('>>>> ASTCHECK: exception while parsing AST with Python%d:\n%s\n<<<< exception output end'
                  % (PYMAJOR_CURRENT, current_error))

    if verbosity:
        print('AST extractable with version %d?: %s' % (PYMAJOR_CURRENT, str(current_ok)))

    if not current_ok or try_other_on_sucess:
        # Open an external interpreter and try to export its AST
        cmd = [pyexec_other, "-c",
               "import ast,pydetector.ast2dict,sys;"
               "r=sys.stdin.read();"
               "print(pydetector.ast2dict.ast2dict(r))"]

        if verbosity > 1:
            print('Running in other Python:\n%s' % ' '.join(cmd))

        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate(code.encode('utf-8'))
            if p.returncode == 0:
                if PYMAJOR_CURRENT == 3:
                    out = out.decode('utf-8')
                other_ast = ast.literal_eval(out)
                other_ok = True
            else:
                other_error = err
                if verbosity > 1:
                    print('>>>> ASTCHECK: error while parsing AST with Python%d:\n%s\n<<<< error output end'
                          % (PYMAJOR_OTHER, err))
        except:
            print(format_exc())  # XXX
            other_ok = False
            other_error = format_exc()
            if verbosity > 1:
                print('>>>> ASTCHECK: exception while parsing AST with Python%d:\n%s\n<<<< exception output end'
                      % (PYMAJOR_OTHER, other_error))

    if verbosity:
        print('AST extractable with version %d?: %s' % (PYMAJOR_OTHER, str(other_ok)))

    if PYMAJOR_CURRENT == 2:
        py2_ast   = current_ast
        py2_error = current_error
        py3_ast   = other_ast
        py3_error = other_error
    else:
        py3_ast   = current_ast
        py3_error = current_error
        py2_ast   = other_ast
        py2_error = other_error

    version = 0
    if current_ok and not other_ok:
        version = PYMAJOR_CURRENT
    elif other_ok and not current_ok:
        version = PYMAJOR_OTHER
    elif current_ok and other_ok:
        version = 6

    return version, py2_ast, py3_ast, py2_error, py3_error
