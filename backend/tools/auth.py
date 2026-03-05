from functools import wraps
from flask import request, jsonify, g

from tools.respone import Response
from tools.logger import log


ROLE_LEVELS = {
	"user": 1,
	"teacher": 2,
	"admin": 3,
}


def _extract_credentials():
	data = request.get_json(silent=True) if request.is_json else {}
	if data is None:
		data = {}

	auth_email = (
		request.headers.get("X-Auth-Email")
		or request.args.get("auth_email")
		or data.get("auth_email")
		or request.args.get("email")
		or data.get("email")
	)

	auth_password_hash = (
		request.headers.get("X-Auth-Password-Hash")
		or request.args.get("auth_password_hash")
		or data.get("auth_password_hash")
		or request.args.get("password_hash")
		or data.get("password_hash")
	)

	if isinstance(auth_email, str):
		auth_email = auth_email.strip().lower()

	return auth_email, auth_password_hash


def require_role(db_connector, minimum_role: str = "user"):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			try:
				email, password_hash = _extract_credentials()

				if not email:
					return jsonify(Response.error("auth_email (oder X-Auth-Email) ist erforderlich")), 401
				if not password_hash:
					return jsonify(Response.error("auth_password_hash (oder X-Auth-Password-Hash) ist erforderlich")), 401

				conn = db_connector.connect()
				cursor = conn.cursor()
				cursor.execute(
					"""
					SELECT id, email, role
					FROM users
					WHERE lower(email) = ? AND password_hash = ?
					""",
					(email, password_hash),
				)
				row = cursor.fetchone()
				conn.close()

				if not row:
					return jsonify(Response.error("Ungültige Authentifizierungsdaten")), 401

				user_role = (row[2] or "user").lower()
				required_level = ROLE_LEVELS.get((minimum_role or "user").lower(), 1)
				user_level = ROLE_LEVELS.get(user_role, 0)

				if user_level < required_level:
					return jsonify(Response.error(f"Unzureichende Rolle: benötigt {minimum_role}")), 403

				g.auth_user = {
					"id": row[0],
					"email": row[1],
					"role": user_role,
				}

				return func(*args, **kwargs)
			except Exception as e:
				log(f"Auth check failed: {str(e)}", "error")
				return jsonify(Response.error("Authentifizierung fehlgeschlagen")), 500

		return wrapper

	return decorator