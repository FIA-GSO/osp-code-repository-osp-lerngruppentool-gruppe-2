from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def get_all_groups(db_connector: DBConnector, limit: int = 20, offset: int = 0, search: str = None):
    """
    Retrieve all groups with pagination and search functionality.
    
    Args:
        db_connector (DBConnector): Database connector instance
        limit (int): Maximum number of groups to return (default 20)
        offset (int): Number of groups to skip (default 0)
        search (str): Search query for filtering groups by title, subject, topic, or description
    
    Returns:
        dict: JSON response with groups list and pagination info
    """
    try:
        # Validate and set defaults
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        if limit < 1:
            return Response.error("limit must be at least 1")
        if offset < 0:
            return Response.error("offset must be >= 0")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Build query with search filter
        base_query = """
            SELECT g.id, g.organiser_id, g.title, g.subject, g.topic, g.description, 
                   g.class, g.type, g.location, g.max_users, g.status, g.created_at, 
                   g.last_active_at, g.reports,
                   COUNT(gu.user_id) as member_count
            FROM groups g
            LEFT JOIN group_users gu ON g.id = gu.group_id
        """
        
        count_query = "SELECT COUNT(*) FROM groups g"
        params = []
        
        if search:
            search_condition = """
                WHERE g.title LIKE ? OR g.subject LIKE ? OR g.topic LIKE ? 
                OR g.description LIKE ? OR g.class LIKE ?
            """
            search_param = f"%{search}%"
            params = [search_param, search_param, search_param, search_param, search_param]
            base_query += search_condition
            count_query += search_condition
        
        # Get total count
        if search:
            cursor.execute(count_query, params)
        else:
            cursor.execute(count_query)
        total = cursor.fetchone()[0]
        
        # Get groups with pagination
        base_query += " GROUP BY g.id ORDER BY g.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(base_query, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        groups = []
        for row in rows:
            groups.append({
                'id': row[0],
                'organiser_id': row[1],
                'title': row[2],
                'subject': row[3],
                'topic': row[4],
                'description': row[5],
                'class': row[6],
                'type': row[7],
                'location': row[8],
                'max_users': row[9],
                'status': row[10],
                'created_at': row[11],
                'last_active_at': row[12],
                'reports': row[13],
                'member_count': row[14]
            })
        
        return Response.ok({
            'groups': groups,
            'total': total,
            'limit': limit,
            'offset': offset
        }, "Groups retrieved successfully")
        
    except Exception as e:
        log(f"get_all_groups failed: {str(e)}", "error")
        return Response.error(f"Failed to retrieve groups: {str(e)}")