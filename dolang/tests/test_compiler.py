def test_compiler():
    from dolang.factory import FlatFunctionFactory
    from dolang.codegen import to_source

    fff = FlatFunctionFactory(
        dict(x="b+c*p1", y="(a+b)*c"),  # preamble
        dict(out_1="exp(y*p1)-a*p2", out_2="x+y"),
        dict(g1=["a", "b"], g2=["c"], g3=["p1", "p2"]),
        "testfun",
    )

    from dolang.function_compiler import make_method_from_factory

    fun = make_method_from_factory(fff)[0]

    import numpy as np

    out = np.array([0.3, 0.1])

    fun(np.array([0.1, 0.2]), np.array([10]), np.array([0.5, 0.3]), out)

    assert abs(out[0] - 4.45168907) < 1e-8
    assert abs(out[1] - 8.2) < 1e-8


def test_compiler_2():
    from dolang.factory import FlatFunctionFactory
    from dolang.codegen import to_source

    fff = FlatFunctionFactory(
        dict(x="b+c*p1", y="(a+b)*c"),  # preamble
        dict(out_1="exp(y*p1)-a*p2", out_2="x+y"),
        dict(g1=["a", "b"], g2=["c"], g3=["p1", "p2"]),
        "testfun",
    )

    from dolang.function_compiler import make_method_from_factory

    fun = make_method_from_factory(fff, compile=False, debug=True)

    import numpy as np

    out = np.array([0.3, 0.1])

    fun(np.array([0.1, 0.2]), np.array([10]), np.array([0.5, 0.3]), out)

    assert abs(out[0] - 4.45168907) < 1e-8
    assert abs(out[1] - 8.2) < 1e-8
