from lark.exceptions import LarkError, UnexpectedInput, UnexpectedCharacters
from yaml import ScalarNode

import copy
import lark
from lark.tree import Tree
from lark.lexer import Token
from lark.visitors import Interpreter,  Visitor, Transformer

from functools import wraps

from typing import Tuple, Dict, Set, Union, List
Expression = Union[Tree, Token]

from dataclasses import dataclass

## the following grammar represents equations
## it recognizes variables indexed as v[t] or v[t+k] where k is an integer
## for compatibility purposes, it also recognizes v(0) as v[t] unless 
## v is a prespecified function.
## later, this compatibility feature will be turned off.

import os
DIR_PATH, this_filename = os.path.split(__file__)
DATA_PATH = os.path.join(DIR_PATH, "grammar.lark")

grammar_0 = open(DATA_PATH,'rt').read()


from lark.lark import Lark
parser = Lark(grammar_0, start=['start', 'variable', 'equation_block', 'assignment_block', 'complementarity_block'])


def parse_string(text, start=None):

    if start is None:
        start = 'start'

    if isinstance(text, ScalarNode):
        if text.tag != 'tag:yaml.org,2002:str':
        #     raise Exception(f"Don't know how to parse node {text}")
            txt = text.value
        else:
            buffer = text.end_mark.buffer
            i1 = text.start_mark.pointer
            i2 = text.end_mark.pointer
            txt = buffer[i1:i2]
            if text.style in ('>', '|'):
                txt = txt[1:]

    else:
        txt = text
    
    try:
        return parser.parse(txt, start)

    except (UnexpectedInput, UnexpectedCharacters) as e:

        if isinstance(text, ScalarNode):
            sm = text.start_mark
            # em = text.end_mark
            if text.style not in ('>', '|'):
                new_column = sm.column + e.column
                new_line = sm.line + e.line
            else:
                new_line = sm.line + e.line
                new_column = e.column
            newargs = list(e.args)
            newargs[0] = e.args[0].replace(f"line {e.line}", f"line {new_line}")
            newargs[0] = newargs[0].replace(f"col {e.column}", f"col {new_column}")
            e.args = tuple(newargs)
            e.line = new_line
            e.column = new_column

        raise e


# Prints a tree as a string
# WIP!!! (probably correct, but way too many parentheses)
class Printer(Interpreter):
    def add(self, tree):
        if len(tree.children) ==1:
            return "ERROR"
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        return f"{a} + {b}"
    def sub(self, tree):
        if len(tree.children) ==1:
            return "ERROR"
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        return f"{a} - ({b})"

    def variable(self, tree):
        name = tree.children[0].children[0].value

        # is there a subperiod?
        subperiod = [c for c in tree.children if (isinstance(c,Tree) and c.data=='subperiod')]
        if len(subperiod)==1:
            sp = subperiod[0].children[0].value
            return f"{name}[t${sp}]"

        try:
            time = int(tree.children[1].children[0].value)
        except:
            time = 0
        if time ==0:
            ds = "t"
        elif time>0:
            ds = "t+"+str(time)
        elif time<0:
            ds = "t-"+str(-time)
        return f"{name}[{ds}]"

    def equality(self, tree):
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        return f"{a} = {b}"

    def double_complementarity(self, tree):
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        return f"{a} ⟂ {b}"

    def double_inequality(self, tree):
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        c = self.visit(tree.children[2])
        return f"{a} <= {b} <= {c}"

    def assignment(self, tree):
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        return f"{a} = {b}"


    def symbol(self, tree):
        name = tree.children[0].value
        return (name)
    def mul(self, tree):
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        return f"({a})*({b})"
    def div(self, tree):
        a = self.visit(tree.children[0])
        b = self.visit(tree.children[1])
        return f"({a})/({b})"
    def call(self, tree):
        funname = tree.children[0].value
        args = self.visit( tree.children[1] )
        return f"{funname}({args})"
    def pow(self, tree):
        arg1 = self.visit(tree.children[0])
        arg2 = self.visit(tree.children[1])
        return f"({arg1})^({arg2})"
    def number(self, tree):
        return tree.children[0].value
    def signed_int(self, tree):
        return tree.children[0].value
    def neg(self, tree):
        a = self.visit(tree.children[0])
        return f"-({a})"
    def expectation(self, tree):
        a = self.visit(tree.children[0])
        return f"𝔼[ {a} ]"
    def inequality(self, tree):
        a = self.visit(tree.children[0])
        b = (tree.children[1]).value
        c = self.visit(tree.children[2])
        return f"{a} {b} {c}"
    def predicate(self, tree):
        if len(tree.children)==1:
            return self.visit(tree.children[0])
        else:
            return "∀t, " + self.visit(tree.children[1])


def create_variable(name, time):
    return Tree("variable", [Tree("name", [Token("NAME", name)]), Tree("date", [Token("NUMBER", str(time))])])


## replaces v[t] by v[t+0] (I didn't find how to do it in the grammar)
## replaces v by v[t] when v identified as a variable
class Sanitizer(Transformer):

    def __init__(self, variables=[]):
        self.__variables__= variables

    def symbol(self, *args):
        tok = args[0][0]
        val = tok.value
        if val in self.__variables__:
            return Tree("variable", [Tree("name", [Token("NAME", val)]), Tree("date", [Token("NUMBER", '0')])])
        else:
            return Tree("symbol", *args)

    def variable(self, *args):
        if len(args[0])==1:
            date = Tree('date',[Token("NUMBER", '0')])
            args = (args[0] + [date], )
        return Tree("variable", *args)


## removes timing (replace v[t], v[t-1] or v[t+1] by v)
class TimeRemover(Transformer):

    def variable(self, args):
        name = args[0].children[0].value
        return Tree("symbol", [Token("NAME", name)])

def stringify_variable(arg: Tuple[str, int]) -> str:
    s = arg[0]
    date = arg[1]
    if date == 0:
        return '{}__0_'.format(s)
    elif date <= 0:
        return '{}_m{}_'.format(s, str(-date))
    elif date >= 0:
        return '{}__{}_'.format(s, str(date))


def stringify_parameter(p: str) -> str:
    return '{}_'.format(p)


def stringify_symbol(arg) -> str:
    if isinstance(arg, str):
        return stringify_parameter(arg)
    elif isinstance(arg, tuple):
        if len(arg) == 2 and isinstance(arg[0], str) and isinstance(
                arg[1], int):
            return stringify_variable(arg)
    raise Exception("Unknown canonical form: {}".format(arg))



## replaces symbols and variables by their canonical string represantation:
## symbols s -> "s_"
## variable v(1) -> "v_p1_"
## variable v(-1) -> "v_m1_"
class Stringifier(Transformer):

    def symbol(self, children):
        
        name = children[0].value
        if name == "inf":
            s = name
        else:
            s = stringify_parameter( name)
        return Tree("symbol", [Token("NAME",s)])

    def variable(self, children):
        
        name = children[0].children[0].value
        if len(children) == 1:
            date = 0
        else:
            date = int(children[1].children[0].value)
        s = stringify_variable( (name, date) )
        return Tree("symbol", [Token("NAME",s)])


###
## if shift == 'S' replaces all v[t+k] by v[t] (is that reasonable ?)
## if shift is an integer, replaces v[t+k] by v[t+k+shift]
class TimeShifter(Transformer):

    def __init__(self, shift: int):
        self.shift = shift

    def variable(self, children):
        
        name = children[0].children[0].value
        try:
            date = int(children[1].children[0].value)
        except:
            date = 0
        if self.shift=="S":
            new_date = "0"
        else:
            new_date = str(date + self.shift)
        return Tree("variable", [Tree("name", [Token("NAME", name)]), Tree("date", [Token("NUMBER", new_date)])])



@dataclass
class SymbolList(dict):
    variables: List[Tuple[str, int]]
    parameters: List[str]
    functions: List[str]

## lists all variables in an  expression
## result field contains variables with timing, parameters, and functions used
class VariablesLister(Visitor):

    def __init__(self):
        self.result = SymbolList([],[],[])

    def variable(self, tree):
        children = tree.children
        
        name = children[0].children[0].value
        date = int(children[1].children[0].value)
        if (name,date) not in self.result.variables:
            self.result.variables.append((name, date))

    def symbol(self, tree):
        children = tree.children
        name = children[0].value
        if name not in self.result.parameters:
            self.result.parameters.append(name)

    def call(self, tree):
        children = tree.children
        name = children[0].value
        if name not in self.result.functions:
            self.result.functions.append(name)


## replaces symbols in an expression:
## NameSustituter({'h': parser.parse("e+1")}).visit(parser.parse("h+p"))  returns 
## parser.parse("e+1+p")
class NameSubstituter(Transformer):

    # substitutes a symbol by an expression
    def __init__(self, substitutions: Dict[str, Expression]):
        self.substitutions = substitutions

    def symbol(self, children):
        name = children[0].value
        if name in self.substitutions:
            return self.substitutions[name]
        else:
            return Tree("symbol", children)

def subs(expr: str, substitutions):
    import copy
    s = dict()
    f = expr
    for k,v in substitutions.items():
        s[k] = parser.parse(v, start='start')
    ns = NameSubstituter(s)
    res = ns.transform(f)
    return str_expression(res)

# prints expression
def str_expression(expr: Expression)->str:
    return Printer().visit(expr)


# decorator to define functions which operate
# either on Trees or on strings.
def expression_or_string(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if not isinstance(args[0], str):
            return f(*args, **kwds)
        else:
            a = parser.parse(args[0], start='start')
            nargs = tuple([a]) + args[1:]
            res = f(*nargs, **kwds)
            return str_expression(res)

    return wrapper


## these functions apply the vistors/transformers either on expressions or on strings 
@expression_or_string
def stringify(expr: Expression):
    return Stringifier().transform(expr)

@expression_or_string
def time_shift(expr: Expression, n) -> Expression:

    return TimeShifter(n).transform(expr)


@expression_or_string
def steady_state(expr: Expression) -> Expression:
    return TimeShifter(shift='S').transform(expr)


@expression_or_string
def sanitize(expr: Expression, variables=[]):
    return Sanitizer(variables=variables).transform(expr)
    

@expression_or_string
def remove_timing(expr: Expression):
    return TimeRemover().transform(expr)
    

def list_symbols(expr: Union[Expression,str]) -> SymbolList:

    if isinstance(expr, str):
        expr = parser.parse(str, start='start')

    ll = VariablesLister()
    ll.visit(expr)

    return ll.result

def list_variables(expr: Union[Expression, str]):
    return list_symbols(expr).variables


def test():

    l = lark.Lark(grammar_0)

    s = "d + h + oij^2 - (1.0 + a) + sin(x) + v[t+1] + v[t] + x(0) + z[t]"
    p0 = l.parse(s)

    list_variables = ['h']
    p = Sanitizer(list_variables).transform(p0)

    pp = time_shift(s,-2)
    pp_2 = time_shift(s, "S")

    print("Original:                 ", s)
    print("Steady-state:             ", steady_state(s))
    print("Sanitize (variables=[h]): ", sanitize(s, variables=['h']))
    print("Stringify: ", stringify(s))

    print("Original Tree:")
    print( p0.pretty() )

if __name__ == "__main__":
    test()


def tree_to_ast(tree):
    import ast
    import re
    __regex_eq__ = re.compile("([^=]*)=([^=]*)")

    txt = (str_expression(tree))

    ss = txt.replace("^", "**")
    m = re.match(__regex_eq__, ss)
    if m:
        ss = str.join('==', m.groups())
    
    return ast.parse(ss).body[0]
