from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def get_join_requests(db_connector: DBConnector, group_id: int = None, user_id: int = None, status: str = None):
    """
    Get membership requests with optional filters.
    
    Args:
        db_connector (DBConnector): Database connector instance
        group_id (int): Optional - filter by group ID
        user_id (int): Optional - filter by user ID
        status (str): Optional - filter by status (pending, approved, rejected)
    
    Returns:
        dict: JSON response with list of join requests
    """
    try:
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Build query with filters
        query = """
            SELECT jr.id, jr.user_id, jr.group_id, jr.message, jr.status, 
                   jr.created_at, jr.responded_at,
                   u.email, g.title
            FROM join_requests jr
            JOIN users u ON jr.user_id = u.id
            JOIN groups g ON jr.group_id = g.id
            WHERE 1=1
        """
        params = []
        
        if group_id is not None:
            query += " AND jr.group_id = ?"
            params.append(group_id)
        
        if user_id is not None:
            query += " AND jr.user_id = ?"
            params.append(user_id)
        
        if status:
            if status not in ['pending', 'approved', 'rejected']:
                conn.close()
                return Response.error("Invalid status. Must be: pending, approved, or rejected")
            query += " AND jr.status = ?"
            params.append(status)
        
        query += " ORDER BY jr.created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        requests = []
        for row in rows:
            requests.append({
                'id': row[0],
                'user_id': row[1],
                'group_id': row[2],
                'message': row[3],
                'status': row[4],
                'created_at': row[5],
                'responded_at': row[6],
                'user_email': row[7],
                'group_title': row[8]
            })
        
        return Response.ok({
            'requests': requests,
            'count': len(requests)
        }, "Join requests retrieved successfully")
        
    except Exception as e:
        log(f"get_join_requests failed: {str(e)}", "error")
        return Response.error(f"Failed to retrieve join requests: {str(e)}")


def get_join_request_by_id(db_connector: DBConnector, request_id: int):
    """
    Get a specific membership request by ID.
    
    Args:
        db_connector (DBConnector): Database connector instance
        request_id (int): ID of the request to get
    
    Returns:
        dict: JSON response with request details
    """
    try:
        if not request_id:
            return Response.error("request_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT jr.id, jr.user_id, jr.group_id, jr.message, jr.status, 
                   jr.created_at, jr.responded_at,
                   u.email, g.title
            FROM join_requests jr
            JOIN users u ON jr.user_id = u.id
            JOIN groups g ON jr.group_id = g.id
            WHERE jr.id = ?
        """, (request_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return Response.error("Join request not found")
        
        request_data = {
            'id': row[0],
            'user_id': row[1],
            'group_id': row[2],
            'message': row[3],
            'status': row[4],
            'created_at': row[5],
            'responded_at': row[6],
            'user_email': row[7],
            'group_title': row[8]
        }
        
        return Response.ok(request_data, "Join request retrieved successfully")
        
    except Exception as e:
        log(f"get_join_request_by_id failed for request_id={request_id}: {str(e)}", "error")
        return Response.error(f"Failed to retrieve join request: {str(e)}")