import unittest
from textwrap import dedent
from pydetector.ast_checks import check_ast

PYVERIDX = 0
PY2AST   = 1
PY3AST   = 2
PY2ERR   = 3
PY3ERR   = 4


class Test10Ast(unittest.TestCase):
    # XXX check errors here in res[3] and res[4]
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


if __name__ == '__main__':
    unittest.main()
