from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.bad_word_filter import contains_bad_word
from tools.logger import log
from tools.email_sender import send_template_email


def create_group(db_connector: DBConnector, data: dict):
    """
    Create a new group.
    
    Args:
        db_connector (DBConnector): Database connector instance
        data (dict): Group data containing organiser_id, title, subject, topic, 
                     description, class, type, location, max_users
    
    Returns:
        dict: JSON response with created group details
    """
    try:
        # Validate required fields
        if not data.get('organiser_id'):
            return Response.error("organiser_id is required")
        if not data.get('title'):
            return Response.error("title is required")
        
        # Check for bad words in text fields
        text_fields = ['title', 'subject', 'topic', 'description', 'location']
        for field in text_fields:
            if data.get(field) and contains_bad_word(str(data.get(field))):
                return Response.error(f"{field} contains inappropriate language")
        
        # Extract fields
        organiser_id = data.get('organiser_id')
        title = data.get('title')
        subject = data.get('subject')
        topic = data.get('topic')
        description = data.get('description')
        class_name = data.get('class')
        type_name = data.get('type')
        location = data.get('location')
        max_users = data.get('max_users')
        
        # Validate max_users if provided
        if max_users is not None:
            try:
                max_users = int(max_users)
                if max_users < 0:
                    return Response.error("max_users must be >= 0")
            except (ValueError, TypeError):
                return Response.error("max_users must be a valid integer")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if organiser exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (organiser_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("Organiser user not found")
        
        # Insert group
        cursor.execute("""
            INSERT INTO groups (organiser_id, title, subject, topic, description, class, type, location, max_users)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (organiser_id, title, subject, topic, description, class_name, type_name, location, max_users))
        
        group_id = cursor.lastrowid
        
        # Add organiser as first member
        cursor.execute("""
            INSERT INTO group_users (user_id, group_id)
            VALUES (?, ?)
        """, (organiser_id, group_id))
        
        conn.commit()
        
        # Fetch created group
        cursor.execute("""
            SELECT id, organiser_id, title, subject, topic, description, class, type, location, 
                   max_users, status, created_at, last_active_at, reports
            FROM groups WHERE id = ?
        """, (group_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return Response.error("Failed to load created group")

        conn.close()
        
        group_data = {
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
            'reports': row[13]
        }
        
        return Response.ok(group_data, "Group created successfully")
        
    except Exception as e:
        log(f"create_group failed: {str(e)}", "error")
        return Response.error(f"Failed to create group: {str(e)}")