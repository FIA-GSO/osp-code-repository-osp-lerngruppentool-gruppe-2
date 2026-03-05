
import sqlite3
from tools.logger import log

class DBConnector:
	def __init__(self, db_path):
		self.db_path = db_path
		# Test connection on init
		try:
			conn = sqlite3.connect(self.db_path)
			conn.execute("PRAGMA foreign_keys = ON;")
			conn.close()
			log(f"DB connection initialized successfully for {self.db_path}")
		except Exception as e:
			log(f"DB connection initialization failed for {self.db_path}: {e}", "error")
			raise RuntimeError(f"DB connection failed: {e}")

	def connect(self):
		# Returns a new connection with foreign keys enabled
		try:
			conn = sqlite3.connect(self.db_path)
			conn.execute("PRAGMA foreign_keys = ON;")
			return conn
		except Exception as e:
			log(f"Failed to create DB connection for {self.db_path}: {e}", "error")
			raise RuntimeError(f"Failed to create DB connection: {e}")