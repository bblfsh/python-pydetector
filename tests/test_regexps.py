import unittest
from textwrap import dedent
from pydetector.regexp_checks import check_modules_regex, \
        check_syntax_regex, check_modulesymbols_regex


class RegexpTestCase(unittest.TestCase):
    """
    Helper class, will test the datasnippet with
    (code, py_expected_points, py3_same, num_matches)
    and check that the result is the expected one in
    points and number of matches
    """
    def do_regexp_test(self, testdata):
        matches = []
        ret = self.check_method(testdata[0], matches)
        self.assertEqual(ret[0], testdata[1])
        self.assertEqual(ret[1], testdata[2])
        self.assertEqual(len(matches), testdata[3])


class Test10SyntaxRegex(RegexpTestCase):
    def setUp(self):
        self.check_method = check_syntax_regex

    def test_exceptions_nonlocal(self):
        code = (dedent("""
            if something:
                nonlocal var
                raise SomeException() from None
            """), 0, 200, 2)
        self.do_regexp_test(code)

    def test_raise_except(self):
        code = (dedent("""
            try:
                someargo.thing()
                raise SomeException, stuff
            except SomeException, e
            """), 100, 0, 1)
        self.do_regexp_test(code)

    def test_old_print(self):
        code = (dedent("""
            print "im old"
            print("im not so old")
            """), 100, 0, 1)
        self.do_regexp_test(code)

    def test_rawinput(self):
        code = (dedent("""
            var = raw_input("tell me something:")
            """), 100, 0,  1)
        self.do_regexp_test(code)

    def test_unicode(self):
        code = (dedent("""
            someunicode = unicode(somevar);other()
            unicode()
            someunicode()
            unicode but not method
            """), 50, 0, 1)
        self.do_regexp_test(code)

    def test_iteritems(self):
        code = (dedent("""
            for item in somedict.iteritems():
                foo(item)
            """), 25, 0, 1)
        self.do_regexp_test(code)

    def test_iterkeys(self):
        code = (dedent("""
            for item in somedict.iterkeys():
                foo(item)
            """), 25, 0, 1)
        self.do_regexp_test(code)

    def test_itervalues(self):
        code = (dedent("""
            for item in somedict.itervalues():
                foo(item)
            """), 25, 0, 1)
        self.do_regexp_test(code)

    def test_xrange(self):
        code = (dedent("""
            for item in xrange(3):
                foo(item)
            """), 100, 0, 1)
        self.do_regexp_test(code)

    def test_xreadlines(self):
        code = (dedent("""
            for item in xreadlines():
                foo(item)
            """), 100, 0, 1)
        self.do_regexp_test(code)

    def test_basestring(self):
        code = (dedent("""
            if type(var) == basestring:
                foo(var)
            """), 100, 0, 1)
        self.do_regexp_test(code)

    def test_haskey(self):
        code = (dedent("""
            d = {1:2}
            if d.has_key(3):
              print("fail")
            """), 100, 0, 1)
        self.do_regexp_test(code)

    def test_metaclass(self):
        code = (dedent("""
            class NotOriginal(object):
                __metaclass__ = Singleton
            """), 100, 0, 1)
        self.do_regexp_test(code)


class Test20ModulesRegex(RegexpTestCase):
    def setUp(self):
        self.check_method = check_modules_regex

    def test_pymodules_simple(self):
        code = (dedent("""
            import something, other, mimetools, mimify # 1 double match
            def somefunc():
                import thing,compiler,blabla,collections.UserDict,pok # 1 double match
            """), 200, 0, 2)
        self.do_regexp_test(code)

    def test_pymodules_simple_multiline(self):
        code = ("b = 4; import other, mimetools, mimify # 1 double match",
                100, 0, 1)
        self.do_regexp_test(code)

    def test_py3modules_simple_multiline(self):
        code = ("b = 4; import other, urllib.parse, dbm.bsd # 1 double match",
                0, 100, 1)
        self.do_regexp_test(code)

    def test_pymodules_simple_multiline_nospace(self):
        code = ("b = 4;import other,mimetools,mimify # 1 double match",
                100, 0, 1)
        self.do_regexp_test(code)

    def test_pymodules_importfrom(self):
        code = ("from audiodev import * # 1 match", 100, 0, 1)
        self.do_regexp_test(code)

    def test_py3modules_importfrom(self):
        code = ("from queue import * # 1 match", 0, 100, 1)
        self.do_regexp_test(code)

    def test_pymodules_importfrom_multiline(self):
        code = ("a = 3; from audiodev import * # 1 match", 100, 0, 1)
        self.do_regexp_test(code)

    def test_pymodules_importfrom_multiline_nospace(self):
        code = ("a = 3;from audiodev import * # 1 match", 100, 0, 1)
        self.do_regexp_test(code)

    def test_py_modules_falsepos1(self):
        code = ("from something import htmllib # NOT match", 0, 0, 0)
        self.do_regexp_test(code)

    def test_py_modules_falsepos2(self):
        code = ("from thing.mhlib import stuff # NOT match", 0, 0, 0)
        self.do_regexp_test(code)

    def test_py_modules_falsepos3(self):
        code = ("import_multifile = doStuff() # NOT match", 0, 0, 0)
        self.do_regexp_test(code)

    def test_py_modules_falsepos4(self):
        code = ("reprlib = doStuff() # NOT match", 0, 0, 0)
        self.do_regexp_test(code)


class Test30ModuleSymbolsRegex(RegexpTestCase):
    def setUp(self):
        self.check_method = check_modulesymbols_regex

    # def test_pymodules_simple(self):
        # code = (dedent("""
            # import something, other, mimetools, mimify # 1 double match
            # def somefunc():
                # import thing,compiler,blabla,collections.UserDict,pok # 1 double match
            # """), 200, 0, 2)
        # self.do_regexp_test(code)


if __name__ == '__main__':
    unittest.main()
