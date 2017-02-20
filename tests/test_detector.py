import unittest
from textwrap import dedent
from pydetector.detector import remove_str_comments, detect


class Test20Detect(unittest.TestCase):
    def _check_res(self, res, version, score=None, ast2check=False, ast3check=False):
        self.assertEqual(res['version'], version)

        if score:
            self.assertEqual(res['score'], score)

        if ast2check:
            self.assertIsNotNone(res['py2ast'])
        if ast3check:
            self.assertIsNotNone(res['py3ast'])


    def test_detect_py2(self):
        code = "print 'old'"
        self._check_res(
                detect(codestr=code, modsyms_checks=True)['<code_string>'],
                version=2, ast2check=True
        )

    def test_detect_py3(self):
        code = dedent("""
            import sys
            print('new', file=sys.stderr)
            def func(arg1, arg2, arg3):
                print(arg1, arg2, arg3)
            func(1, 2, 3)
        """)
        self._check_res(
                detect(codestr=code, modsyms_checks=True)['<code_string>'],
                version=3, ast3check=True
        )

    def test_detect_both(self):
        with open(__file__) as this:
            code = this.read()

        self._check_res(
                detect(codestr=code, modsyms_checks=True)['<code_string>'],
                version=6, ast2check=True, ast3check=True
        )

class Test10RemoveStrComments(unittest.TestCase):
    def test_remove_comment(self):
        code = "# Yep, this is a comment \na = 1"
        self.assertEqual(remove_str_comments(code), "\na = 1")

    def test_remove_comment_whitespace(self):
        code = "   # Yep, another comment   \na = 1"
        self.assertEqual(remove_str_comments(code), "   \na = 1")

    def test_remove_comment_mixed(self):
        code = "b = 2 # set b to two (dont do this please)"
        self.assertEqual(remove_str_comments(code), "b = 2 ")

    def test_remove_anidated_comment(self):
        code = "a = 1 # first comment # inside comment"
        self.assertEqual(remove_str_comments(code), "a = 1 ")

    def test_remove_simple_str(self):
        code = 'print("with some string")'
        self.assertEqual(remove_str_comments(code), "print('')")
        code = "print('with some string')"
        self.assertEqual(remove_str_comments(code), "print('')")

    def test_remove_str_inside(self):
        code = '''print("with some string 'with another inside' outside")'''
        self.assertEqual(remove_str_comments(code), "print('')")

    def test_remove_str_inside2(self):
        code = r'''print("with some string \'with another inside\' outside")'''
        self.assertEqual(remove_str_comments(code), "print('')")

    def test_remove_str_escaped(self):
        code = r'a = \"; b = \"'
        self.assertEqual(remove_str_comments(code), code)

    def test_remove_str_triple(self):
        code = '''triple = """
            some stuff
            inside and
            multiline"""; b = 3'''
        result = "triple = ''; b = 3"
        self.assertEqual(remove_str_comments(code), result)


if __name__ == '__main__':
    unittest.main()
