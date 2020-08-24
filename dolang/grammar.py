from typing import Tuple
import lark
from lark import Tree, Token
from lark import Visitor
from lark import Transformer
from lark.visitors import Interpreter

from functools import wraps

from typing import Union
Expression = Union[Tree, Token]

from typing import Set
from dataclasses import dataclass

@dataclass
class SymbolList(dict):
    variables: Set[Tuple[str, int]]
    parameters: Set[str]
    functions: Set[str]


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
    # def mul(self, tok):
    #     a = self.visit(tree.children[0])
    #     b = self.visit(tree.children[1])
    #     return f"{a} * {b}"
    def variable(self, tree):
        # print(args)
        name = tree.children[0].children[0].value
        time = int(tree.children[1].children[0].value)
        if time ==0:
            ds = "t"
        elif time>0:
            ds = "t+"+str(time)
        elif time<0:
            ds = "t-"+str(-time)
        return f"{name}[{ds}]"

    def symbol(self, tree):
        name = tree.children[0].value
        return (name)
    def mul(self, tree):
        return "****"
    def call(self, tree):
        funname = tree.children[0].value
        args = self.visit( tree.children[1] )
        return f"{funname}({args})"
    def exponential(self, tree):
        arg1 = self.visit(tree.children[0])
        arg2 = self.visit(tree.children[1])
        return f"({arg1})^({arg2})"
    def number(self, tree):
        return tree.children[0].value


grammar_0 = """
    ?start: equation
    ?equation: equality | sum
    ?equality: sum "=" sum 
        | sum "==" sum
    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub
    ?product: atom
        | exponential
        | product "*" atom  -> mul
        | product "/" atom  -> div
    ?exponential: atom "^" atom
    ?atom: NUMBER           -> number
         | "-" atom         -> neg
         | symbol            
         | "(" sum ")"
         | call
         | variable
    ?symbol: NAME -> symbol
    ?variable: symbol  "[" "t" ("+" date_index)? "]" -> variable
            | symbol "(" date_index ")" -> variable
    ?date_index: NUMBER -> date
    ?call: FUNCTION "(" sum ")" -> call
    FUNCTION: "sin"|"cos"|"exp"|"log"

    
    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE
    %ignore WS_INLINE
"""

parser = lark.Lark(grammar_0)


class Sanitizer(Transformer):

    def __init__(self, variables=[]):
        self.__variables__= variables

    def symbol(self, *args):
        tok = args[0][0]
        val = tok.value
        if val in self.__variables__:
            return Tree("variable", [Tree("symbol", [Token("NAME", val)]), Tree("date", [Token("NUMBER", '0')])])
        else:
            return Tree("symbol", *args)

    def variable(self, *args):
        if len(args[0])==1:
            date = Tree('date',[Token("NUMBER", '0')])
            args = (args[0] + [date], )
        return Tree("variable", *args)

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



class Stringifier(Transformer):

    def symbol(self, children):
        
        name = children[0].value
        s = stringify_parameter( name)
        return Tree("symbol", [Token("NAME",s)])

    def variable(self, children):
        
        name = children[0].children[0].value
        date = int(children[1].children[0].value)
        s = stringify_variable( (name, date) )
        return Tree("symbol", [Token("NAME",s)])

class TimeShifter(Transformer):

    def __init__(self, shift: int):
        self.shift = shift

    def variable(self, children):
        
        name = children[0].children[0].value
        date = int(children[1].children[0].value)
        if self.shift=="S":
            new_date = "0"
        else:
            new_date = str(date + self.shift)
        return Tree("variable", [Tree("symbol", [Token("NAME", name)]), Tree("date", [Token("NUMBER", new_date)])])




def str_expression(expr: Expression)->str:
    return Printer().visit(expr)

def expression_or_string(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if not isinstance(args[0], str):
            return f(*args, **kwds)
        else:
            a = parser.parse(args[0])
            nargs = tuple([a]) + args[1:]
            res = f(*nargs, **kwds)
            return str_expression(res)

    return wrapper

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
    


def list_variables(expr: Union[Expression,str]) -> SymbolList:

    if isinstance(expr, str):
        expr = parser.parse(str)

    ll = VariablesLister()
    ll.visit(expr)

    return ll.result
    # if ll.problems:
    #     e = Exception('Symbolic error.')
    #     e.problems = ll.problems
    #     raise e
    # return dedup([v[0] for v in ll.variables])

list_symbols = list_variables

class VariablesLister(Visitor):

    def __init__(self):
        self.result = SymbolList(set(),set(),set())

    def variable(self, tree):
        children = tree.children
        
        name = children[0].children[0].value
        date = int(children[1].children[0].value)
        self.result.variables.add((name, date))

    def symbol(self, tree):
        children = tree.children
        name = children[0].value

        self.result.parameters.add(name)

    def call(self, tree):
        children = tree.children
        name = children[0].value

        self.result.functions.add(name)

def test():

    l = lark.Lark(grammar_0)

    s = "d + h + oij^2 - (1.0 + a) + sin(x) + v[t+1] + v[t] + x(0) + z[t]"
    p0 = l.parse(s)

    list_variables = ['h']
    p = Sanitize(list_variables).transform(p0)
    print( p.pretty() )

    print("Before: ", s)
    print("After:  ", Printer().visit(p))



    pp = time_shift(s,-2)
    pp_2 = time_shift(s, "S")
