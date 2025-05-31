from pydantic import BaseModel # type: ignore
from typing import List

class Position(BaseModel):
    symbol: str
    allocation: float


class Portfolio(BaseModel):
    positions: List[Position]


class CreatePortfolioRequest(BaseModel):
    user_id: str
    portfolio: Portfolio
