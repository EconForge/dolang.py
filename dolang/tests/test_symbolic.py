import ast
from dolang.grammar import str_expression as to_source
from dolang.symbolic import stringify, list_variables, list_symbols
from dolang.grammar import Tree


def test_parsing():
    from dolang.grammar import str_expression, sanitize
    from dolang.symbolic import parse_string

    e = parse_string("s + a(0) + b[t-1] + b[t] + b[t+1]")
    print(e.pretty())

    e = parse_string("chi*n^eta*c^sigma - w(1)")
    print(e.pretty())

    e = parse_string("chi*n^eta*c^sigma - w(1) | 0.01 <= n <= 1.0")
    print(e.pretty())

    e = parse_string("chi*n^eta*c^sigma - w(1) ⟂ 0.01 <= n <= 1.0")
    print(e.pretty())

    e = parse_string("i = exp(z)*k^alpha*n^(1-alpha) - (m)^(-1/sigma)")
    print(e.pretty())
    f = sanitize(e, variables=["m"])
    print(str_expression(f))

    s = "i = exp(z)*k^alpha*n^(1-alpha) - (m)^(-1/sigma)"
    e = parse_string(s)

    s = "i = exp(z)*k^alpha*n^(1-alpha) - (m)^(-1/sigma)"
    # vars = ['z', 'p', 'k', 'n', 'i', 'm', 'V', 'u', 'y', 'c', 'rk', 'w', 'y', 'c']
    # print("HI")
    # v = sanitize(s, variables=vars)
    # print(v)
    e = parse_string(s)
    print(str_expression(e))


def test_parsing_unicode():

    from dolang.symbolic import parse_string

    s = "αα"
    e = parse_string(s)
    print(e)


def test_expectation():
    from dolang.symbolic import parse_string

    s = "𝔼[ (x[t+1] / x[t]) ]"
    e = parse_string(s)
    print(e.pretty())
    from dolang.symbolic import str_expression

    print(str_expression(e))


def test_parse_string():
    from dolang.symbolic import parse_string

    e = parse_string("sin(a(1)+b+f(1)+f(4)+a[t+1])")
    assert isinstance(e, Tree)
    s = to_source(e)
    assert s == "sin(a[t+1] + b + f[t+1] + f[t+4] + a[t+1])"


def test_remove_timing():
    from dolang.symbolic import parse_string, remove_timing

    e = parse_string("sin(a(1)+b+f(1)+f(4)+a[t+1])")
    assert isinstance(e, Tree)
    s = to_source(e)
    rr = remove_timing(s)
    assert rr == "sin(a + b + f + f + a)"


def test_multiline():
    from dolang.symbolic import parse_string

    e = parse_string(
        "a ⟂ x <= y <= exp(z)\nb ⟂ x <= y <= z", start="complementarity_block"
    )
    assert len(e.children) == 2


def test_predicate():
    from dolang.symbolic import parse_string, str_expression

    e = parse_string("a[t] <= (x[t]+b)")
    print(e.pretty())
    print(str_expression(e))
    e = parse_string("∀t, a[t] <= (x[t]+b)")
    print(e.pretty())
    print(str_expression(e))


def test_subperiod():
    from dolang.symbolic import parse_string, str_expression

    e = parse_string("a[t$1] = a[t+1]")
    print(e.pretty())
    print(str_expression(e))
    e = parse_string("a[t$consumption] = a[t+1]")
    print(e.pretty())
    print(str_expression(e))
    from lark.lark import Lark


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

    e = parse_string("sin(a(1)+b+f(1)+f(4)+a(1))+cos(0)")
    ll = list_symbols(e)
    print(ll.variables)
    print(ll.parameters)
    # cos is recognized as a usual function
    assert ll.variables == [("a", 1), ("f", 1), ("f", 4)]
    assert ll.parameters == ["b"]


def test_list_variables():
    from dolang.symbolic import parse_string

    e = parse_string("sin(a(1)+b+f(1)+f(4)+sin(a)+k*cos(a(0)))")
    list_variables(e)
    assert list_variables(e) == [("a", 1), ("f", 1), ("f", 4), ("a", 0)]


def test_sanitize():

    from dolang.symbolic import sanitize, parse_string

    s = "sin(a(1)+b+a+f(-1)+f(4)+a(1))"

    expected = "sin(a[t+1] + b + a[t] + f[t-1] + f[t+4] + a[t+1])"
    assert sanitize(s, variables=["a", "f"]) == expected

    # # we also deal with = signs, and convert to python exponents
    # assert (sanitize("a(1) = a^3 + b") == "a(1) == (a) ** (3) + b")


def test_stringify():

    from dolang.symbolic import parse_string

    s = "sin(a(1) + b + a(0) + f(-1) + f(4) + a(1))"
    enes = stringify(s)
    assert enes == "sin(a__1_ + b_ + a__0_ + f_m1_ + f__4_ + a__1_)"


def test_time_shift():

    from dolang.symbolic import time_shift, stringify_parameter

    e = "sin(a(1) + b + a(0) + f(-1) + f(4) + a(1))"

    enes = stringify(time_shift(e, +1))
    assert (enes) == "sin(a__2_ + b_ + a__1_ + f__0_ + f__5_ + a__2_)"
