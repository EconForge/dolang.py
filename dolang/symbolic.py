from .grammar import *

import ast


def eval_scalar(tree):
    try:
        if isinstance(tree, ast.Num):
            return tree.n
        elif isinstance(tree, ast.UnaryOp):
            if isinstance(tree.op, ast.USub):
                return -tree.operand.n
        else:
            raise Exception("Don't know how to do that.")
    except:
        raise Exception("Don't know how to do that.")
