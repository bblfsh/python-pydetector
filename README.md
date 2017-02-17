# PyDetector

This script/module can be used to guess if a Python source file is version 2 or 3
of the language or compatible with both. It will do a series of tests (AST
extraction, regular expressions for finding syntactic elements, modules or module
symbols) that can be enabled or disabled individually depending on how fast or how
precise you want the guessing to be. It doesn't currently use 2tolib since it's
pretty slow but it implement some of their tests with regexes). I could add it in
the future.  Or, better, you can send me a PR if you are bored enough to add it.

It it developer as a semi-independing part of
the [Babelfish](https://github.com/src-d/babelfish) project.  

```bash
usage: detector.py [-h] [-v VERBOSITY] [-d DEFAULTVERSION] [-a] [-o] [-n] [-m]
                   [-s]
                   ...

positional arguments:
  files                 Files to parse

optional arguments:
  -h, --help            show this help message and exit
  -v VERBOSITY, --verbosity VERBOSITY
                        increase output verbosity (0 to 2)
  -d DEFAULTVERSION, --defaultversion DEFAULTVERSION
                        Python version to return if there is a match. If not
                        used it will be just reported as a match
                        (default=report matches)
  -a, --testast         Do the AST extraction test (default=enabled)
  -o, --asttestboth     Do the AST test with the other version even if the
                        first one works(default=enabled)
  -n, --no-asttestboth  Do the AST test with the other version even if the
                        first one works(default=enabled)
  -m, --testmodules     Test for version-specific modules (default=enabled)
  -s, --testmodulesyms  Test for version-specific module symbols (WARNING:
                        SLOW!) (default=disabled)
```

```python
def detect(files=None, codestr=None, ast_checks=True, modules_checks=True,
        modsyms_checks=False, stop_on_ok_ast=False, modules_score=150,
        symbols_score=100, verbosity=0):
    """
    Try to detect if a source file is Python 2 or 3. It uses a combination of
    tests based on AST extraction and regular expressions.

    Args: files (List[str], optional): list of files. You can omit this parameter
    if you pass codestr.

        codestr (str, optional): source code of a single module to parse. You can
        omit this parameter if you pass "files".

        ast_checks (bool): enable checking if the AST parses with both Python
        versions

        modules_checks (bool): enable checking version-specific module imports

        modsyms_checks (bool): enable checking version-specific module symbols.
        Please note that this test can be much slower than the others.

        stop_on_ok_ast (bool): if the first AST tested works, don't even try with
        the other version

        modules_score (int): score given to specific-module matches

        symbols_score (int): score given to symbol-specific matches

        verbosity (int): verbosity level from 0 (quiet) to 2

    Return:
        Dictionary where each key is the filename and the value another dictionary
        with the keys "py2ast" and "py3ast" that will hold the AST if sucessfully
        parser for that version or "None", "version" with the version number (2 or
        3) or 6 is the module seems to be compatible with both versions, "matches"
        that will hold a list of the matched rules and scores and
        "py2_score/py3_score" with the specific score.
    """
```
