from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def report_group(db_connector: DBConnector, group_id: int, data: dict = None):
    """
    Report a group for violating guidelines.
    
    Args:
        db_connector (DBConnector): Database connector instance
        group_id (int): ID of the group to report
        data (dict): Report details (optional, for future use)
    
    Returns:
        dict: JSON response with report confirmation
    """
    try:
        if not group_id:
            return Response.error("group_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id, reports FROM groups WHERE id = ?", (group_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return Response.error("Group not found")
        
        current_reports = row[1]
        
        # Increment reports counter
        cursor.execute("""
            UPDATE groups 
            SET reports = reports + 1 
            WHERE id = ?
        """, (group_id,))
        
        conn.commit()
        conn.close()
        
        return Response.ok({
            'group_id': group_id,
            'reports': current_reports + 1
        }, "Group reported successfully")
        
    except Exception as e:
        log(f"report_group failed for group_id={group_id}: {str(e)}", "error")
        return Response.error(f"Failed to report group: {str(e)}")