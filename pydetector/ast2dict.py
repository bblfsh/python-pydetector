"""
Export an improved version of the Python AST for the given codestr
as a Python Dictionary or JSON object
"""

from __future__ import print_function

import ast
import sys
from collections import Sequence
from six import string_types

__all__ = ["ast2dict"]


def ast2dict(codestr):
    """ Returns the AST as a Python dictionary """
    visitor = DictExportVisitor(codestr)
    return visitor.parse()


class DictExportVisitor(object):

    def __init__(self, codestr, ast_parser=ast.parse):
        self.codestr = codestr

    def _nodedict(self, node, newdict, ast_type=None):
        # Adds ast_type (if not specified), lineno and col_offset to the
        # node-derived dictionary
        if ast_type is None:
            ast_type = node.__class__.__name__

        newdict["ast_type"] = ast_type
        if hasattr(node, "lineno"):
            newdict["lineno"] = node.lineno

        if hasattr(node, "col_offset"):
            newdict["col_offset"] = node.col_offset

        newdict["_fields"] = getattr(node, "_fields", [])
        newdict["_attributes"] = getattr(node, "_attributes", [])
        return newdict

    def parse(self):
        tree = ast.parse(self.codestr, mode='exec')
        res = self.visit(tree, root=True)
        return res

    def visit(self, node, root=False):
        if isinstance(node, string_types) or \
                (not isinstance(node, Sequence) and
                 not isinstance(node, ast.AST)):
            return node

        nodedict = self._nodedict(node, {}, ast_type=node.__class__.__name__)

        for field in nodedict["_fields"]:
            nodedict[field] = self.visit_field(getattr(node, field))

        return nodedict

    def visit_field(self, node):
        if isinstance(node, ast.AST):
            return self.visit(node)
        elif isinstance(node, list) or isinstance(node, tuple):
            return [self.visit(x) for x in node]
        else:
            return node


if __name__ == '__main__':
    # for manual tests

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as codefile:
            content = codefile.read()
    else:
        content = \
'''if True:
    if False:
        a = 6 + 7
    else:
        print('LAST')

'''

    print(ast2dict(content))
