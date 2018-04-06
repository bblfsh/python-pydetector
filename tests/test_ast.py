import unittest
import _ast
from textwrap import dedent
from pydetector.ast_checks import check_ast

PYVERIDX = 0
PY2AST   = 1
PY3AST   = 2
PY2ERR   = 3
PY3ERR   = 4


class Test10Ast(unittest.TestCase):
    def test_py2_ast(self):
        code = "print 'hello old world'"
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[PYVERIDX], 2)
        self.assertIsInstance(res[PY2AST], dict)
        self.assertEqual(res[PY3AST], None)
        self.assertEqual(len(res[PY2ERR]), 0)
        self.assertNotEqual(len(res[PY3ERR]), 0)

    def test_py3_ast(self):
        code = dedent("""
            import sys
            print('hello not so new world', file=sys.stderr)
        """)
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[PYVERIDX], 3)
        self.assertEqual(res[PY2AST], None)
        self.assertIsInstance(res[PY3AST], dict)
        self.assertEqual(len(res[PY3ERR]), 0)
        self.assertNotEqual(len(res[PY2ERR]), 0)

    def test_both_ast(self):
        code = "pass"
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[PYVERIDX], 6)
        self.assertIsInstance(res[PY2AST], dict)
        self.assertIsInstance(res[PY3AST], dict)
        self.assertEqual(len(res[PY3ERR]), 0)
        self.assertEqual(len(res[PY2ERR]), 0)

    def test_neither_ast(self):
        code = "Fail like a boss"
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[PYVERIDX], 0)
        self.assertEqual(res[PY2AST], None)
        self.assertEqual(res[PY3AST], None)
        self.assertNotEqual(len(res[PY3ERR]), 0)
        self.assertNotEqual(len(res[PY2ERR]), 0)


class Test20Positions(unittest.TestCase):
    def test_positions_attribute(self):
        code = "import sys\nsys.stdout.write('foo')\nprint('py2', file=sys.stderr)"
        res = check_ast(code, try_other_on_sucess=False)
        self.assertEqual(res[PYVERIDX], 3)
        self.assertEqual(len(res[PY3ERR]), 0)
        ast = res[PY3AST]
        self.assertIsInstance(ast, dict)

        self.assertEqual(ast["body"][1]['value']['args'][0]['col_offset'], 17)
        self.assertEqual(ast["body"][1]['value']['args'][0]['lineno'], 2)

        self.assertEqual(ast["body"][1]['value']['func']['col_offset'], 0)
        self.assertEqual(ast["body"][1]['value']['func']['lineno'], 2)

        self.assertEqual(ast["body"][1]['value']['func']['value']['col_offset'], 0)
        self.assertEqual(ast["body"][1]['value']['func']['value']['lineno'], 2)

        self.assertEqual(ast["body"][1]['value']['func']['value']['value']['col_offset'], 0)
        self.assertEqual(ast["body"][1]['value']['func']['value']['value']['lineno'], 2)

    def test_positions_args(self):
        code = "func(aaa, bbb)"
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[PYVERIDX], 6)
        self.assertEqual(len(res[PY3ERR]), 0)
        ast = res[PY3AST]

        self.assertEqual(ast["body"][0]["value"]["args"][0]["col_offset"], 5)
        self.assertEqual(ast["body"][0]["value"]["args"][0]["lineno"], 1)

        self.assertEqual(ast["body"][0]["value"]["args"][1]["col_offset"], 10)
        self.assertEqual(ast["body"][0]["value"]["args"][1]["lineno"], 1)

    def test_positions_fstring(self):
        code = "def func(): pass\nvar = f'Im a fstring {func()} string end'"
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[PYVERIDX], 3)
        ast = res[PY3AST]

        # f"
        self.assertEqual(ast["body"][1]["value"]["col_offset"], 6)
        self.assertEqual(ast["body"][1]["value"]["lineno"], 2)

        # "Im a fstring "
        self.assertEqual(ast["body"][1]["value"]["values"][0]["col_offset"], 6)
        self.assertEqual(ast["body"][1]["value"]["values"][0]["lineno"], 2)

        # FormattedValue node (virtual, should be the same as the child below
        self.assertEqual(ast["body"][1]["value"]["values"][1]["col_offset"], 6)
        self.assertEqual(ast["body"][1]["value"]["values"][1]["lineno"], 2)

        # func() insde the braces
        self.assertEqual(ast["body"][1]["value"]["values"][1]["value"]["col_offset"], 22)
        self.assertEqual(ast["body"][1]["value"]["values"][1]["value"]["lineno"], 2)

        # " string end"
        self.assertEqual(ast["body"][1]["value"]["values"][2]["col_offset"], 6)
        self.assertEqual(ast["body"][1]["value"]["values"][2]["lineno"], 2)


if __name__ == '__main__':
    unittest.main()
