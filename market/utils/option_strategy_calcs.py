# type: ignore
from typing import Dict, Optional

import polars as pl
from trading_formations.option_utils.option import Option
from trading_formations.option_utils.option_calcs import option_calcs


def strategy_type_calcs(selected_options: list) -> Dict:
    strategy: Optional[str] = None
    payment: Optional[float] = None
    maximum_risk: Optional[float] = None
    maximum_reward: Optional[float] = None
    breakeven: Optional[float] = None
    breakeven_down: Optional[float] = None
    breakeven_up: Optional[float] = None
    warning: Optional[str] = None

    for option in range(len(selected_options)):
        if selected_options[option]["buy"] and selected_options[option]["sell"]:
            warning = "Buying and selling the same option doesn't make sense."

    if len(selected_options) == 1:
        if selected_options[0]["call_put"] == "C":  # type: ignore
            if selected_options[0]["buy"]:  # type: ignore
                payment = selected_options[0]["mid"]  # type: ignore
                maximum_risk = payment
                breakeven = round(
                    selected_options[0]["strike"] + selected_options[0]["mid"],
                    3,  # type: ignore
                )
                strategy = "Long Call"
            else:
                payment = selected_options[0]["mid"] * -1  # type: ignore
                maximum_reward = selected_options[0]["mid"]  # type: ignore
                breakeven = round(
                    selected_options[0]["strike"] + selected_options[0]["mid"],
                    3,  # type: ignore
                )
                strategy = "Short (Naked) Call"
        else:
            if selected_options[0]["buy"]:  # type: ignore
                payment = selected_options[0]["mid"]  # type: ignore
                maximum_risk = payment
                maximum_reward = round(
                    selected_options[0]["strike"] - selected_options[0]["mid"],
                    3,  # type: ignore
                )
                breakeven = round(
                    selected_options[0]["strike"] - selected_options[0]["mid"],
                    3,  # type: ignore
                )
                strategy = "Long Put"
            else:
                payment = selected_options[0]["mid"] * -1
                maximum_risk = round(
                    selected_options[0]["strike"] - selected_options[0]["mid"], 3
                )
                maximum_reward = selected_options[0]["mid"]
                breakeven = round(
                    selected_options[0]["strike"] - selected_options[0]["mid"], 3
                )
                strategy = "Short (Naked) Put"

    if len(selected_options) == 2:
        if selected_options[0]["expiry_date"] == selected_options[1]["expiry_date"]:
            if (
                selected_options[0]["call_put"] == "C"
                and selected_options[1]["call_put"] == "C"
            ):
                if selected_options[0]["buy"] and selected_options[1]["buy"]:
                    warning = "Buying two calls is an unknown strategy."
                elif selected_options[0]["sell"] and selected_options[1]["sell"]:
                    warning = "Selling two calls is an unknown strategy."
                elif selected_options[0]["buy"]:
                    if selected_options[0]["strike"] < selected_options[1]["strike"]:
                        payment = round(
                            selected_options[0]["mid"] - selected_options[1]["mid"], 3
                        )
                        maximum_risk = payment
                        maximum_reward = round(
                            (
                                selected_options[1]["strike"]
                                - selected_options[0]["strike"]
                                - payment
                            ),
                            3,
                        )
                        breakeven = round(selected_options[0]["strike"] + payment, 3)
                        strategy = "Bull Call Spread"
                    elif selected_options[0]["strike"] > selected_options[1]["strike"]:
                        payment = round(
                            (selected_options[1]["mid"] - selected_options[0]["mid"])
                            * -1,
                            3,
                        )
                        maximum_risk = round(
                            (
                                selected_options[0]["strike"]
                                - selected_options[1]["strike"]
                                - (
                                    selected_options[1]["mid"]
                                    - selected_options[0]["mid"]
                                )
                            ),
                            3,
                        )
                        maximum_reward = round(
                            (selected_options[1]["mid"] - selected_options[0]["mid"]), 3
                        )
                        breakeven = round(
                            selected_options[1]["strike"]
                            + (selected_options[1]["mid"] - selected_options[0]["mid"]),
                            3,
                        )
                        strategy = "Bear Call Spread"
                    else:
                        warning = "Buying and selling calls with the same date and strike doesn't make sense."
            elif (
                selected_options[0]["call_put"] == "P"
                and selected_options[1]["call_put"] == "P"
            ):
                if selected_options[0]["buy"] and selected_options[1]["buy"]:
                    warning = "Buying two puts is an unknown strategy."
                elif selected_options[0]["sell"] and selected_options[1]["sell"]:
                    warning = "Selling two puts is an unknown strategy."
                elif selected_options[0]["buy"]:
                    if selected_options[0]["strike"] < selected_options[1]["strike"]:
                        payment = round(
                            (selected_options[1]["mid"] - selected_options[0]["mid"])
                            * -1,
                            3,
                        )
                        maximum_risk = round(
                            (
                                selected_options[1]["strike"]
                                - selected_options[0]["strike"]
                                - (
                                    (
                                        selected_options[1]["mid"]
                                        - selected_options[0]["mid"]
                                    )
                                    * -1
                                )
                            ),
                            3,
                        )
                        maximum_reward = round(
                            (selected_options[1]["mid"] - selected_options[0]["mid"]), 3
                        )
                        breakeven = round(
                            selected_options[1]["strike"]
                            - (selected_options[1]["mid"] - selected_options[0]["mid"]),
                            3,
                        )
                        strategy = "Bull Put Spread"
                    elif selected_options[0]["strike"] > selected_options[1]["strike"]:
                        payment = round(
                            selected_options[1]["mid"] - selected_options[0]["mid"], 3
                        )
                        maximum_risk = payment
                        maximum_reward = round(
                            (
                                selected_options[0]["strike"]
                                - selected_options[1]["strike"]
                                - payment
                            ),
                            3,
                        )
                        breakeven = round(selected_options[0]["strike"] + payment, 3)
                        strategy = "Bear Put Spread"
                    else:
                        warning = "Buying and selling puts with the same date and strike doesn't make sense."
            elif (
                selected_options[0]["call_put"] == "C"
                and selected_options[1]["call_put"] == "P"
            ):
                if selected_options[0]["buy"] and selected_options[1]["buy"]:
                    if selected_options[0]["strike"] == selected_options[1]["strike"]:
                        payment = round(
                            selected_options[0]["mid"] + selected_options[1]["mid"], 3
                        )
                        maximum_risk = payment
                        breakeven_down = round(
                            selected_options[0]["strike"] - payment, 3
                        )
                        breakeven_up = round(selected_options[0]["strike"] + payment, 3)
                        strategy = "Long Straddle"
                    elif selected_options[0]["strike"] != selected_options[1]["strike"]:
                        payment = round(
                            selected_options[0]["mid"] + selected_options[1]["mid"], 3
                        )
                        maximum_risk = payment
                        breakeven_down = round(
                            selected_options[1]["strike"]
                            - (selected_options[0]["mid"] + selected_options[1]["mid"]),
                            3,
                        )
                        breakeven_up = round(
                            selected_options[0]["strike"]
                            + (selected_options[0]["mid"] + selected_options[1]["mid"]),
                            3,
                        )
                        strategy = "Long Strangle"
                elif selected_options[0]["sell"] and selected_options[1]["sell"]:
                    if selected_options[0]["strike"] == selected_options[1]["strike"]:
                        payment = round(
                            (selected_options[0]["mid"] + selected_options[1]["mid"])
                            * -1,
                            3,
                        )
                        maximum_reward = (
                            selected_options[0]["mid"] + selected_options[1]["mid"]
                        )
                        breakeven_down = round(
                            selected_options[0]["strike"]
                            - (selected_options[0]["mid"] + selected_options[1]["mid"]),
                            3,
                        )
                        breakeven_up = round(
                            selected_options[0]["strike"]
                            + (selected_options[0]["mid"] + selected_options[1]["mid"]),
                            3,
                        )
                        strategy = "Short Straddle"
                    elif selected_options[0]["strike"] != selected_options[1]["strike"]:
                        payment = round(
                            (selected_options[0]["mid"] + selected_options[1]["mid"])
                            * -1,
                            3,
                        )
                        maximum_reward = (
                            selected_options[0]["mid"] + selected_options[1]["mid"]
                        )
                        breakeven_down = round(
                            selected_options[1]["strike"]
                            - (selected_options[0]["mid"] + selected_options[1]["mid"]),
                            3,
                        )
                        breakeven_up = round(
                            selected_options[0]["strike"]
                            + (selected_options[0]["mid"] + selected_options[1]["mid"]),
                            3,
                        )
                        strategy = "Short Strangle"
                else:
                    warning = "This is an unknown strategy. Do some more coding."
        # Remember the first option in the list should be the sold option with the shorter expiry date for calendards and diagonals
        elif selected_options[0]["expiry_date"] < selected_options[1]["expiry_date"]:
            warning = "The following chart is not quite correct due to the different expiry dates."
            if (
                selected_options[0]["call_put"] == "C"
                and selected_options[1]["call_put"] == "C"
            ):
                if selected_options[0]["buy"] and selected_options[1]["buy"]:
                    warning = "Buying two calls is an unknown strategy."
                elif selected_options[0]["sell"] and selected_options[1]["sell"]:
                    warning = "Selling two calls is an unknown strategy."
                elif selected_options[0]["buy"]:
                    warning = "This appears to be a diagonal call. However the bought call should have a longer expiry date than the sold call."
                elif selected_options[0]["sell"]:
                    if selected_options[0]["strike"] > selected_options[1]["strike"]:
                        payment = round(
                            selected_options[0]["mid"] - selected_options[1]["mid"], 3
                        )
                        maximum_risk = payment
                        strategy = "Diagonal Call"
                    elif selected_options[0]["strike"] < selected_options[1]["strike"]:
                        warning = "This appears to be a diagonal call. However the bought call should have a lower strike than the sold call."
                    else:
                        payment = round(
                            selected_options[0]["mid"] - selected_options[1]["mid"], 3
                        )
                        maximum_risk = payment
                        strategy = "Calender Call"
            elif (
                selected_options[0]["call_put"] == "P"
                and selected_options[1]["call_put"] == "P"
            ):
                if selected_options[0]["buy"] and selected_options[1]["buy"]:
                    warning = "Buying two puts is an unknown strategy."
                elif selected_options[0]["sell"] and selected_options[1]["sell"]:
                    warning = "Selling two puts is an unknown strategy."
                elif selected_options[0]["buy"]:
                    warning = "This appears to be a diagonal call. However the bought put should have a longer expiry date than the bought call."
                elif selected_options[0]["sell"]:
                    if selected_options[0]["strike"] < selected_options[1]["strike"]:
                        warning = "This appears to be a diagonal call. However the bought put should have a lower strike than the bought call."
                    elif selected_options[0]["strike"] > selected_options[1]["strike"]:
                        payment = round(
                            selected_options[0]["mid"] - selected_options[1]["mid"], 3
                        )
                        strategy = "Diagonal Put"
                    else:
                        payment = round(
                            selected_options[0]["mid"] - selected_options[1]["mid"], 3
                        )
                        strategy = "Calendar Put"
            else:
                warning = "This is an unknown strategy. Do some more coding."
        else:
            warning = "This is an unknown strategy."

    if len(selected_options) == 4:
        if (
            selected_options[0]["expiry_date"] == selected_options[1]["expiry_date"]
            and selected_options[2]["expiry_date"] == selected_options[3]["expiry_date"]
        ):
            if (
                selected_options[0]["call_put"] == "C"
                and selected_options[1]["call_put"] == "C"
                and selected_options[2]["call_put"] == "P"
                and selected_options[3]["call_put"] == "P"
            ):
                if (
                    selected_options[0]["buy"]
                    and selected_options[1]["sell"]
                    and selected_options[3]["sell"]
                    and selected_options[2]["buy"]
                ):
                    if (
                        selected_options[0]["strike"]
                        > selected_options[1]["strike"]
                        > selected_options[3]["strike"]
                        > selected_options[2]["strike"]
                    ):
                        payment = round(
                            (
                                selected_options[0]["mid"]
                                + selected_options[2]["mid"]
                                - selected_options[1]["mid"]
                                - selected_options[3]["mid"]
                            ),
                            3,
                        )
                        # Difference in adjacent strikes - net credit (Note that payment is a credit so it is negative, so we need to add it)
                        maximum_risk = round(
                            (
                                selected_options[0]["strike"]
                                - selected_options[1]["strike"]
                            )
                            + payment,
                            3,
                        )
                        maximum_reward = payment * -1
                        # Middle short put strike - net credit (Note that payment is a credit so it is negative, so we need to add it))
                        breakeven_down = round(
                            selected_options[3]["strike"] + payment, 3
                        )
                        # Middle short call strike + net credit (Note that payment is a credit so it is negative, so we need to subtract it it))
                        breakeven_up = round(selected_options[1]["strike"] - payment, 3)
                        strategy = "Long Iron Condor"
                    elif (
                        selected_options[0]["strike"]
                        > selected_options[1]["strike"]
                        == selected_options[3]["strike"]
                        > selected_options[2]["strike"]
                    ):
                        payment = round(
                            (
                                selected_options[0]["mid"]
                                + selected_options[2]["mid"]
                                - selected_options[1]["mid"]
                                - selected_options[3]["mid"]
                            ),
                            3,
                        )
                        # Difference in adjacent strikes - net credit (Note that payment is a credit so it is negative, so we need to add it)
                        maximum_risk = round(
                            (
                                selected_options[0]["strike"]
                                - selected_options[1]["strike"]
                            )
                            + payment,
                            3,
                        )
                        maximum_reward = payment
                        # Middle short put strike - net credit (Note that payment is a credit so it is negative, so we need to add it))
                        breakeven_down = round(
                            selected_options[3]["strike"] + payment, 3
                        )
                        # Middle short call strike + net credit (Note that payment is a credit so it is negative, so we need to subtract it it))
                        breakeven_up = round(selected_options[1]["strike"] - payment, 3)
                        strategy = "Long Iron Butterfly"
                    elif (
                        selected_options[1]["strike"]
                        > selected_options[0]["strike"]
                        == selected_options[2]["strike"]
                        > selected_options[3]["strike"]
                    ):
                        payment = round(
                            (
                                selected_options[0]["mid"]
                                + selected_options[2]["mid"]
                                - selected_options[1]["mid"]
                                - selected_options[3]["mid"]
                            ),
                            3,
                        )
                        # Difference in adjacent strikes - net debit
                        maximum_risk = payment
                        maximum_reward = round(
                            (
                                selected_options[1]["strike"]
                                - selected_options[0]["strike"]
                            )
                            - payment,
                            3,
                        )
                        # Middle short put strike - net debit
                        breakeven_down = round(
                            selected_options[2]["strike"] - payment, 3
                        )
                        # Middle short call strike + net debit
                        breakeven_up = round(selected_options[0]["strike"] + payment, 3)
                        strategy = "Short Iron Butterfly"
                    elif (
                        selected_options[1]["strike"]
                        > selected_options[0]["strike"]
                        > selected_options[2]["strike"]
                        > selected_options[3]["strike"]
                    ):
                        payment = round(
                            (
                                selected_options[0]["mid"]
                                + selected_options[2]["mid"]
                                - selected_options[1]["mid"]
                                - selected_options[3]["mid"]
                            ),
                            3,
                        )
                        # Difference in adjacent strikes - net debit
                        maximum_risk = payment
                        maximum_reward = round(
                            (
                                selected_options[1]["strike"]
                                - selected_options[0]["strike"]
                            )
                            - payment,
                            3,
                        )
                        # Middle short put strike - net debit
                        breakeven_down = round(
                            selected_options[2]["strike"] - payment, 3
                        )
                        # Middle short call strike + net debit
                        breakeven_up = round(selected_options[0]["strike"] + payment, 3)
                        strategy = "Short Iron Condor"
                    else:
                        warning = "1.This is an unknown strategy. Do some more coding."
                else:
                    warning = "1.This is an unknown strategy. Do some more coding."
            elif (
                selected_options[0]["call_put"] == "C"
                and selected_options[1]["call_put"] == "C"
                and selected_options[2]["call_put"] == "C"
                and selected_options[3]["call_put"] == "C"
            ):
                if (
                    selected_options[0]["buy"]
                    and selected_options[2]["sell"]
                    and selected_options[3]["sell"]
                    and selected_options[1]["buy"]
                ):
                    if (
                        selected_options[3]["strike"]
                        > selected_options[1]["strike"]
                        > selected_options[0]["strike"]
                        > selected_options[2]["strike"]
                    ):
                        strategy = "Short Call Condor"
                    elif (
                        selected_options[3]["strike"]
                        > selected_options[1]["strike"]
                        == selected_options[0]["strike"]
                        > selected_options[2]["strike"]
                    ):
                        strategy = "Short Call Butterfly"
                    elif (
                        selected_options[1]["strike"]
                        > selected_options[3]["strike"]
                        == selected_options[2]["strike"]
                        > selected_options[0]["strike"]
                    ):
                        strategy = "Long Call Butterfly"
                    elif (
                        selected_options[1]["strike"]
                        > selected_options[3]["strike"]
                        > selected_options[2]["strike"]
                        > selected_options[0]["strike"]
                    ):
                        strategy = "Long Call Condor"
                    else:
                        warning = "1.This is an unknown strategy. Do some more coding."
                else:
                    warning = "1.This is an unknown strategy. Do some more coding."
            elif (
                selected_options[0]["call_put"] == "P"
                and selected_options[1]["call_put"] == "P"
                and selected_options[2]["call_put"] == "P"
                and selected_options[3]["call_put"] == "P"
            ):
                if (
                    selected_options[0]["buy"]
                    and selected_options[2]["sell"]
                    and selected_options[3]["sell"]
                    and selected_options[1]["buy"]
                ):
                    if (
                        selected_options[3]["strike"]
                        > selected_options[1]["strike"]
                        > selected_options[0]["strike"]
                        > selected_options[2]["strike"]
                    ):
                        strategy = "Short Put Condor"
                    elif (
                        selected_options[3]["strike"]
                        > selected_options[1]["strike"]
                        == selected_options[0]["strike"]
                        > selected_options[2]["strike"]
                    ):
                        strategy = "Short Put Butterfly"
                    elif (
                        selected_options[1]["strike"]
                        > selected_options[3]["strike"]
                        == selected_options[2]["strike"]
                        > selected_options[0]["strike"]
                    ):
                        strategy = "Long Put Butterfly"
                    elif (
                        selected_options[1]["strike"]
                        > selected_options[3]["strike"]
                        > selected_options[2]["strike"]
                        > selected_options[0]["strike"]
                    ):
                        strategy = "Long Put Condor"
                    else:
                        warning = "1.This is an unknown strategy. Do some more coding."
                else:
                    warning = "1.This is an unknown strategy. Do some more coding."
            else:
                warning = "3.This is an unknown strategy. Do some more coding."
        else:
            warning = "4.This is an unknown strategy. Do some more coding."

    strategy_dict = {}
    strategy_dict["strategy"] = strategy
    strategy_dict["payment"] = payment
    strategy_dict["maximum_risk"] = maximum_risk
    strategy_dict["maximum_reward"] = maximum_reward
    strategy_dict["breakeven"] = breakeven
    strategy_dict["breakeven_down"] = breakeven_down
    strategy_dict["breakeven_up"] = breakeven_up
    strategy_dict["warning"] = warning

    return strategy_dict


def strategy_payoff_calcs(
    selected_options: list, last_close: float, risk_free_rate: float, volatility: float
) -> pl.DataFrame:
    min_x_value = selected_options[0]["strike"]
    max_x_value = selected_options[0]["strike"]
    for i in range(len(selected_options)):
        if selected_options[i]["strike"] < min_x_value:
            min_x_value = selected_options[i]["strike"]
        if selected_options[i]["strike"] > max_x_value:
            max_x_value = selected_options[i]["strike"]

    if last_close < min_x_value:
        min_x_value = last_close
    if last_close > max_x_value:
        max_x_value = last_close

    start_price = min_x_value - (min_x_value * 0.1)
    end_price = max_x_value + (max_x_value * 0.1)

    # start_price = self.stock_price - (self.stock_price * 0.10)
    # end_price = self.stock_price + (self.stock_price * 0.10)
    steps = 100
    step_size = (end_price - start_price) / steps
    stock_prices = [start_price + i * step_size for i in range(steps)]

    total_payoff = [0 for i in range(len(stock_prices))]

    for i in range(len(selected_options)):
        option_id = selected_options[i]["id"]
        option_ticker = selected_options[i]["ticker"]
        option_strike = selected_options[i]["strike"]
        option_call_put = selected_options[i]["call_put"]
        option_expiry_date = selected_options[i]["expiry_date"]
        option_mid = selected_options[i]["mid"]

        option = Option(
            option_id, option_ticker, option_strike, option_expiry_date, option_call_put
        )
        option_calc = option_calcs(
            option, last_close, risk_free_rate=risk_free_rate, volatility=volatility
        )
        payoff = option_calc.payoff(stock_prices)
        if selected_options[i]["buy"]:
            # total_premium = total_premium - option_mid
            for j in range(len(stock_prices)):
                total_payoff[j] = total_payoff[j] + payoff[j] - option_mid
        else:
            # total_premium = total_premium + option_mid
            for j in range(len(stock_prices)):
                total_payoff[j] = total_payoff[j] - payoff[j] + option_mid

    return pl.DataFrame({"stock_price": stock_prices, "profit": total_payoff})
