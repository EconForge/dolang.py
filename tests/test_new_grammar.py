def test_formulas():
    # import dolang.grammar
    
    from dolang.grammar import parser_f, parser
    print("Testing formulas grammar:")

    formulas = [
        "x[t-1]",
        "x[t]",
        "x[t+1]",
        "x[t]^alpha*x[t-1]^(1-alpha)",
        "-x[t]^alpha*x[t-1]^(1-alpha)",
        "sin(x[t])",
        "cos(x[t]+1)",
        "exp(x[t]+sin(x[t-1]))",
    ]
    import time
    t = time.time()
    for f in formulas:
        print(f)
        res = parser_f.parse(f, start="formula")
        print(res.pretty())
    print("time:", time.time() - t)


    t = time.time()
    for f in formulas:
        print(f)
        res = parser.parse(f, start="equation")
        print(res.pretty())
    print("time:", time.time() - t)

def test_parse_neoclassical():

    import time
    txt = """
    z[t] = ρ*z[t-1] + e_z[t] + e_y[t]
    y[t] = exp(z[t])*k[t-1]^α
    k[t] = k[t-1]*(1-δ) + i[t]
    c[t] = exp(z[t])*k[t-1]^α - i[t]
    β*(c[t+1]/c[t])^(-γ)*(1-δ+α*y[t+1]/k[t]) = 1

    α = 0.387 
    β = 0.96
    γ = 4.0
    δ = 0.1
    z = 0.0
    ρ = 0.9
    k = ((1/β-(1-δ))/α)**(1/(α-1))
    y = k^α
    i = δ*k
    c = y - i
    """

    from dolang.grammar import parser_f, parser
    print("Testing neoclassical model")

    t = time.time()
    res = parser.parse(txt, start="equation_block")
    print("time:", time.time() - t)

    t = time.time()
    res = parser_f.parse(txt, start="equation_block")
    print("time:", time.time() - t)

