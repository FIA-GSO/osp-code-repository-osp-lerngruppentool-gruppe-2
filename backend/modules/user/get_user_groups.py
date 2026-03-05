from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def get_user_groups(db_connector: DBConnector, user_id: int, role: str = None):
    """
    Get all groups associated with a user.
    
    Args:
        db_connector (DBConnector): Database connector instance
        user_id (int): ID of the user
        role (str): Optional filter - 'member' (all memberships), 'organiser' (organised groups), or None (both)
    
    Returns:
        dict: JSON response with list of groups
    """
    try:
        if not user_id:
            return Response.error("user_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("User not found")
        
        groups = []
        
        # Get groups where user is a member
        if role is None or role == 'member':
            cursor.execute("""
                SELECT g.id, g.organiser_id, g.title, g.subject, g.topic, g.description, 
                       g.class, g.type, g.location, g.max_users, g.status, g.created_at, 
                       g.last_active_at, g.reports, gu.joined_at,
                       COUNT(gu2.user_id) as member_count,
                       'member' as user_role
                FROM groups g
                JOIN group_users gu ON g.id = gu.group_id
                LEFT JOIN group_users gu2 ON g.id = gu2.group_id
                WHERE gu.user_id = ?
                GROUP BY g.id
                ORDER BY gu.joined_at DESC
            """, (user_id,))
            
            for row in cursor.fetchall():
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
                    'joined_at': row[14],
                    'member_count': row[15],
                    'user_role': row[16],
                    'is_organiser': row[1] == user_id
                })
        
        # Get groups where user is the organiser (if not already included)
        if role == 'organiser':
            cursor.execute("""
                SELECT g.id, g.organiser_id, g.title, g.subject, g.topic, g.description, 
                       g.class, g.type, g.location, g.max_users, g.status, g.created_at, 
                       g.last_active_at, g.reports,
                       COUNT(gu.user_id) as member_count
                FROM groups g
                LEFT JOIN group_users gu ON g.id = gu.group_id
                WHERE g.organiser_id = ?
                GROUP BY g.id
                ORDER BY g.created_at DESC
            """, (user_id,))
            
            for row in cursor.fetchall():
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
                    'member_count': row[14],
                    'user_role': 'organiser',
                    'is_organiser': True
                })
        
        conn.close()
        
        return Response.ok({
            'groups': groups,
            'count': len(groups)
        }, "User groups retrieved successfully")
        
    except Exception as e:
        log(f"get_user_groups failed for user_id={user_id}: {str(e)}", "error")
        return Response.error(f"Failed to retrieve user groups: {str(e)}")
