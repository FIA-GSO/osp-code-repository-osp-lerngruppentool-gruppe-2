from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.bad_word_filter import contains_bad_word
from tools.logger import log
import hashlib


def update_user(db_connector: DBConnector, user_id: int, data: dict):
    """
    Update user information.
    
    Args:
        db_connector (DBConnector): Database connector instance
        user_id (int): ID of the user to update
        data (dict): Updated user data (email and/or password)
    
    Returns:
        dict: JSON response with updated user details
    """
    try:
        if not user_id:
            return Response.error("user_id is required")
        if not data:
            return Response.error("No update data provided")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("User not found")
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        if 'email' in data and data['email'].endswith("@gso.schule.koeln"):
            email = data['email'].strip().lower()
            # Basic email validation
            if '@' not in email or '.' not in email:
                conn.close()
                return Response.error("Invalid email format")
            
            # Check for bad words in email
            if contains_bad_word(email):
                conn.close()
                return Response.error("Email contains inappropriate language")
            
            # Check if email already exists for another user
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
            if cursor.fetchone():
                conn.close()
                return Response.error("Email already exists")
            
            update_fields.append("email = ?")
            params.append(email)

        elif 'email' in data and not data['email'].endswith("@gso.schule.koeln"):
            conn.close()
            return Response.error("Email must be a GSO email address")
        
        if 'password' in data:
            password = data['password']
            if not password:
                conn.close()
                return Response.error("Password cannot be empty")
            
            # Hash password (using SHA-256 for simplicity, consider bcrypt for production)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            update_fields.append("password_hash = ?")
            params.append(password_hash)
        
        if not update_fields:
            conn.close()
            return Response.error("No valid fields to update")
        
        # Update user
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        # Fetch updated user (without password hash)
        cursor.execute("""
            SELECT id, email
            FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        user_data = {
            'id': row[0],
            'email': row[1]
        }
        
        return Response.ok(user_data, "User updated successfully")
        
    except Exception as e:
        log(f"update_user failed for user_id={user_id}: {str(e)}", "error")
        return Response.error(f"Failed to update user: {str(e)}")