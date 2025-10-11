import sqlite3
import threading
import pymysql
import os
from typing import Optional
from urllib.parse import urlparse

DB_PATH = 'alerts.db'
CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS alerts (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	symbol TEXT NOT NULL,
	timeframe TEXT NOT NULL,
	bar_close_time INTEGER NOT NULL,
	signature TEXT NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	UNIQUE(symbol, timeframe, bar_close_time)
);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol_time ON alerts(symbol, bar_close_time);
CREATE INDEX IF NOT EXISTS idx_alerts_signature ON alerts(signature);
'''

class AlertDeduplicationDB:
	def __init__(self, db_path: str = DB_PATH):
		self.db_path = db_path
		self.lock = threading.Lock()
		self._init_db()

	def _init_db(self):
		with sqlite3.connect(self.db_path) as conn:
			conn.executescript(CREATE_TABLE_SQL)

	def store_alert(self, symbol: str, timeframe: str, bar_close_time: int, signature: str) -> bool:
		with self.lock, sqlite3.connect(self.db_path) as conn:
			try:
				conn.execute(
					"INSERT INTO alerts (symbol, timeframe, bar_close_time, signature) VALUES (?, ?, ?, ?)",
					(symbol, timeframe, bar_close_time, signature)
				)
				return True
			except sqlite3.IntegrityError:
				return False  # Duplicate

	def cleanup_old(self, days: int = 7):
		with self.lock, sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"DELETE FROM alerts WHERE created_at < datetime('now', ?)",
				(f'-{days} days',)
			)

	def alert_exists(self, symbol: str, timeframe: str, bar_close_time: int) -> bool:
		with self.lock, sqlite3.connect(self.db_path) as conn:
			cur = conn.execute(
				"SELECT 1 FROM alerts WHERE symbol=? AND timeframe=? AND bar_close_time=?",
				(symbol, timeframe, bar_close_time)
			)
			return cur.fetchone() is not None

class AlertDeduplicationMySQL:
    """
    Manages storing and deduplicating full MomentumSignal alerts in MySQL.
    This class is a complete replacement for the original SQLite version.
    """
    
    def __init__(self, db_url: str):
        if not db_url:
            raise ValueError("DATABASE_URL is required.")

        parsed_url = urlparse(db_url.replace("mysql+pymysql://", "mysql://"))
        self.conn_config = {
            'host': parsed_url.hostname,
            'port': parsed_url.port or 3306,
            'user': parsed_url.username,
            'password': parsed_url.password,
            'database': parsed_url.path[1:],
        }
        self.conn = None
        # Initialize connection and create table
        self.connect()
        self._init_db()
    
    def _ensure_connection(self):
        """Ensures the database connection is active."""
        if not self.conn or not self.conn.open:
            self.conn = pymysql.connect(**self.conn_config)
    
    def connect(self):
        """Establishes the database connection."""
        self._ensure_connection()
        return self

    def close(self):
        """Closes the database connection."""
        if self.conn and self.conn.open:
            self.conn.close()    
    
    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _init_db(self):
        """Creates the expanded alerts table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS alerts (
            id INT PRIMARY KEY AUTO_INCREMENT, symbol VARCHAR(50) NOT NULL,
            candle_timestamp BIGINT NOT NULL, timeframe VARCHAR(20) NOT NULL,
            volume_spike_pct FLOAT, volume_building BOOLEAN, current_volume DOUBLE,
            avg_volume DOUBLE, price_change_pct FLOAT, price_change_current_bar FLOAT,
            price_change_1hour FLOAT, price_change_2hour FLOAT, price_change_4hour FLOAT,
            momentum_score INT, momentum_stage VARCHAR(50), trends_aligned BOOLEAN,
            volume_price_sync BOOLEAN, volatility FLOAT, current_price DECIMAL(20, 8),
            volume_score FLOAT, price_score FLOAT, trend_score FLOAT,
            quality_score FLOAT, volatility_score FLOAT, volume_zscore FLOAT NULL,
            signal_strength FLOAT NULL, atr_normalized_return FLOAT NULL,
            volume_spike_threshold FLOAT NULL,
            ema_21_daily DECIMAL(20, 8) NULL,
            ema_50_daily DECIMAL(20, 8) NULL,
            price_vs_ema_21 VARCHAR(20) NULL,
            ema_trend_bias VARCHAR(20) DEFAULT 'neutral',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timeframe, candle_timestamp)
        );"""
        with self.conn.cursor() as cursor:
            cursor.execute(create_table_sql)
        self.conn.commit()
    
    def store_alert(self, signal: 'MomentumSignal') -> bool:
        """
        Stores a full MomentumSignal object. Returns True if new, False if duplicate.
        """
        self._ensure_connection()  # Ensure connection is active
        sql = """
            INSERT INTO alerts (
                symbol, candle_timestamp, timeframe, volume_spike_pct, volume_building,
                current_volume, avg_volume, price_change_pct, price_change_current_bar,
                price_change_1hour, price_change_2hour, price_change_4hour,
                momentum_score, momentum_stage, trends_aligned, volume_price_sync,
                volatility, current_price, volume_score, price_score, trend_score,
                quality_score, volatility_score, volume_zscore, signal_strength,
                atr_normalized_return, volume_spike_threshold,
                ema_21_daily, ema_50_daily, price_vs_ema_21, ema_trend_bias
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            signal.symbol, signal.candle_timestamp, signal.timeframe,
            signal.volume_spike_pct, signal.volume_building, signal.current_volume,
            signal.avg_volume, signal.price_change_pct, signal.price_change_current_bar,
            signal.price_change_1hour, signal.price_change_2hour, signal.price_change_4hour,
            signal.momentum_score, signal.momentum_stage, signal.trends_aligned,
            signal.volume_price_sync, signal.volatility, signal.current_price,
            signal.volume_score, signal.price_score, signal.trend_score,
            signal.quality_score, signal.volatility_score, signal.volume_zscore,
            signal.signal_strength, signal.atr_normalized_return,
            signal.volume_spike_threshold,
            signal.ema_21_daily, signal.ema_50_daily, signal.price_vs_ema_21, signal.ema_trend_bias
        )
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
            self.conn.commit()
            return True
        except pymysql.IntegrityError:
            self.conn.rollback()
            return False    
    
    def alert_exists(self, symbol: str, timeframe: str, bar_close_time: int) -> bool:
        """
        Checks if a specific alert already exists using its unique keys.
        """
        self._ensure_connection()  # Ensure connection is active
        
        sql = """
            SELECT 1 FROM alerts 
            WHERE symbol=%s AND timeframe=%s AND candle_timestamp=%s 
            LIMIT 1
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (symbol, timeframe, bar_close_time))
            return cursor.fetchone() is not None
    
    def cleanup_old(self, days: int = 180):
        """Deletes alerts older than a specified number of days."""
        self._ensure_connection()  # Ensure connection is active
        
        sql = "DELETE FROM alerts WHERE created_at < NOW() - INTERVAL %s DAY"
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (days,))
        self.conn.commit()
