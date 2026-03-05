from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log
import hashlib


def login_user(db_connector: DBConnector, data: dict):
    """
    Authenticate a user with email and password.
    
    Args:
        db_connector (DBConnector): Database connector instance
        data (dict): Login data containing email and password
    
    Returns:
        dict: JSON response with user details if authentication successful
    """
    try:
        # Validate required fields
        if not data.get('email'):
            return Response.error("email is required")
        if not data.get('password'):
            return Response.error("password is required")
        
        email = data.get('email').strip().lower()
        password = data.get('password')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Get user by email and password hash
        cursor.execute("""
            SELECT id, email, role
            FROM users WHERE email = ? AND password_hash = ?
        """, (email, password_hash))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return Response.error("Invalid email or password")

        user_id = row[0]

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'user_email_verifications'
        """)
        has_verification_table = cursor.fetchone() is not None

        if has_verification_table:
            cursor.execute("""
                SELECT verified_at FROM user_email_verifications
                WHERE user_id = ?
            """, (user_id,))
            verification_row = cursor.fetchone()

            if verification_row and verification_row[0] is None:
                conn.close()
                return Response.error("Please verify your email before login")

        conn.close()
        
        user_data = {
            'id': row[0],
            'email': row[1],
            'role': row[2]
        }
        
        return Response.ok(user_data, "Login successful")
        
    except Exception as e:
        log(f"login_user failed: {str(e)}", "error")
        return Response.error(f"Login failed: {str(e)}")
