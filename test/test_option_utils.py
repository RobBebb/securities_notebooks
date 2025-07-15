import select

from securities_notebooks.market.utils.option_strategy_calcs import (
    strategy_payoff_calcs,
    strategy_type_calcs,
)


def test_long_call(options):
    selected_options = [options["A250718C00130000_buy"]]
    strategy_dict = strategy_type_calcs(selected_options)
    assert strategy_dict["strategy"] == "Long Call"
    assert strategy_dict["payment"] == 0.175
    assert strategy_dict["maximum_risk"] == 0.175
    assert strategy_dict["maximum_reward"] is None
    assert strategy_dict["breakeven"] == 130.175


def test_short_call(options):
    selected_options = [options["A250718C00125000_sell"]]
    strategy_dict = strategy_type_calcs(selected_options)
    assert strategy_dict["strategy"] == "Short (Naked) Call"
    assert strategy_dict["payment"] == -1.225
    assert strategy_dict["maximum_risk"] is None
    assert strategy_dict["maximum_reward"] == 1.225
    assert strategy_dict["breakeven"] == 126.225


def test_long_put(options):
    selected_options = [options["A250718P00115000_buy"]]
    strategy_dict = strategy_type_calcs(selected_options)
    assert strategy_dict["strategy"] == "Long Put"
    assert strategy_dict["payment"] == 0.25
    assert strategy_dict["maximum_risk"] == 0.25
    assert strategy_dict["maximum_reward"] == 114.75
    assert strategy_dict["breakeven"] == 114.75


def test_short_put(options):
    selected_options = [options["A250718P00120000_sell"]]
    strategy_dict = strategy_type_calcs(selected_options)
    assert strategy_dict["strategy"] == "Short (Naked) Put"
    assert strategy_dict["payment"] == -0.725
    assert strategy_dict["maximum_risk"] == 119.275
    assert strategy_dict["maximum_reward"] == 0.725
    assert strategy_dict["breakeven"] == 119.275


def test_long_iron_condor(options):
    selected_options = [
        options["A250718C00130000_buy"],
        options["A250718C00125000_sell"],
        options["A250718P00115000_buy"],
        options["A250718P00120000_sell"],
    ]
    strategy_dict = strategy_type_calcs(selected_options)
    assert strategy_dict["strategy"] == "Long Iron Condor"
    assert strategy_dict["payment"] == -1.525
    assert strategy_dict["maximum_risk"] == 3.475
    assert strategy_dict["maximum_reward"] == 1.525
    assert strategy_dict["breakeven"] is None
    assert strategy_dict["breakeven_down"] == 118.475
    assert strategy_dict["breakeven_up"] == 126.525
    assert strategy_dict["warning"] is None
