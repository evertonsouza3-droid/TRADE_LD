import math
import random

from app.schemas import SimulationRequest, SimulationResponse


def simulate(payload: SimulationRequest) -> SimulationResponse:
    random.seed(42)

    annual_return = payload.initial_value * (payload.monthly_contribution / 100)
    projected_value = payload.initial_value

    for _ in range(payload.years):
        annual_growth = 1 + random.uniform(-payload.volatility, payload.volatility)
        projected_value = (projected_value + payload.monthly_contribution * 12) * annual_growth

    annualized_return = (projected_value / payload.initial_value) ** (1 / payload.years) - 1 if payload.years else 0

    return SimulationResponse(
        projected_value=round(projected_value, 2),
        annualized_return=round(annualized_return, 6),
    )
