from pydantic import BaseModel # type: ignore
from typing import List, Optional

class Position(BaseModel):
    symbol: str
    allocation: float


class Portfolio(BaseModel):
    id: Optional[str] = None 
    positions: List[Position]


class CreatePortfolioRequest(BaseModel):
    user_id: str
    portfolio: Portfolio
