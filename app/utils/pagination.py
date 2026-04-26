"""Pagination helper for raw SQL queries.

Usage:
    rows, total = await paginate(db, "SELECT * FROM table ORDER BY created_at DESC", (), page, per_page)
    return success(rows, total=total, page=page, per_page=per_page)
"""

from psycopg.rows import dict_row

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


async def paginate(
    db,
    sql: str,
    values: tuple | list,
    page: int,
    per_page: int,
) -> tuple[list[dict], int]:
    """Execute *sql* with LIMIT/OFFSET and return (rows, total_count).

    The total is obtained by wrapping the query in a COUNT subquery so any
    WHERE / JOIN / GROUP BY clauses are automatically respected.
    """
    per_page = min(per_page, MAX_PER_PAGE)
    offset = (page - 1) * per_page
    values = tuple(values)

    async with db.cursor() as cur:
        await cur.execute(f"SELECT COUNT(*) FROM ({sql}) AS _pq", values)
        total: int = (await cur.fetchone())[0]

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(f"{sql} LIMIT %s OFFSET %s", values + (per_page, offset))
        rows: list[dict] = await cur.fetchall()

    return rows, total
