
def test_latex():

    
    from dolang.latex import expr2tex, eq2tex

    s = '(a + w_1__y)/2 + 1'
    s =  "-(1+2)"
    s = "a*x(2) + b*y(-1)"
    assert( expr2tex(['x','y'], s) == "a \\; x_{t+2} + b \\; y_{t-1}")
    eq = "l = a*x(2) + b*y(-1)"
    assert( eq2tex(['x','y'], eq) == "l = a \\; x_{t+2} + b \\; y_{t-1}")