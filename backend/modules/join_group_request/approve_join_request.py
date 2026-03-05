from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log
from tools import email_sender


def approve_join_request(db_connector: DBConnector, request_id: int):
    """
    Approve a membership request and add the user to the group.
    
    Args:
        db_connector (DBConnector): Database connector instance
        request_id (int): ID of the request to approve
    
    Returns:
        dict: JSON response with approval status
    """
    try:
        if not request_id:
            return Response.error("request_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Get request details
        cursor.execute("""
            SELECT id, user_id, group_id, status 
            FROM join_requests WHERE id = ?
        """, (request_id,))
        
        request_row = cursor.fetchone()
        if not request_row:
            conn.close()
            return Response.error("Join request not found")
        
        if request_row[3] != 'pending':
            conn.close()
            return Response.error(f"Request already {request_row[3]}")
        
        user_id = request_row[1]
        group_id = request_row[2]
        
        # Check if user is already a member (race condition check)
        cursor.execute("""
            SELECT user_id FROM group_users WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        if cursor.fetchone():
            conn.close()
            return Response.error("User is already a member of this group")
        
        # Check if group is full
        cursor.execute("SELECT max_users FROM groups WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        if group_row and group_row[0] is not None:
            cursor.execute("""
                SELECT COUNT(*) FROM group_users WHERE group_id = ?
            """, (group_id,))
            current_count = cursor.fetchone()[0]
            if current_count >= group_row[0]:
                conn.close()
                return Response.error(f"Group is full (max {group_row[0]} members)")
        
        try:
            # Add user to group
            cursor.execute("""
                INSERT INTO group_users (user_id, group_id)
                VALUES (?, ?)
            """, (user_id, group_id))

            # Resolve requester email before closing connection
            cursor.execute("""
                SELECT email FROM users WHERE id = ?
            """, (user_id,))
            user_row = cursor.fetchone()
            user_email = user_row[0] if user_row else None
            
            # Update request status
            cursor.execute("""
                UPDATE join_requests 
                SET status = 'approved', responded_at = datetime('now')
                WHERE id = ?
            """, (request_id,))
            
            conn.commit()
            conn.close()

            # Send notification email to user
            if user_email:
                email_sender.send_email(
                    to=user_email,
                    subject="Join Request Approved",
                    body=f"Your request to join group {group_id} has been approved."
                )
            
            return Response.ok({
                'request_id': request_id,
                'user_id': user_id,
                'group_id': group_id
            }, "Join request approved and user added to group")
            
        except Exception as e:
            conn.rollback()
            conn.close()
            error_msg = str(e)
            log(f"approve_join_request transaction failed for request_id={request_id}: {error_msg}", "error")
            if "Group is full" in error_msg:
                return Response.error("Group is full (max_users reached)")
            raise
        
    except Exception as e:
        log(f"approve_join_request failed for request_id={request_id}: {str(e)}", "error")
        return Response.error(f"Failed to approve join request: {str(e)}")


def reject_join_request(db_connector: DBConnector, request_id: int):
    """
    Reject a membership request.
    
    Args:
        db_connector (DBConnector): Database connector instance
        request_id (int): ID of the request to reject
    
    Returns:
        dict: JSON response with rejection status
    """
    try:
        if not request_id:
            return Response.error("request_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if request exists and is pending
        cursor.execute("""
            SELECT id, status FROM join_requests WHERE id = ?
        """, (request_id,))
        
        request_row = cursor.fetchone()
        if not request_row:
            conn.close()
            return Response.error("Join request not found")
        
        if request_row[1] != 'pending':
            conn.close()
            return Response.error(f"Request already {request_row[1]}")
        
        # Update request status to rejected
        cursor.execute("""
            UPDATE join_requests 
            SET status = 'rejected', responded_at = datetime('now')
            WHERE id = ?
        """, (request_id,))
        
        conn.commit()
        conn.close()
        
        return Response.ok({'request_id': request_id}, "Join request rejected")
        
    except Exception as e:
        log(f"reject_join_request failed for request_id={request_id}: {str(e)}", "error")
        return Response.error(f"Failed to reject join request: {str(e)}")
