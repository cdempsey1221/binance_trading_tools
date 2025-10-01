import sqlite3
import threading
from typing import Optional

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
