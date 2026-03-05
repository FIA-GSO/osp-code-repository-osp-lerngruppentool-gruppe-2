from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def delete_user(db_connector: DBConnector, user_id: int, executing_user_email: str = None):
    """
    Delete a user.
    
    Args:
        db_connector (DBConnector): Database connector instance
        user_id (int): ID of the user to delete
        executing_user_email (str, required): Email of the user executing the deletion (for authorization checks for deletion options)
    Returns:
        dict: JSON response with deletion status
    """
    try:
        if not user_id:
            return Response.error("user_id is required")
        
        conn = db_connector.connect()
        cursor = conn.cursor()

        # Authorization check: Only allow deletion if executing user is admin, teacher or the user themselves
        if not executing_user_email:
            conn.close()
            return Response.error("Executing user email is required for authorization")
        
        if executing_user_email:
            cursor.execute("SELECT id, role FROM users WHERE email = ?", (executing_user_email,))
            executing_user = cursor.fetchone()
            if not executing_user:
                conn.close()
                return Response.error("Executing user not found by email: " + executing_user_email)
            executing_user_id, executing_user_role = executing_user
            if executing_user_role not in ('admin', 'teacher'):
                # If not admin or teacher, check if they are trying to delete their own account
                if executing_user_id != user_id:
                    conn.close()
                    return Response.error("Nicht berechtigt. Nur Admins, Lehrkräfte oder der User selbst dürfen einen User löschen.")
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("User not found")
        
        # Check if user is an organiser of any groups
        cursor.execute("SELECT id FROM groups WHERE organiser_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return Response.error("Cannot delete user who is an organiser of groups. Transfer or delete groups first.")
        
        # Delete user (cascade will delete group_users and join_requests entries)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return Response.ok(message="User deleted successfully")
        
    except Exception as e:
        log(f"delete_user failed for user_id={user_id}: {str(e)}", "error")
        return Response.error(f"Failed to delete user: {str(e)}")
    
    finally:
        if 'conn' in locals():
            conn.close()