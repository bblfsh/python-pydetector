"""
Export an improved version of the Python AST for the given codestr
as a Python Dictionary or JSON object
"""
from __future__ import print_function

import ast
import tokenize
import token as token_module
from codecs import encode
from six import StringIO
# from pprint import pprint

# TODO: add an option to not change the node names of NameConstant, Num and Str


def export_dict(codestr):
    """ Returns the AST as a Python dictionary """
    visitor = DictExportVisitor(codestr)
    return visitor.parse()


def export_json(codestr, pretty_print=False):
    """ Returns the AST as a JSON object """
    import json
    dict_ = {'AST': export_dict(codestr)}
    json_ = json.dumps(dict_, indent=2 if pretty_print else 0, ensure_ascii=False)
    return json_, dict_


NAMECOUNTER = 0


def export_graphviz(codestr):
    """
    WARNING: Experimental, only compatible with Python 3 and unfinished
    """
    # TODO: use fillcolor for different ast_types
    # TODO: use shape for giving different shapes to different nodes: http://www.graphviz.org/content/node-shapes#polygon
    parent_nodekeys = {'body', 'names', 'targets', 'value', 'func', 'args', 'keywords',
                       'keys', 'left', 'right'}
    from graphviz import Graph

    # These nodes will show their childs as hanging from their parent
    def generate(dot, obj, parent=None, reparent=False):
        global NAMECOUNTER

        NAMECOUNTER += 1
        nodename = str(NAMECOUNTER)

        def get_name(node):
            subname = ''
            if isinstance(node, dict):
                ast = node.get('ast_type', '')
                subname = node.get('name', '')
                id = node.get('id', '')
                arg = node.get('arg', '')
                separator = ': ' if ast and (subname or id or arg) else ''
                name = '%s%s%s%s%s' % (ast, separator, subname, id, arg)
            else:
                name = str(type(node))
            return name, subname

        name, origname = get_name(obj)
        if reparent or type(obj) in (list, tuple):
            nodename = parent
        else:
            dot.node(nodename, label=name)
            if parent:
                dot.edge(parent, nodename)

        if isinstance(obj, dict):
            for childkey in parent_nodekeys:
                if childkey in obj:
                    reparent = childkey == 'names'
                    generate(dot, obj[childkey], nodename, reparent)

        elif isinstance(obj, list) or isinstance(obj, tuple):
            for value in obj:
                generate(dot, value, nodename)

    dict_ = export_dict(codestr),
    dot = Graph(comment="Python AST", format='pdf',
                graph_attr={'ranksep': '2.5'
                            })
    generate(dot, dict_, 'RootNode')

    with open('ast.dot', 'w') as dotfile:
        print(dot.source, file=dotfile)


TOKEN_TYPE     = 0
TOKEN_VALUE    = 1
TOKEN_STARTLOC = 2
TOKEN_ENDLOC   = 3
TOKEN_RAWVALUE = 4

ROW = 0
COL = 1

NOOP_TOKENS_LINE = {'COMMENT', 'INDENT', 'NL', 'NEWLINE'}


def _token_name(token):
    return token_module.tok_name[token[TOKEN_TYPE]]


class NoopExtractor(object):
    """
    Tokenize the source code and extract lines with tokens that Python's
    AST generator ignore like blanks and comments
    """

    def __init__(self, codestr):
        tokens = tokenize.generate_tokens(StringIO(codestr).readline)

        self.current_line = None
        self.all_lines = self._create_tokenized_lines(tokens, codestr)
        self.astmissing_lines = self._create_astmissing_lines()

        # This set is used to avoid adding the "same line-remainder noops" nodes as a child
        # of every "real" node to avoid having this node duplicated on all semantic
        # nodes in the same line, thus avoiding duplication. It will contain just the
        # line numbers of already added sameline_noops
        self._sameline_added_noops = set()

    def _create_astmissing_lines(self):
        """
        Return a copy of line_tokens containing lines ignored by the AST
        (comments and blanks-only lines)
        """
        lines = []
        nl_token = (token_module.NEWLINE, '\n', (0, 0), (0, 0), '\n')

        tname = _token_name
        for i, linetokens in enumerate(self.all_lines):
            if len(linetokens) == 1 and tname(linetokens[0]) == 'NL':
                lines.append(nl_token)
            else:
                for token in linetokens:
                    if tname(token) == 'COMMENT' and \
                            token[TOKEN_RAWVALUE].lstrip().startswith('#'):
                        lines.append(token)
                        break
                else:
                    lines.append(None)
        assert len(lines) == len(self.all_lines)

        for i, linetokens in enumerate(lines):
            if linetokens:
                self.current_line = i
                break
        else:
            self.current_line = len(lines)
        return lines

    def _create_tokenized_lines(self, tokens, codestr):
        """
        Create a list of tokenized lines
        """
        lines = codestr.splitlines() if codestr else []
        result = []
        for i in range(0, len(lines) + 1):
            result.append([])

        tname = _token_name
        for token in tokens:
            # Save noops in the line of the starting row except for strings where
            # we save it in the last line (because they can be multiline)
            if tname(token) == 'STRING':
                line = token[TOKEN_ENDLOC][ROW] - 1
            else:
                line = token[TOKEN_STARTLOC][ROW] - 1
            result[line].append(token)
        assert len(lines) + 1 == len(result), len(result)
        return result

    def previous_nooplines(self, node):
        """Return a list of the preceding comment and blank lines"""
        previous = []
        noop_first_lineno = None
        noop_last_lineno = None

        if hasattr(node, 'lineno'):
            while self.current_line < node.lineno:
                token = self.astmissing_lines[self.current_line]
                if token:
                    s = token[TOKEN_RAWVALUE].rstrip() + '\n'
                    previous.append(s)

                    # take only the first line of the noops as the start and the last
                    # one (overwriteen every iteration)
                    if not noop_first_lineno:
                        noop_first_lineno = self.current_line + 1
                    noop_last_lineno = self.current_line + 1
                self.current_line += 1
        return previous, noop_first_lineno, noop_last_lineno

    def remainder_noops_sameline(self, node):
        """
        Return a string containing the trailing (until EOL) noops for the
        node, if any. The ending newline is implicit and thus not returned
        """

        # Without a line number for the node we can't know
        if not hasattr(node, 'lineno'):
            return ''

        # Skip remainder comments already added to a node in this line to avoid every node
        # in the same line having it (which is not conceptually wrong, but not DRY)
        if node.lineno in self._sameline_added_noops:
            return ''

        # Module nodes have the remaining comments but since we put their first line as "1"
        # any comment on the first line would wrongly show as sameline comment for the module
        if node.__class__.__name__ == 'Module':
            return ''

        tokens = self.all_lines[node.lineno - 1]
        trailing = []

        tname = _token_name
        for token in tokens:
            if tname(token) not in NOOP_TOKENS_LINE:
                # restart
                trailing = []
            else:
                trailing.append({
                    'rowstart' : token[TOKEN_STARTLOC][ROW],
                    'colstart' : token[TOKEN_STARTLOC][COL],
                    'rowend'   : token[TOKEN_ENDLOC][ROW],
                    'colend'   : token[TOKEN_ENDLOC][COL],
                    'value'    : token[TOKEN_VALUE],
                    })
        if not trailing:
            return ''

        self._sameline_added_noops.add(node.lineno)
        nonewline_trailing = trailing[:-1] if trailing[-1]['value'] == '\n' else trailing
        return nonewline_trailing

    def remainder_noops(self):
        """return any remaining ignored lines."""
        trailing = []
        noop_last_lineno = None
        i = self.current_line
        noop_first_lineno = self.current_line + 1

        while i < len(self.astmissing_lines):
            token = self.astmissing_lines[i]
            if token:
                s = token[TOKEN_RAWVALUE]
                trailing.append(s)

            i += 1
            noop_last_lineno = i
        self.current_line = i
        return trailing, noop_first_lineno, noop_last_lineno


def node_dict(node, newdict, ast_type=None):
    """
    Shortcut that adds ast_type (if not specified),
    lineno and col_offset to the node-derived dictionary
    """
    if ast_type is None:
        ast_type = node.__class__.__name__

    newdict["ast_type"] = ast_type
    if hasattr(node, "lineno"):
        newdict["lineno"] = node.lineno
    if hasattr(node, "col_offset"):
        newdict["col_offset"] = node.col_offset

    return newdict


class DictExportVisitor(object):
    ast_type_field = "ast_type"

    def __init__(self, codestr, ast_parser=ast.parse, tsync_class=NoopExtractor):
        """
        Initialize the Token Syncer composited object, parse the source code
        and start visiting the node tree to add comments and other modifications

        Args:
            codestr (string): the string with the source code to parse and visit.

            ast_parser (function, optional): the AST parser function to use. It needs to take
            a string with the code as parameter. By default it will be ast.parse from stdlib.

            tsync_class (class, optional): the class to use to sinchronize the tokenizer with
            the AST visits. This is needed to extract aditional info like comments or whitespace
            that most AST parsers doesn't include in the tree. This class need to provide the public
            methods "previous_nooplines",  "remainder_noops_sameline" and "rmainder_noops".
            By default astexport.NoopExtractor will be used.
        """
        self.codestr = codestr
        self.sync = tsync_class(codestr)
        # this is used to store the parent node of the current one; currently is only
        # used to inherit the lineno and col_offset of the parent for "arguments" and
        # "Operator" types
        self._current_parent = None

    def _addNoopFields(self, node, visit_dict, root):
        if not isinstance(visit_dict, dict):
            return visit_dict

        def _create_nooplines_list(startline, noops_previous):
            nooplines = []
            curline = startline
            for noopline in noops_previous:
                nooplines.append({
                    'ast_type': 'NoopLine',
                    'noop_line': noopline,
                    'lineno': curline,
                    'col_offset': 1,
                })
                curline += 1
            return nooplines

        # Add all the noop (whitespace and comments) lines between the
        # last node and this one
        noops_previous, startline, endline = self.sync.previous_nooplines(node)
        if noops_previous:
            visit_dict['noops_previous'] = {
                "ast_type": "PreviousNoops",
                "lineno": startline,
                "col_offset": 1,
                "end_lineno": endline,
                "lines": _create_nooplines_list(startline, noops_previous)
            }

        # Other noops at the end of its significative line except the implicit
        # finishing newline
        noops_sameline = self.sync.remainder_noops_sameline(node)
        joined_sameline = ''.join([x['value'] for x in noops_sameline])
        if noops_sameline:
            visit_dict['noops_sameline'] = {
                "ast_type": "SameLineNoops",
                "lineno": node.lineno if hasattr(node, "lineno") else 0,
                "col_offset": noops_sameline[0]["colstart"],
                "col_end": noops_sameline[-1]["colend"],
                "noop_line": joined_sameline
            }

        # Finally, if this is the root node, add all noops after the last op node
        if root:
            noops_remainder, startline, endline = self.sync.remainder_noops()
            if noops_remainder:
                visit_dict['noops_remainder'] = {
                    "ast_type": "RemainderNoops",
                    "lineno": startline,
                    "col_offset": 1,
                    "end_lineno": endline,
                    "lines": _create_nooplines_list(startline, noops_remainder)
                }

    def parse(self):
        node = ast.parse(self.codestr, mode='exec')
        res = self.visit(node, root=True)
        return res

    def visit(self, node, root=False):
        node_type = node.__class__.__name__

        if node_type == 'Module':
            # add line and col since Python doesnt adds them
            node.__dict__['lineno'] = 1
            node.__dict__['col_offset'] = 0

        # the ctx property always has a "Load"/"Store"/etc nodes that
        # can be perfectly converted to a string value since they don't
        # hold anything more than the name
        if hasattr(node, 'ctx'):
            node.ctx = node.ctx.__class__.__name__

        meth = getattr(self, "visit_" + node_type, self.visit_other)
        visit_result = meth(node)
        self._addNoopFields(node, visit_result, root)

        if 'col_offset' in visit_result:
            # Python AST gives a 0 based column, I prefer a 1-based one
            visit_result['col_offset'] += 1

        return visit_result

    def visit_other(self, node):
        node_type = node.__class__.__name__
        nodedict = node_dict(node, {}, ast_type = node_type)

        # Visit fields
        for field in node._fields:
            meth = getattr(self, "visit_" + node_type, self.visit_other_field)
            nodedict[field] = meth(getattr(node, field))

            # these must inherit their position from the parent
            # FIXME: move to a method
            if field in ('args', 'op', 'ops', 'alias', 'keywords'):
                if isinstance(nodedict[field], dict):
                    toprocess = [nodedict[field]]
                elif isinstance(nodedict[field], list):
                    toprocess = nodedict[field]
                else:
                    continue

                for proc in toprocess:
                    if 'lineno' not in proc and hasattr(node, 'lineno'):
                        proc['lineno'] = node.lineno
                    # doesnt make sense to inherit col_offset since it would be different

        # Visit attributes
        for attr in node._attributes:
            meth = getattr(self, "visit_" + node_type + "_" + attr, self.visit_other_field)
            nodedict[attr] = meth(getattr(node, attr))

        return nodedict

    def visit_other_field(self, node):
        if isinstance(node, ast.AST):
            return self.visit(node)
        elif isinstance(node, list) or isinstance(node, tuple):
            return [self.visit(x) for x in node]
        else:
            # string attribute
            return node

    def visit_str(self, node):
        """
        This visits str fields inside nodes (which are represented as keys
        in the node dictionary), not Str AST nodes
        """
        return str(node)

    def visit_Str(self, node):
        return node_dict(node, {"LiteralValue": node.s}, ast_type="StringLiteral")

    def visit_Bytes(self, node):
        try:
            s = node.s.decode()
            encoding = 'utf8'
        except UnicodeDecodeError:
            # try with base64
            s = encode(node.s, 'base64').decode().strip()
            encoding = 'base64'

        return node_dict(node, {"LiteralValue": s, "encoding": encoding}, ast_type="ByteLiteral")

    def visit_NoneType(self, node):
        return 'NoneLiteral'

    def visit_Global(self, node):
        # Python AST by default stores global and nonlocal variable names
        # in a "names" array of strings. That breaks the structure of everything
        # else in the AST (dictionaries, properties or list of objects) so we
        # convert those names to Name objects

        names_as_nodes = [{"ast_type": "Name",
                          "id": i,
                          "lineno": node.lineno,
                          "col_offset": node.col_offset} for i in node.names]
        return node_dict(node, {"names": names_as_nodes}, ast_type="Global")

    def visit_Nonlocal(self, node):
        # ditto
        names_as_nodes = [{"ast_type": "Name",
                          "id": i,
                          "lineno": node.lineno,
                          "col_offset": node.col_offset} for i in node.names]
        return node_dict(node, {"names": names_as_nodes}, ast_type="Nonlocal")

    def visit_NameConstant(self, node):
        if hasattr(node, 'value'):
            repr_val = repr(node.value)
            if repr_val in ('True', 'False'):
                return node_dict(node, {"LiteralValue": node.value}, ast_type="BoolLiteral")
            elif repr_val == 'None':
                return node_dict(node, {"LiteralValue": node.value}, ast_type="NoneLiteral")
        return str(node)

    def visit_Num(self, node):
        if isinstance(node.n, int):
            ret_dict = { "NumType": "int", "LiteralValue": node.n }
        elif isinstance(node.n, float):
            ret_dict = { "NumType": "float", "LiteralValue": node.n }
        elif isinstance(node.n, complex):
            ret_dict = {
                        "NumType": "complex",
                        "LiteralValue": {"real": node.n.real, "imaginary": node.n.imag},
                       }

        return node_dict(node, ret_dict, ast_type="NumLiteral")


if __name__ == '__main__':
    import sys

    with open(sys.argv[1]) as codefile:
        content = codefile.read()

    # content = "#firstcomment\n#secondcomment\nppass #trailing comment\n#middle\n#secondmiddle\npass\n#beforelast\n#lastcomment"
    # print(content)

    # from pprint import pprint
    # pprint(export_dict(content))
    print(export_json(content, pretty_print=True)[0])
    # export_graphviz(content)
