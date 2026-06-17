from pydantic import BaseModel
from typing import Optional


class OperationCreate(BaseModel):
    name: str
    symbol: str
    quantity: float
    price: float


class OperationResponse(OperationCreate):
    id: int

    class Config:
        from_attributes = True


class SimulationRequest(BaseModel):
    initial_value: float
    monthly_contribution: float
    years: int
    volatility: float


class SimulationResponse(BaseModel):
    projected_value: float
    annualized_return: float
