import unittest
from textwrap import dedent
from pydetector.ast_checks import check_ast

class Test10Ast(unittest.TestCase):
    def test_py2_ast(self):
        code = "print 'hello old world'"
        res = check_ast(code)
        self.assertEqual(res[0], 2)
        self.assertIsInstance(res[1], dict)
        self.assertEqual(res[2], None)

    def test_py3_ast(self):
        code = dedent("""
            import sys
            print('hello not so new world', file=sys.stderr)
        """)
        res = check_ast(code)
        self.assertEqual(res[0], 3)
        self.assertEqual(res[1], None)
        self.assertIsInstance(res[2], dict)

    def test_both_ast(self):
        code = "pass"
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[0], 6)
        self.assertIsInstance(res[1], dict)
        self.assertIsInstance(res[2], dict)

    def test_neither_ast(self):
        code = "Fail like a boss"
        res = check_ast(code, try_other_on_sucess=True)
        self.assertEqual(res[0], 0)
        self.assertEqual(res[1], None)
        self.assertEqual(res[2], None)


if __name__ == '__main__':
    unittest.main()
