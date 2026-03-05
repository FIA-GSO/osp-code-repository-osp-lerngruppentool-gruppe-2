from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.bad_word_filter import contains_bad_word
from tools.logger import log


def update_group(db_connector: DBConnector, group_id: int, data: dict):
    """
    Update group information.
    
    Args:
        db_connector (DBConnector): Database connector instance
        group_id (int): ID of the group to update
        data (dict): Updated group data (title, subject, topic, description, 
                     class, type, location, max_users, status)
    
    Returns:
        dict: JSON response with updated group details
    """
    try:
        if not group_id:
            return Response.error("group_id is required")
        if not data:
            return Response.error("No update data provided")
        
        # Check for bad words in text fields
        text_fields = ['title', 'subject', 'topic', 'description', 'location']
        for field in text_fields:
            if field in data and data[field] and contains_bad_word(str(data[field])):
                return Response.error(f"{field} contains inappropriate language")
        
        conn = db_connector.connect()
        cursor = conn.cursor()
        
        # Check if group exists
        cursor.execute("SELECT id FROM groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("Group not found")
        
        # Build update query dynamically based on provided fields
        allowed_fields = ['title', 'subject', 'topic', 'description', 'class', 
                         'type', 'location', 'max_users', 'status']
        update_fields = []
        params = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not update_fields:
            conn.close()
            return Response.error("No valid fields to update")
        
        # Validate max_users if provided
        if 'max_users' in data and data['max_users'] is not None:
            try:
                max_users = int(data['max_users'])
                if max_users < 0:
                    conn.close()
                    return Response.error("max_users must be >= 0")
                
                # Check if new max_users is not less than current member count
                cursor.execute("""
                    SELECT COUNT(*) FROM group_users WHERE group_id = ?
                """, (group_id,))
                current_count = cursor.fetchone()[0]
                
                if max_users < current_count:
                    conn.close()
                    return Response.error(f"max_users ({max_users}) cannot be less than current member count ({current_count})")
            except (ValueError, TypeError):
                conn.close()
                return Response.error("max_users must be a valid integer")
        
        # Update group
        params.append(group_id)
        query = f"UPDATE groups SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        # Fetch updated group
        cursor.execute("""
            SELECT id, organiser_id, title, subject, topic, description, class, type, location, 
                   max_users, status, created_at, last_active_at, reports
            FROM groups WHERE id = ?
        """, (group_id,))
        
        row = cursor.fetchone()
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
        
        return Response.ok(group_data, "Group updated successfully")
        
    except Exception as e:
        log(f"update_group failed for group_id={group_id}: {str(e)}", "error")
        return Response.error(f"Failed to update group: {str(e)}")