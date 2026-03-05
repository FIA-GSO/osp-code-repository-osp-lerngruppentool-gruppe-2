from tools import email_sender
from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def delete_beitrittsanfrage(db_connector: DBConnector, request_id: int):
    """
    Delete/decline a membership request.
    
    Args:
        db_connector (DBConnector): Database connector instance
        request_id (int): ID of the request to delete
    
    Returns:
        dict: JSON response with deletion status
    """
    try:
        if not request_id:
            return Response.error("request_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if request exists
        cursor.execute("""
            SELECT r.id, u.email FROM join_requests r
            JOIN users u ON u.id = r.user_id
            WHERE r.id = ?
        """, (request_id,))
        request_row = cursor.fetchone()
        if not request_row:
            conn.close()
            return Response.error("Join request not found")
        user_email = request_row[1]
        
        # Delete request
        cursor.execute("DELETE FROM join_requests WHERE id = ?", (request_id,))
        conn.commit()
        conn.close()

        # Notification email to user
        if user_email:
            email_sender.send_email(
                to=user_email,
                subject="Join Request Deleted",
                body=f"Your request to join a group has been deleted."
            )

        return Response.ok(message="Join request deleted successfully")
        
    except Exception as e:
        log(f"delete_beitrittsanfrage failed for request_id={request_id}: {str(e)}", "error")
        return Response.error(f"Failed to delete join request: {str(e)}")