def test_yaml_extension():

    txt = """
        name: "Model"

        symbols:
            controls: [alpha, beta]
            states: [hei, ho]

        equations:
            arbitrage: |

                β*(c[t+1]/c[t])^(-γ+)*r - 1
                β*(c[t+1]/c[t])^(-γ)*(r_2[t+1]-r_1[t+1])
        
        calibration:
            a: 0.1
            b: 10
    """

    import dolang  # monkey-patch yaml

    import yaml

    data = yaml.compose(txt)

    assert "name" in data
    assert "equation" not in data

    assert data["name"].value == "Model"

    assert [e.value for e in data["symbols"]["controls"]] == ["alpha", "beta"]

    assert [*data["symbols"].keys()] == ["controls", "states"]
