from dataclasses import dataclass
from typing import Optional, Literal
from decimal import Decimal
from pydantic import BaseModel, Field

Timeframe = Literal["1m","5m","15m","30m","1h","2h","4h","1d"]
MomentumStage = Literal["early","developing","mature","none"]

# Pydantic response/IO model aligned to DB (uses Decimal for exactness, casts on output)
class MomentumSignalModel(BaseModel):
    id: int | None = Field(default=None)
    symbol: str
    candle_timestamp: int
    timeframe: str
    volume_spike_pct: float | None = None
    volume_building: bool | None = None
    current_volume: float | None = None
    avg_volume: float | None = None
    price_change_pct: float | None = None
    price_change_current_bar: float | None = None
    price_change_1hour: float | None = None
    price_change_2hour: float | None = None
    price_change_4hour: float | None = None
    momentum_score: int | None = None
    momentum_stage: str | None = None
    trends_aligned: bool | None = None
    volume_price_sync: bool | None = None
    volatility: float | None = None
    current_price: Decimal | float | None = None
    volume_score: float | None = None
    price_score: float | None = None
    trend_score: float | None = None
    quality_score: float | None = None
    volatility_score: float | None = None
    volume_zscore: float | None = None
    signal_strength: float | None = None
    atr_normalized_return: float | None = None
    volume_spike_threshold: float | None = None
    created_at: str | None = None

    class Config:
        json_encoders = {Decimal: lambda d: float(d)}
