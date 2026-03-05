("""
Simple SQLite database helper for initializing schema and populating test data.

Provides:
- `Database.init_db()` to create tables, indexes and triggers.
- `Database.populate_test_data()` to insert 20 users, 20 groups and 20 memberships.
""")
import sqlite3
import random
from tools.logger import log


class Database:
	def __init__(self, db_path: str):
		self.db_path = db_path

	def _connect(self) -> sqlite3.Connection:
		conn = sqlite3.connect(self.db_path)
		conn.execute("PRAGMA foreign_keys = ON;")
		return conn

	def init_db(self) -> None:
		"""Create tables, indexes and triggers according to the provided schema."""
		log(f"Initializing database schema for {self.db_path}")
		schema = '''
PRAGMA foreign_keys = ON;
-- users
CREATE TABLE IF NOT EXISTS users (
	id            INTEGER PRIMARY KEY,
	email         TEXT NOT NULL UNIQUE,
	password_hash TEXT NOT NULL, 
	role		  TEXT NOT NULL DEFAULT 'user' -- 'user', 'teacher' or 'admin'
);
-- user_email_verifications (double opt-in)
CREATE TABLE IF NOT EXISTS user_email_verifications (
	user_id    INTEGER PRIMARY KEY,
	token_hash TEXT,
	expires_at TEXT,
	verified_at TEXT,
	created_at TEXT NOT NULL DEFAULT (datetime('now')),
	FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
);
-- groups
CREATE TABLE IF NOT EXISTS groups (
	id              INTEGER PRIMARY KEY,
	organiser_id    INTEGER NOT NULL,
	title           TEXT NOT NULL,
	subject         TEXT,
	topic           TEXT,
	description     TEXT,
	class           TEXT,
	type            TEXT,
	location        TEXT,
	max_users       INTEGER,
	status          TEXT NOT NULL DEFAULT 'active',
	created_at      TEXT NOT NULL DEFAULT (datetime('now')),
	last_active_at  TEXT,
	reports         INTEGER NOT NULL DEFAULT 0,
	FOREIGN KEY (organiser_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT,
	CHECK (max_users IS NULL OR max_users >= 0)
);
-- group_users (membership)
CREATE TABLE IF NOT EXISTS group_users (
	user_id   INTEGER NOT NULL,
	group_id  INTEGER NOT NULL,
	joined_at TEXT NOT NULL DEFAULT (datetime('now')),
	PRIMARY KEY (user_id, group_id),
	FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (group_id) REFERENCES groups(id) ON UPDATE CASCADE ON DELETE CASCADE
);
-- join_requests (Beitrittsanfragen)
CREATE TABLE IF NOT EXISTS join_requests (
	id           INTEGER PRIMARY KEY,
	user_id      INTEGER NOT NULL,
	group_id     INTEGER NOT NULL,
	message      TEXT,
	status       TEXT NOT NULL DEFAULT 'pending',
	created_at   TEXT NOT NULL DEFAULT (datetime('now')),
	responded_at TEXT,
	FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (group_id) REFERENCES groups(id) ON UPDATE CASCADE ON DELETE CASCADE,
	CHECK (status IN ('pending', 'approved', 'rejected')),
	UNIQUE (user_id, group_id)
);
CREATE INDEX IF NOT EXISTS idx_group_users_group_id ON group_users(group_id);
CREATE INDEX IF NOT EXISTS idx_groups_organiser_id ON groups(organiser_id);
CREATE INDEX IF NOT EXISTS idx_join_requests_group_id ON join_requests(group_id);
CREATE INDEX IF NOT EXISTS idx_join_requests_user_id ON join_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_email_verifications_token_hash ON user_email_verifications(token_hash);

-- 1) Trigger: max_users nicht überschreiten
CREATE TRIGGER IF NOT EXISTS trg_group_users_limit_before_insert
BEFORE INSERT ON group_users FOR EACH ROW
BEGIN
	SELECT CASE WHEN (SELECT max_users FROM groups WHERE id = NEW.group_id) IS NOT NULL
		AND (SELECT COUNT(*) FROM group_users WHERE group_id = NEW.group_id) >= (SELECT max_users FROM groups WHERE id = NEW.group_id)
	THEN RAISE(ABORT, 'Group is full (max_users reached)') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_group_users_limit_before_update
BEFORE UPDATE OF group_id ON group_users FOR EACH ROW
BEGIN
	SELECT CASE WHEN (SELECT max_users FROM groups WHERE id = NEW.group_id) IS NOT NULL
		AND (SELECT COUNT(*) FROM group_users WHERE group_id = NEW.group_id) >= (SELECT max_users FROM groups WHERE id = NEW.group_id)
	THEN RAISE(ABORT, 'Group is full (max_users reached)') END;
END;

-- 2) Trigger: last_active_at automatisch pflegen
CREATE TRIGGER IF NOT EXISTS trg_groups_last_active_after_member_insert
AFTER INSERT ON group_users FOR EACH ROW
BEGIN
	UPDATE groups SET last_active_at = datetime('now') WHERE id = NEW.group_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_groups_last_active_after_member_delete
AFTER DELETE ON group_users FOR EACH ROW
BEGIN
	UPDATE groups SET last_active_at = datetime('now') WHERE id = OLD.group_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_groups_last_active_after_member_update
AFTER UPDATE OF group_id ON group_users FOR EACH ROW
BEGIN
	UPDATE groups SET last_active_at = datetime('now') WHERE id IN (OLD.group_id, NEW.group_id);
END;
'''

		conn = self._connect()
		try:
			conn.executescript(schema)
			conn.commit()
			log(f"Database schema initialized for {self.db_path}")
		except Exception as e:
			log(f"Failed to initialize database schema for {self.db_path}: {e}", "error")
			raise
		finally:
			conn.close()

	def populate_test_data(self) -> None:
		"""Fill the database with x users, x groups and x memberships.

		- All groups will have `max_users` = NULL (unlimited) to avoid trigger conflicts.
		- Emails and names are deterministic for easy inspection.
		"""
		create_sum = 20
		conn = self._connect()
		try:
			cur = conn.cursor()
			
			# Check if test data already exists
			cur.execute("SELECT COUNT(*) FROM users")
			if cur.fetchone()[0] > 0:
				log("Test data already exists, skipping test data population")
				return # Avoid duplicate test data
			
			# Insert users
			# Possible names
			names = ["farbian", "celinna", "arndte", "morris", "farbiarndt"]
			surnameChars = "abcdefghijklmnopqrstuvwxyz"
			users = []
			for i in range(1, create_sum + 1):
				name = f"{names[i % len(names)]}.{surnameChars[i]}1"
				email = f"{name}@gso.schule.koeln"
				password_hash = f"hash{i}"
				users.append((email, password_hash))
			cur.executemany("INSERT INTO users (email, password_hash) VALUES (?,?)", users)

			# gather user ids
			cur.execute("SELECT id FROM users ORDER BY id")
			user_ids = [r[0] for r in cur.fetchall()]

			# Insert groups (max_users left NULL)
			subjects = ["EvP", "SuD", "WuB", "FU1", "Politik"]
			topics = ["Linux", "MySQL", "Projektmanagement", "Webentwicklung", "WISO-Basics"]
			descriptions = ["Raspberry Pi", "Datenbanken", "Agiles Arbeiten", "HTML5, CSS3 und JS", "Betriebsrat"]
			groups = []
			for i in range(1, create_sum + 1):
				organiser = random.choice(user_ids)
				title = f"Gruppe {i}"
				subject = random.choice(subjects)
				topic = topics[subjects.index(subject)]
				description = descriptions[subjects.index(subject)]
				class_name = random.choice(["FIA3A", "FI302", "FIS3A", "FI102", "FI202"])
				type_ = random.choice(["online", "in-person"])
				location = ("Teams" if type_ == "online" else f"Raum {random.choice(['A', 'B', 'C'])} {random.randint(1,50)}")
				max_users = None
				status = random.choice(["aktiv", "inaktiv"])
				groups.append((organiser, title, subject, topic, description, class_name, type_, location, max_users, status))

			cur.executemany(
				"""INSERT INTO groups (organiser_id, title, subject, topic, description, class, type, location, max_users, status)
				VALUES (?,?,?,?,?,?,?,?,?,?)""",
				groups,
			)

			# gather group ids
			cur.execute("SELECT id FROM groups ORDER BY id")
			group_ids = [r[0] for r in cur.fetchall()]

			# Insert unique memberships (group_users)
			memberships = set()
			rows = []
			while len(rows) < create_sum:
				u = random.choice(user_ids)
				g = random.choice(group_ids)
				if (u, g) in memberships:
					continue
				memberships.add((u, g))
				rows.append((u, g))

			cur.executemany("INSERT INTO group_users (user_id, group_id) VALUES (?,?)", rows)

			# Insert admin
			admin_email = "admin@gso.schule.koeln"
			admin_hash = "8543f5f3406167609396a21adb8c7a306f9d74a1d43222e0b19379edfd4e89ef"  # Password hash for "fabo_boss" (SHA256)
			cur.execute("SELECT id, role FROM users WHERE email = ?", (admin_email,))
			existing_admin_user = cur.fetchone()
			if existing_admin_user:
				if existing_admin_user[1] != "admin":
					cur.execute(
						"UPDATE users SET role = 'admin', password_hash = ? WHERE id = ?",
						(admin_hash, existing_admin_user[0]),
					)
					log("Existing user with admin email promoted to admin")
				else:
					cur.execute(
						"UPDATE users SET password_hash = ? WHERE id = ?",
						(admin_hash, existing_admin_user[0]),
					)
					log("Admin user already exists, password hash refreshed")
			else:
				cur.execute(
					"INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
					(admin_email, admin_hash),
				)
				log("Admin user created")
			conn.commit()

			conn.commit()
			log(f"Test data populated successfully for {self.db_path}")
		except Exception as e:
			log(f"Failed to populate test data for {self.db_path}: {e}", "error")
			raise
		finally:
			conn.close()

