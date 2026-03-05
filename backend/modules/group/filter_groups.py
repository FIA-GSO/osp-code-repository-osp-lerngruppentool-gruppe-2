from tools.dbConnector import DBConnector
from tools.respone import Response
from tools.logger import log


def filter_groups(
    db_connector: DBConnector,
    subject: str = None,
    type: str = None,
    class_: str = None,
    status: str = None,
    location: str = None,
    has_space: bool = None,
    organiser_id: int = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    Filter groups by one or more exact-match criteria with pagination.

    Args:
        db_connector (DBConnector): Database connector instance
        subject (str):       Filter by exact subject name
        type (str):          Filter by group type (e.g. 'online', 'in-person')
        class_ (str):        Filter by class identifier
        status (str):        Filter by status ('active', 'closed', ...)
        location (str):      Filter by location
        has_space (bool):    True = only groups with free spots; False = only full groups
        organiser_id (int):  Filter by the group creator's user ID
        limit (int):         Maximum number of results (default 20)
        offset (int):        Number of results to skip (default 0)

    Returns:
        dict: JSON response with filtered groups list and pagination info
    """
    try:
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0

        if limit < 1:
            return Response.error("limit must be at least 1")
        if offset < 0:
            return Response.error("offset must be >= 0")

        conditions = []
        params = []

        if subject is not None:
            conditions.append("g.subject = ?")
            params.append(subject)

        if type is not None:
            conditions.append("g.type = ?")
            params.append(type)

        if class_ is not None:
            conditions.append("g.class = ?")
            params.append(class_)

        if status is not None:
            conditions.append("g.status = ?")
            params.append(status)

        if location is not None:
            conditions.append("g.location = ?")
            params.append(location)

        if organiser_id is not None:
            conditions.append("g.organiser_id = ?")
            params.append(organiser_id)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        having_clause = ""
        if has_space is True:
            having_clause = "HAVING (g.max_users IS NULL OR COUNT(gu.user_id) < g.max_users)"
        elif has_space is False:
            having_clause = "HAVING g.max_users IS NOT NULL AND COUNT(gu.user_id) >= g.max_users"

        conn = db_connector.connect()
        cursor = conn.cursor()

        count_query = f"SELECT COUNT(*) FROM groups g {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        main_query = f"""
            SELECT g.id, g.organiser_id, g.title, g.subject, g.topic, g.description,
                   g.class, g.type, g.location, g.max_users, g.status, g.created_at,
                   g.last_active_at, g.reports,
                   COUNT(gu.user_id) as member_count
            FROM groups g
            LEFT JOIN group_users gu ON g.id = gu.group_id
            {where_clause}
            GROUP BY g.id
            {having_clause}
            ORDER BY g.created_at DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(main_query, params + [limit, offset])
        rows = cursor.fetchall()
        conn.close()

        groups = []
        for row in rows:
            groups.append({
                "id": row[0],
                "organiser_id": row[1],
                "title": row[2],
                "subject": row[3],
                "topic": row[4],
                "description": row[5],
                "class": row[6],
                "type": row[7],
                "location": row[8],
                "max_users": row[9],
                "status": row[10],
                "created_at": row[11],
                "last_active_at": row[12],
                "reports": row[13],
                "member_count": row[14],
            })

        return Response.ok(
            {
                "groups": groups,
                "total": total,
                "limit": limit,
                "offset": offset,
            },
            "Groups filtered successfully",
        )

    except Exception as e:
        log(f"filter_groups failed: {str(e)}", "error")
        return Response.error(f"Failed to filter groups: {str(e)}")
