from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def get_user(db_connector: DBConnector, user_id: int):
    """
    Retrieve user information.
    
    Args:
        db_connector (DBConnector): Database connector instance
        user_id (int): ID of the user to retrieve
    
    Returns:
        dict: JSON response with user details
    """
    try:
        if not user_id:
            return Response.error("user_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Get user details (excluding password_hash)
        cursor.execute("""
            SELECT id, email
            FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return Response.error("User not found")
        
        # Get user's group memberships count
        cursor.execute("""
            SELECT COUNT(*) FROM group_users WHERE user_id = ?
        """, (user_id,))
        group_count = cursor.fetchone()[0]
        
        # Get user's organised groups count
        cursor.execute("""
            SELECT COUNT(*) FROM groups WHERE organiser_id = ?
        """, (user_id,))
        organised_count = cursor.fetchone()[0]
        
        conn.close()
        
        user_data = {
            'id': row[0],
            'email': row[1],
            'group_memberships': group_count,
            'organised_groups': organised_count
        }
        
        return Response.ok(user_data, "User retrieved successfully")
        
    except Exception as e:
        log(f"get_user failed for user_id={user_id}: {str(e)}", "error")
        return Response.error(f"Failed to retrieve user: {str(e)}")


def get_all_users(db_connector: DBConnector, limit: int = 50, offset: int = 0, search: str = None):
    """
    Retrieve all users with pagination and search functionality.
    
    Args:
        db_connector (DBConnector): Database connector instance
        limit (int): Maximum number of users to return (default 50)
        offset (int): Number of users to skip (default 0)
        search (str): Search query for filtering users by email
    
    Returns:
        dict: JSON response with users list and pagination info
    """
    try:
        # Validate and set defaults
        try:
            limit = int(limit) if limit is not None else 50
            offset = int(offset) if offset is not None else 0
        except (ValueError, TypeError):
            return Response.error("limit and offset must be valid integers")
        
        if limit < 1:
            return Response.error("limit must be at least 1")
        if offset < 0:
            return Response.error("offset must be >= 0")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Build query with search filter
        base_query = "SELECT id, email FROM users"
        count_query = "SELECT COUNT(*) FROM users"
        params = []
        
        if search:
            search_condition = " WHERE email LIKE ?"
            search_param = f"%{search}%"
            params = [search_param]
            base_query += search_condition
            count_query += search_condition
        
        # Get total count
        if search:
            cursor.execute(count_query, params)
        else:
            cursor.execute(count_query)
        total = cursor.fetchone()[0]
        
        # Get users with pagination
        base_query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(base_query, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'email': row[1]
            })
        
        return Response.ok({
            'users': users,
            'total': total,
            'limit': limit,
            'offset': offset
        }, "Users retrieved successfully")
        
    except Exception as e:
        log(f"get_all_users failed: {str(e)}", "error")
        return Response.error(f"Failed to retrieve users: {str(e)}")