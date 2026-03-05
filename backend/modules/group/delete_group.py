from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def delete_group(db_connector: DBConnector, group_id: int):
    """
    Delete a group.
    
    Args:
        db_connector (DBConnector): Database connector instance
        group_id (int): ID of the group to delete
    
    Returns:
        dict: JSON response with deletion status
    """
    try:
        if not group_id:
            return Response.error("group_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("Group not found")
        
        # Delete group (cascade will delete group_users entries)
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()
        conn.close()
        
        return Response.ok(message="Group deleted successfully")
        
    except Exception as e:
        log(f"delete_group failed for group_id={group_id}: {str(e)}", "error")
        return Response.error(f"Failed to delete group: {str(e)}")