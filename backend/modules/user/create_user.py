from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.bad_word_filter import contains_bad_word
from tools.logger import log
from tools.email_sender import send_template_email
import hashlib
import secrets
from datetime import datetime, timedelta


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _token_expiry_utc(hours: int = 24) -> str:
    return (datetime.utcnow() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")


def _build_confirmation_link(raw_token: str, email: str) -> str:
    return f"http://127.0.0.1:5000/api/users/verify-email?token={raw_token}&email={email}"


def create_user(db_connector: DBConnector, data: dict):
    """
    Create a new user.
    
    Args:
        db_connector (DBConnector): Database connector instance
        data (dict): User data containing email and password
    
    Returns:
        dict: JSON response with created user details
    """
    try:
        # Validate required fields
        if not data.get('email'):
            return Response.error("email is required")
        if not data.get('password'):
            return Response.error("password is required")
        
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # GSO email validation
        if not email.endswith("@gso.schule.koeln"):
            return Response.error("Email must be a GSO email address")
        
        # Check for bad words in email
        if contains_bad_word(email):
            return Response.error("Email contains inappropriate language")
        
        # Hash password (using SHA-256 for simplicity, consider bcrypt for production)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return Response.error("Email already exists")
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        """, (email, password_hash))
        
        user_id = cursor.lastrowid

        raw_token = secrets.token_urlsafe(32)
        token_hash = _token_hash(raw_token)
        expires_at = _token_expiry_utc(24)

        cursor.execute("""
            INSERT OR REPLACE INTO user_email_verifications (user_id, token_hash, expires_at, verified_at)
            VALUES (?, ?, ?, NULL)
        """, (user_id, token_hash, expires_at))

        conn.commit()
        
        # Fetch created user (without password hash)
        cursor.execute("""
            SELECT id, email
            FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()

        confirmation_link = _build_confirmation_link(raw_token, email)
        try:
            send_template_email(
                email_address=email,
                template_type="double_opt_in",
                placeholders={
                    "user_name": email.split(".")[0],
                    "confirmation_link": confirmation_link
                }
            )
        except Exception as mail_error:
            log(f"create_user DOI email send failed for {email}: {str(mail_error)}", "error")
            return Response.error(
                "User created, but verification email could not be sent. Please contact support.",
                {
                    "user_id": user_id,
                    "email": email
                }
            )
        
        user_data = {
            'id': row[0],
            'email': row[1],
            'email_verified': False,
            'verification_required': True
        }
        
        return Response.ok(user_data, "User created. Please verify your email address.")
        
    except Exception as e:
        log(f"create_user failed: {str(e)}", "error")
        return Response.error(f"Failed to create user: {str(e)}")


def verify_user_email(db_connector: DBConnector, token: str, email: str | None = None):
    """
    Verify a user's email via double opt-in token.
    """
    try:
        if not token:
            return Response.error("token is required")

        token_hash = _token_hash(token)
        conn = db_connector.connect()
        cursor = conn.cursor()

        query = """
            SELECT u.id, u.email, v.expires_at, v.verified_at
            FROM user_email_verifications v
            JOIN users u ON u.id = v.user_id
            WHERE v.token_hash = ?
        """
        params = [token_hash]

        if email:
            query += " AND u.email = ?"
            params.append(email.strip().lower())

        cursor.execute(query, tuple(params))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return Response.error("Invalid verification token")

        user_id, user_email, expires_at, verified_at = row

        if verified_at is not None:
            conn.close()
            return Response.ok({"email": user_email, "email_verified": True}, "Email already verified")

        cursor.execute("SELECT datetime('now')")
        now_utc = cursor.fetchone()[0]
        if expires_at is None or expires_at <= now_utc:
            conn.close()
            return Response.error("Verification token expired")

        cursor.execute("""
            UPDATE user_email_verifications
            SET verified_at = datetime('now'), token_hash = NULL, expires_at = NULL
            WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        conn.close()

        return Response.ok(
            {
                "user_id": user_id,
                "email": user_email,
                "email_verified": True
            },
            "Email verified successfully"
        )

    except Exception as e:
        log(f"verify_user_email failed: {str(e)}", "error")
        return Response.error(f"Failed to verify email: {str(e)}")