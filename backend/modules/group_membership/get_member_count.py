from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def get_member_count(db_connector: DBConnector, group_id: int):
    """
    Get the number of members in a group.

    Args:
        db_connector (DBConnector): Database connector instance
        group_id (int): ID of the group

    Returns:
        dict: JSON response with the member count
    """
    try:
        conn = db_connector.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return Response.error("Group not found")

        cursor.execute(
            "SELECT COUNT(*) FROM group_users WHERE group_id = ?", (group_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()

        return Response.ok(data={"group_id": group_id, "member_count": count})

    except Exception as e:
        log(f"Error getting member count for group {group_id}: {e}", "error")
        return Response.error("Internal server error")
