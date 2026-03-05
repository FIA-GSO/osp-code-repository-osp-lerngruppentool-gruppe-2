from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log
from tools import email_sender


def create_beitrittsanfrage(db_connector: DBConnector, data: dict):
    """
    Create a membership request (Beitrittsanfrage) for a group.
    
    Args:
        db_connector (DBConnector): Database connector instance
        data (dict): Request data containing user_id, group_id, and optional message
    
    Returns:
        dict: JSON response with request details
    """
    try:
        if not data.get('user_id'):
            return Response.error("user_id is required")
        if not data.get('group_id'):
            return Response.error("group_id is required")
        
        user_id = data.get('user_id')
        group_id = data.get('group_id')
        message = data.get('message', '')
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("User not found")
        
        # Check if group exists and is active
        cursor.execute("SELECT id, status, max_users FROM groups WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        if not group_row:
            conn.close()
            return Response.error("Group not found")
        
        if group_row[1] != 'active':
            conn.close()
            return Response.error("Cannot request to join inactive group")
        
        # Check if user is already a member
        cursor.execute("""
            SELECT user_id FROM group_users WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        if cursor.fetchone():
            conn.close()
            return Response.error("User is already a member of this group")
        
        # Check if there's already a pending request
        cursor.execute("""
            SELECT id, status FROM join_requests 
            WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        existing_request = cursor.fetchone()
        if existing_request:
            if existing_request[1] == 'pending':
                conn.close()
                return Response.error("A pending join request already exists")
            # If there's a rejected/approved request, allow creating a new one by deleting old
            cursor.execute("""
                DELETE FROM join_requests WHERE user_id = ? AND group_id = ?
            """, (user_id, group_id))
        
        # Check if group is full
        if group_row[2] is not None:
            cursor.execute("""
                SELECT COUNT(*) FROM group_users WHERE group_id = ?
            """, (group_id,))
            current_count = cursor.fetchone()[0]
            if current_count >= group_row[2]:
                conn.close()
                return Response.error(f"Group is full (max {group_row[2]} members)")
        
        # Create join request
        cursor.execute("""
            INSERT INTO join_requests (user_id, group_id, message)
            VALUES (?, ?, ?)
        """, (user_id, group_id, message))
        
        request_id = cursor.lastrowid
        conn.commit()

        # Send email notification to group organiser
        cursor.execute("""
            SELECT u.email FROM users u
            JOIN groups g ON u.id = g.organiser_id
            WHERE g.id = ?
        """, (group_id,))
        
        organiser_email = cursor.fetchone()
        if organiser_email:
            email_sender.send_email(
                to=organiser_email[0],
                template_name="notification",
                data={
                    "notification_title": "Neue Beitrittsanfrage",
                    "notification_message": f"Ein Benutzer hat eine Beitrittsanfrage für deine Lerngruppe gestellt.",
                    "action_label": "Anfrage ansehen",
                    "action_url": f"http://localhost:3000/group/{group_id}/requests"
                }
            )
        
        # Fetch created request
        cursor.execute("""
            SELECT id, user_id, group_id, message, status, created_at, responded_at
            FROM join_requests WHERE id = ?
        """, (request_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        request_data = {
            'id': row[0],
            'user_id': row[1],
            'group_id': row[2],
            'message': row[3],
            'status': row[4],
            'created_at': row[5],
            'responded_at': row[6]
        }
        
        return Response.ok(request_data, "Join request created successfully")
        
    except Exception as e:
        log(f"create_beitrittsanfrage failed: {str(e)}", "error")
        return Response.error(f"Failed to create join request: {str(e)}")