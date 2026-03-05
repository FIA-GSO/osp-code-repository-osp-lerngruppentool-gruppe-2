from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def remove_group_member(db_connector: DBConnector, group_id: int, user_id: int):
    """
    Remove a user from a group.
    
    Args:
        db_connector (DBConnector): Database connector instance
        group_id (int): ID of the group
        user_id (int): ID of the user to remove
    
    Returns:
        dict: JSON response with removal status
    """
    try:
        if not group_id:
            return Response.error("group_id is required")
        if not user_id:
            return Response.error("user_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id, organiser_id FROM groups WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        if not group_row:
            conn.close()
            return Response.error("Group not found")
        
        organiser_id = group_row[1]
        
        # Check if user is a member
        cursor.execute("""
            SELECT user_id FROM group_users WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        if not cursor.fetchone():
            conn.close()
            return Response.error("User is not a member of this group")
        
        # Prevent removing the organiser
        if user_id == organiser_id:
            conn.close()
            return Response.error("Cannot remove the group organiser from the group")
        
        # Remove member from group
        cursor.execute("""
            DELETE FROM group_users WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        
        conn.commit()
        conn.close()
        
        return Response.ok(message="Member removed from group successfully")
        
    except Exception as e:
        log(f"remove_group_member failed for group_id={group_id}, user_id={user_id}: {str(e)}", "error")
        return Response.error(f"Failed to remove member from group: {str(e)}")