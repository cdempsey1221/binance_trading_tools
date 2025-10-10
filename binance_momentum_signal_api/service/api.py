from fastapi import FastAPI, HTTPException, Query
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal
from models.model import MomentumSignalModel

class Settings(BaseSettings):
    MYSQL_DSN: str = "mysql+pymysql://user:pass@127.0.0.1:3306/momentum_signal_monitor"
    class Config: env_file = ".env"

settings = Settings()
engine = create_engine(settings.MYSQL_DSN, pool_pre_ping=True, pool_size=8, max_overflow=8)
app = FastAPI(title="Momentum Signals API", version="0.1.0")

def rows_to_models(rs) -> List[MomentumSignalModel]:
    items = []
    for r in rs:
        row_dict = dict(r._mapping)
        # Convert datetime to ISO string for created_at
        if 'created_at' in row_dict and isinstance(row_dict['created_at'], datetime):
            row_dict['created_at'] = row_dict['created_at'].isoformat()
        # Convert Decimal to float for current_price
        if 'current_price' in row_dict and isinstance(row_dict['current_price'], Decimal):
            row_dict['current_price'] = float(row_dict['current_price'])
        m = MomentumSignalModel(**row_dict)
        items.append(m)
    return items

@app.get("/healthz")
def healthz(): return {"status": "ok"}

@app.get("/symbols", response_model=List[str])
def symbols():
    with engine.begin() as conn:
        cur = conn.execute(text("SELECT DISTINCT symbol FROM alerts ORDER BY symbol"))
        return [r[0] for r in cur.fetchall()]

@app.get("/alerts/search")
def search_alerts(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    after_ts: Optional[int] = None,
    min_signal: Optional[float] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort: Literal["ts_desc","signal_desc","momentum_desc","created_desc"] = "ts_desc",
    limit: int = Query(50, ge=1, le=500),
    cursor: Optional[int] = None,
):
    where = ["1=1"]; params = {}
    if symbol: where += ["symbol=:symbol"]; params["symbol"] = symbol.upper()
    if timeframe: where += ["timeframe=:tf"]; params["tf"] = timeframe
    if after_ts: where += ["candle_timestamp > :after_ts"]; params["after_ts"] = after_ts
    if min_signal is not None: where += ["signal_strength >= :min_signal"]; params["min_signal"]=min_signal
    if min_price is not None: where += ["current_price >= :min_price"]; params["min_price"]=min_price
    if max_price is not None: where += ["current_price <= :max_price"]; params["max_price"]=max_price
    if cursor: where += ["id < :cursor"]; params["cursor"]=cursor

    order = {
        "ts_desc": "candle_timestamp DESC, id DESC",
        "signal_desc": "signal_strength DESC, id DESC",
        "momentum_desc": "momentum_score DESC, id DESC",
        "created_desc": "created_at DESC, id DESC",
    }[sort]

    sql = f"SELECT * FROM alerts WHERE {' AND '.join(where)} ORDER BY {order} LIMIT :limit"
    params["limit"] = limit

    with engine.begin() as conn:
        cur = conn.execute(text(sql), params)
        items = rows_to_models(cur.fetchall())
    next_cursor = items[-1].id if len(items)==limit else None
    return {"items": [i.model_dump() for i in items], "next_cursor": next_cursor}

@app.get("/alerts/{id}", response_model=MomentumSignalModel)
def get_alert(id: int):
    with engine.begin() as conn:
        row = conn.execute(text("SELECT * FROM alerts WHERE id=:id"), {"id": id}).mappings().first()
        if not row:
            raise HTTPException(404, "Not found")
        # Convert datetime to ISO string and Decimal to float
        row_dict = dict(row)
        if 'created_at' in row_dict and isinstance(row_dict['created_at'], datetime):
            row_dict['created_at'] = row_dict['created_at'].isoformat()
        if 'current_price' in row_dict and isinstance(row_dict['current_price'], Decimal):
            row_dict['current_price'] = float(row_dict['current_price'])
        return MomentumSignalModel(**row_dict)
