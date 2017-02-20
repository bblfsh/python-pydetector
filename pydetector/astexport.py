# This module uses (modified) code from:
# https://github.com/fpoli/python-astexport/blob/master/astexport/export.py
# Hosted at: https://github.com/edreamleo/python-to-coffeescript

# Released under the MIT License.

import ast
import sys
import json
import types
import tokenize
import token as token_module

isPython3 = sys.version_info >= (3, 0, 0)

def export_dict(codestr):
    visitor = DictExportVisitor(codestr)
    return visitor.parse()

def export_json(codestr, pretty_print=False):
    return json.dumps(
        export_dict(codestr),
        indent=2 if pretty_print else 0,
        ensure_ascii=False
    )

try:
    import msgpack
except ImportError:
    pass
else:
    def export_msgpack(codestr):
        return msgpack.packb(export_dict(codestr))


class TokenSync(object):
    '''A class to sync and remember tokens.'''

    def __init__(self, codestr):
        '''Ctor for TokenSync class.'''
        tokens = list(
                tokenize.generate_tokens(ReadLinesClass(codestr).next)
        )

        self.s = codestr
        self.first_leading_line = None
        self.lines = [z.rstrip() for z in TokenSync.splitLines(codestr)]
        # Order is important from here on...
        self.nl_token = self.make_nl_token()
        self.line_tokens = self.make_line_tokens(tokens)
        self.blank_lines = self.make_blank_lines()
        self.string_tokens = self.make_string_tokens()
        self.ignored_lines = self.make_ignored_lines()

    @staticmethod
    def splitLines(s):
        '''Split s into lines, preserving trailing newlines.'''
        return s.splitlines(True) if s else []

    @staticmethod
    def isString(s):
        '''Return True if s is any string, but not bytes.'''
        if isPython3:
            return isinstance(s, str)
        else:
            return isinstance(s, types.StringTypes)

    @staticmethod
    def isUnicode(s):
        '''Return True if s is a unicode string.'''
        # pylint: disable=no-member
        if isPython3:
            return isinstance(s, str)
        else:
            return isinstance(s, types.UnicodeType)

    @staticmethod
    def toUnicode(s, encoding='utf-8', reportErrors=False):
        '''Connvert a non-unicode string with the given encoding to unicode.'''
        if isPython3:
            def u(s):
                return s

            def ue(s, encoding):
                return s if TokenSync.isUnicode(s) else str(s, encoding)
        else:
            def u(s):
                return unicode(s) # noqa: F821

            def ue(s, encoding):
                return unicode(s, encoding) # noqa: F821

        trace = False
        if TokenSync.isUnicode(s):
            return s
        if not encoding:
            encoding = 'utf-8'
        try:
            s = s.decode(encoding, 'strict')
        except UnicodeError:
            s = s.decode(encoding, 'replace')
            if trace or reportErrors:
                print("toUnicode: Error converting %s... from %s encoding to unicode" % (
                    s[: 200], encoding))
        except AttributeError:
            if trace:
                print('toUnicode: AttributeError!: %s' % s)
            s = u(s)
        if trace and encoding == 'cp1252':
            print('toUnicode: returns %s' % s)
        return s

    def make_blank_lines(self):
        '''Return of list of line numbers of blank lines.'''
        result = []
        for i, aList in enumerate(self.line_tokens):
            # if any([self.token_kind(z) == 'nl' for z in aList]):
            if len(aList) == 1 and self.token_kind(aList[0]) == 'nl':
                result.append(i)
        return result

    def make_ignored_lines(self):
        '''
        Return a copy of line_tokens containing ignored lines,
        that is, full-line comments or blank lines.
        These are the lines returned by leading_lines().
        '''
        result = []
        for i, aList in enumerate(self.line_tokens):
            for z in aList:
                if self.is_line_comment(z):
                    result.append(z)
                    break
            else:
                if i in self.blank_lines:
                    result.append(self.nl_token)
                else:
                    result.append(None)
        assert len(result) == len(self.line_tokens)
        for i, aList in enumerate(result):
            if aList:
                self.first_leading_line = i
                break
        else:
            self.first_leading_line = len(result)
        return result

    def make_line_tokens(self, tokens):
        '''
        Return a list of lists of tokens for each list in self.lines.
        The strings in self.lines may end in a backslash, so care is needed.
        '''
        n, result = len(self.lines), []
        for i in range(0, n+1):
            result.append([])
        for token in tokens:
            t1, t2, t3, t4, t5 = token
            kind = token_module.tok_name[t1].lower()
            srow, scol = t3
            erow, ecol = t4
            line = erow-1 if kind == 'string' else srow-1
            result[line].append(token)
        assert len(self.lines) + 1 == len(result), len(result)
        return result

    def make_nl_token(self):
        '''Return a newline token with '\n' as both val and raw_val.'''
        t1 = token_module.NEWLINE
        t2 = '\n'
        t3 = (0, 0) # Not used.
        t4 = (0, 0) # Not used.
        t5 = '\n'
        return t1, t2, t3, t4, t5

    def make_string_tokens(self):
        '''Return a copy of line_tokens containing only string tokens.'''
        result = []
        for aList in self.line_tokens:
            result.append([z for z in aList if self.token_kind(z) == 'string'])
        assert len(result) == len(self.line_tokens)
        return result

    # TODO: call this check?
    def check_strings(self):
        '''Check that all strings have been consumed.'''
        for i, aList in enumerate(self.string_tokens):
            if aList:
                for z in aList:
                    print(self.dump_token(z))

    def dump_token(self, token, verbose=False):
        '''Dump the token. It is either a string or a 5-tuple.'''
        if TokenSync.isString(token):
            return token
        else:
            t1, t2, t3, t4, t5 = token
            kind = TokenSync.toUnicode(token_module.tok_name[t1].lower())
            val = TokenSync.toUnicode(t2)
            if verbose:
                return 'token: %10s %r' % (kind, val)
            else:
                return val

    def is_line_comment(self, token):
        '''Return True if the token represents a full-line comment.'''
        t1, t2, t3, t4, t5 = token
        kind = token_module.tok_name[t1].lower()
        raw_val = t5
        return kind == 'comment' and raw_val.lstrip().startswith('#')

    def leading_lines(self, node):
        '''Return a list of the preceding comment and blank lines'''
        # This can be called on arbitrary nodes.
        leading = []
        if hasattr(node, 'lineno'):
            i, n = self.first_leading_line, node.lineno
            while i < n:
                token = self.ignored_lines[i]
                if token:
                    s = self.token_raw_val(token).rstrip()+'\n'
                    leading.append(s)
                i += 1
            self.first_leading_line = i
        return leading

    def leading_string(self, node):
        '''Return a string containing all lines preceding node.'''
        return ''.join(self.leading_lines(node))

    def token_kind(self, token):
        '''Return the token's type.'''
        t1, t2, t3, t4, t5 = token
        return TokenSync.toUnicode(token_module.tok_name[t1].lower())

    def token_raw_val(self, token):
        '''Return the value of the token.'''
        t1, t2, t3, t4, t5 = token
        return TokenSync.toUnicode(t5)

    def token_val(self, token):
        '''Return the raw value of the token.'''
        t1, t2, t3, t4, t5 = token
        return TokenSync.toUnicode(t2)

    def trailing_comment(self, node):
        '''
        Return a string containing the trailing comment for the node, if any.
        The string always ends with a newline.
        '''
        if hasattr(node, 'lineno'):
            return self.trailing_comment_at_lineno(node.lineno)
        else:
            return '\n'

    def trailing_comment_at_lineno(self, lineno):
        '''Return any trailing comment at the given node.lineno.'''
        tokens = self.line_tokens[lineno-1]
        for token in tokens:
            if self.token_kind(token) == 'comment':
                raw_val = self.token_raw_val(token).rstrip()
                if not raw_val.strip().startswith('#'):
                    val = self.token_val(token).rstrip()
                    s = ' %s\n' % val
                    return s
        return '\n'

    def trailing_lines(self):
        '''return any remaining ignored lines.'''
        trailing = []
        i = self.first_leading_line
        while i < len(self.ignored_lines):
            token = self.ignored_lines[i]
            if token:
                s = self.token_raw_val(token).rstrip()+'\n'
                trailing.append(s)
            i += 1
        self.first_leading_line = i
        return trailing

class ReadLinesClass:
    """A class whose next method provides a readline method for Python's tokenize module."""

    def __init__(self, s):
        self.lines = s.splitlines(True) if s else []
        self.i = 0

    def next(self):
        if self.i < len(self.lines):
            line = self.lines[self.i]
            self.i += 1
        else:
            line = ''
        return line

    __next__ = next

class DictExportVisitor(object):
    ast_type_field = "ast_type"

    def __init__(self, codestr, ast_parser = ast.parse, tsync_class=TokenSync):
        """
        Initialize the Token Syncer composited object, parse the source code
        and start visiting the node tree to add comments and other modifications

        Args:
            codestr (string): the string with the source code to parse and visit.

            ast_parser (function, optional): the AST parser function to use. It needs to take
            a string with the code as parameter. By default it will be ast.parse from stdlib.

            tsync_class (class, optional): the class to use to sinchronize the tokenizer with
            the AST visits. This is needed to extract aditional info like comments that most
            AST parsers doesn't include in the tree. This class need to provide the public
            methods "leading_lines", "leading_string", "trailing_comment", "trailing_lines"
            and "sync_strings". By default astexport.TokenSync will be used.
        """
        # Instantiate the TSyncClass
        self.codestr = codestr
        self.sync = tsync_class(codestr)

    def parse(self):
        node = ast.parse(self.codestr, mode='exec')
        res = self.visit(node)
        self.sync.check_strings()
        return res

    def visit(self, node):
        node_type = node.__class__.__name__
        # print('XXX node_type: {}'.format(node_type))
        meth = getattr(self, "visit_" + node_type, self.default_visit)
        return meth(node)

    def default_visit(self, node):
        node_type = node.__class__.__name__
        # print('XXX node_type: {}'.format(node_type))
        # Add node type
        args = {
            self.ast_type_field: node_type
        }

        # Visit fields
        for field in node._fields:
            meth = getattr(
                self, "visit_field_" + node_type,
                self.default_visit_field
            )
            args[field] = meth(getattr(node, field))

        # Visit attributes
        for attr in node._attributes:
            meth = getattr(
                self, "visit_attribute_" + node_type + "_" + attr,
                self.default_visit_field
            )
            # Use None as default when lineno/col_offset are not set
            args[attr] = meth(getattr(node, attr, None))
        return args

    def default_visit_field(self, node):
        node_type = node.__class__.__name__
        # print('XXX [visit_field] node_type: {}'.format(node_type))

        if isinstance(node, ast.AST):
            return self.visit(node)
        elif isinstance(node, list) or isinstance(node, tuple):
            return [self.visit(x) for x in node]
        else:
            return node

    def visit_str(self, node):
        node_type = node.__class__.__name__
        # print('XXX [visit_str] node_type: {}'.format(node_type))
        return self.visit_Str(node)

    def visit_Str(self, node):
        node_type = node.__class__.__name__
        # print('XXX [visit_Str] node_type: {}'.format(node_type))
        return {
                self.ast_type_field: "str",
                "s": node.s
        }

    def visit_Bytes(self, node):
        node_type = node.__class__.__name__
        # print('XXX [visit_Bytes] node_type: {}'.format(node_type))
        return {
                self.ast_type_field: "bytes",
                "s": node.s.decode()
        }

    def visit_NoneType(self, node):
        node_type = node.__class__.__name__
        # print('XXX [visit_NoneType] node_type: {}'.format(node_type))
        return 'None'

    def visit_field_NameConstant(self, node):
        node_type = node.__class__.__name__
        # print('XXX [visit_field_NameConstant] node_type: {}'.format(node_type))

        if hasattr(node, 'value') and isinstance(node.value, bool):
            return {
                    self.ast_type_field: "bool",
                    "b": node.value
            }
        return str(node)

    def visit_field_Num(self, node):
        node_type = node.__class__.__name__
        # print('XXX [visit_field_Num] node_type: {}'.format(node_type))

        if isinstance(node, int):
            return {
                self.ast_type_field: "int",
                "n": node
            }
        elif isinstance(node, float):
            return {
                self.ast_type_field: "float",
                "n": node
            }
        elif isinstance(node, complex):
            return {
                self.ast_type_field: "complex",
                "n": node.real,
                "i": node.imag
            }


if __name__ == '__main__':
    import sys
    from pprint import pprint
    f = sys.argv[1]

    with open(f) as codefile:
        pprint(export_dict(codefile.read()))
