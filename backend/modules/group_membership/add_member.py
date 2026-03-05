from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def add_group_member(db_connector: DBConnector, group_id: int, data: dict):
    """
    Add a user to a group.
    
    Args:
        db_connector (DBConnector): Database connector instance
        group_id (int): ID of the group
        data (dict): User data containing user_id
    
    Returns:
        dict: JSON response with membership details
    """
    try:
        if not group_id:
            return Response.error("group_id is required")
        if not data.get('user_id'):
            return Response.error("user_id is required")
        
        user_id = data.get('user_id')
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("User not found")
        
        # Check if group exists and get max_users
        cursor.execute("SELECT id, max_users, status FROM groups WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        if not group_row:
            conn.close()
            return Response.error("Group not found")
        
        if group_row[2] != 'active':
            conn.close()
            return Response.error("Cannot join inactive group")
        
        # Check if user is already a member
        cursor.execute("""
            SELECT user_id FROM group_users WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        if cursor.fetchone():
            conn.close()
            return Response.error("User is already a member of this group")
        
        # Check if group is full (trigger will also check, but we want a clear error message)
        if group_row[1] is not None:
            cursor.execute("""
                SELECT COUNT(*) FROM group_users WHERE group_id = ?
            """, (group_id,))
            current_count = cursor.fetchone()[0]
            if current_count >= group_row[1]:
                conn.close()
                return Response.error(f"Group is full (max {group_row[1]} members)")
        
        # Add member to group
        cursor.execute("""
            INSERT INTO group_users (user_id, group_id)
            VALUES (?, ?)
        """, (user_id, group_id))
        
        conn.commit()
        
        # Fetch membership details
        cursor.execute("""
            SELECT user_id, group_id, joined_at
            FROM group_users WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        
        row = cursor.fetchone()
        conn.close()
        
        membership_data = {
            'user_id': row[0],
            'group_id': row[1],
            'joined_at': row[2]
        }
        
        return Response.ok(membership_data, "Member added to group successfully")
        
    except Exception as e:
        error_msg = str(e)
        log(f"add_group_member failed for group_id={group_id}, user_id={data.get('user_id') if data else None}: {error_msg}", "error")
        if "Group is full" in error_msg:
            return Response.error("Group is full (max_users reached)")
        return Response.error(f"Failed to add member to group: {error_msg}")