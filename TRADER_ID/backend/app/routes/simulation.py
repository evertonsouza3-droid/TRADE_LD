import math
import random


def run_simulation(payload):
    rng = random.Random(42)
    initial_value = float(payload.get("initial_value", 0))
    monthly_contribution = float(payload.get("monthly_contribution", 0))
    years = int(payload.get("years", 0))
    volatility = float(payload.get("volatility", 0))

    if years <= 0 or initial_value <= 0:
        return {
            "projected_value": 0.0,
            "annualized_return": 0.0,
        }

    # Simulação Monte Carlo simples com retorno anual esperado e volatilidade.
    trials = 2000
    expected_annual_return = 0.05
    results = []

    for _ in range(trials):
        value = initial_value
        for _ in range(years):
            shock = rng.gauss(0, volatility)
            annual_growth = math.exp((expected_annual_return - 0.5 * volatility * volatility) + shock)
            value = (value + monthly_contribution * 12) * annual_growth
        results.append(value)

    average_projected = sum(results) / len(results)
    average_annualized = (
        (average_projected / initial_value) ** (1 / years) - 1
        if initial_value > 0 and years > 0
        else 0
    )

    return {
        "projected_value": round(average_projected, 2),
        "annualized_return": round(average_annualized, 6),
    }
