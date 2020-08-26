import ast
from dolang.grammar import str_expression as to_source
from dolang.symbolic import stringify, list_variables, list_symbols
from dolang.grammar import Tree


def test_parsing():
    from dolang.symbolic import parse_string
    e = parse_string("s + a(0) + b[t-1] + b[t] + b[t+1]")
    print(e.pretty())

def test_parse_string():
    from dolang.symbolic import parse_string
    e = parse_string('sin(a(1)+b+f(1)+f(4)+a[t+1])')
    assert isinstance(e, Tree)
    s = to_source(e)
    assert (s == "sin(a[t+1] + b + f[t+1] + f[t+4] + a[t+1])")


# def test_list_symbols_debug():
#     from dolang.symbolic import parse_string
#     e = parse_string('sin(a(1)+b+f(1)+f(4)+a(1)+a+a[t+1]+cos(0)')
#     l = ListSymbols(known_functions=['sin', 'f'])
#     l.visit(e)
#     # note that cos is recognized as variable
#     assert (l.variables == [(('a', 1), 4), (('a', 1), 22), (('cos', 0), 37)])
#     assert (l.constants == [('b', 9), ('a', 27)])
#     assert (l.functions == [('sin', 0), ('f', 11), ('f', 16)])
#     assert (l.problems == [['a', 0, 29, 'incorrect subscript']])


def test_list_symbols():
    from dolang.symbolic import parse_string
    e = parse_string('sin(a(1)+b+f(1)+f(4)+a(1))+cos(0)')
    ll = list_symbols(e)
    print(ll.variables)
    print(ll.parameters)
    # cos is recognized as a usual function
    assert (ll.variables == [('a', 1), ('f', 1), ('f', 4)])
    assert (ll.parameters == ['b'])




def test_list_variables():
    from dolang.symbolic import parse_string
    e = parse_string('sin(a(1)+b+f(1)+f(4)+sin(a)+k*cos(a(0)))')
    list_variables(e)
    assert (list_variables(e) == [('a', 1), ('f', 1), ('f', 4), ('a', 0)])


def test_sanitize():

    from dolang.symbolic import sanitize, parse_string

    s = 'sin(a(1)+b+a+f(-1)+f(4)+a(1))'

    expected = "sin(a[t+1] + b + a[t] + f[t-1] + f[t+4] + a[t+1])"
    assert (sanitize(s, variables=['a', 'f']) == expected)

    # # we also deal with = signs, and convert to python exponents
    # assert (sanitize("a(1) = a^3 + b") == "a(1) == (a) ** (3) + b")


def test_stringify():

    from dolang.symbolic import parse_string
    s = 'sin(a(1) + b + a(0) + f(-1) + f(4) + a(1))'
    enes = stringify(s)
    assert ( enes == "sin(a__1_ + b_ + a__0_ + f_m1_ + f__4_ + a__1_)")


def test_time_shift():

    from dolang.symbolic import time_shift, stringify_parameter
    e = 'sin(a(1) + b + a(0) + f(-1) + f(4) + a(1))'

    enes = stringify(time_shift(e, +1))
    assert (
        (enes) == "sin(a__2_ + b_ + a__1_ + f__0_ + f__5_ + a__2_)")
