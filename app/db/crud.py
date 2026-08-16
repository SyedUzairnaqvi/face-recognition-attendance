from app.db.database import get_connection


# ============================================================
# FIND PERSON
# ============================================================

def get_person_by_name(name: str):
    """
    Find a registered person by name.

    Returns:
        dict | None
    """

    with get_connection() as conn:

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                person_id,
                name,
                created_at,
                is_active
            FROM persons
            WHERE name = %s
            LIMIT 1
            """,
            (name,),
        )

        row = cursor.fetchone()

        cursor.close()

        return row


# ============================================================
# CREATE PERSON
# ============================================================

def create_person(name: str):
    """
    Register a person in the persons table.

    Returns:
        person_id
    """

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO persons (name)
            VALUES (%s)
            """,
            (name,),
        )

        person_id = cursor.lastrowid

        cursor.close()

        return person_id


# ============================================================
# GET OR CREATE PERSON
# ============================================================

def get_or_create_person(name: str):
    """
    Find a person by name.

    If the person doesn't exist, create them.

    Returns:
        person_id
    """

    person = get_person_by_name(name)

    if person:
        return person["person_id"]

    return create_person(name)


# ============================================================
# ATTENDANCE EXISTS
# ============================================================

def attendance_exists(
    name: str,
    date: str,
) -> bool:
    """
    Check whether this person already has attendance
    recorded for the specified date.
    """

    with get_connection() as conn:

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 1
            FROM attendance a
            INNER JOIN persons p
                ON p.person_id = a.person_id
            WHERE p.name = %s
              AND a.attendance_date = %s
            LIMIT 1
            """,
            (
                name,
                date,
            ),
        )

        row = cursor.fetchone()

        cursor.close()

        return row is not None


# ============================================================
# CREATE ATTENDANCE
# ============================================================

def create_attendance(
    name,
    date,
    time,
    distance=None,
    threshold=None,
    blur=None,
    brightness=None,
    method="Face Recognition",
):
    """
    Create one attendance record.

    The person is automatically created if they don't
    already exist.

    Returns:
        True  -> attendance inserted
        False -> already marked for that day
    """

    with get_connection() as conn:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # Find existing person
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT person_id
            FROM persons
            WHERE name = %s
            LIMIT 1
            """,
            (name,),
        )

        person = cursor.fetchone()

        # ----------------------------------------------------
        # Create person if necessary
        # ----------------------------------------------------

        if person:

            person_id = person[0]

        else:

            cursor.execute(
                """
                INSERT INTO persons (name)
                VALUES (%s)
                """,
                (name,),
            )

            person_id = cursor.lastrowid

        # ----------------------------------------------------
        # Insert attendance
        # ----------------------------------------------------
        # The UNIQUE KEY:
        #
        # (person_id, attendance_date)
        #
        # prevents duplicate attendance for the same
        # person on the same day.

        cursor.execute(
            """
            INSERT IGNORE INTO attendance
            (
                person_id,
                attendance_date,
                attendance_time,
                status,
                method
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                person_id,
                date,
                time,
                "Present",
                method,
            ),
        )

        inserted = cursor.rowcount == 1

        cursor.close()

        return inserted


# ============================================================
# LIST ATTENDANCE
# ============================================================

def list_attendance(
    date=None,
    limit=100,
):
    """
    Return attendance records.

    If date is provided, return records for that date.
    Otherwise return the latest records.
    """

    with get_connection() as conn:

        cursor = conn.cursor(dictionary=True)

        if date:

            cursor.execute(
                """
                SELECT
                    a.attendance_id,
                    p.name,
                    a.attendance_date AS date,
                    a.attendance_time AS time,
                    a.status,
                    a.method,
                    a.created_at
                FROM attendance a
                INNER JOIN persons p
                    ON p.person_id = a.person_id
                WHERE a.attendance_date = %s
                ORDER BY a.attendance_time DESC
                LIMIT %s
                """,
                (
                    date,
                    limit,
                ),
            )

        else:

            cursor.execute(
                """
                SELECT
                    a.attendance_id,
                    p.name,
                    a.attendance_date AS date,
                    a.attendance_time AS time,
                    a.status,
                    a.method,
                    a.created_at
                FROM attendance a
                INNER JOIN persons p
                    ON p.person_id = a.person_id
                ORDER BY
                    a.attendance_date DESC,
                    a.attendance_time DESC
                LIMIT %s
                """,
                (limit,),
            )

        rows = cursor.fetchall()

        cursor.close()

        return list(rows)