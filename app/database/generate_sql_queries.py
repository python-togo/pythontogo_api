from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb


def normalize_value(value):
    """Normalize a value for SQL queries, handling different data types appropriately.

    Parameters:
    ----------
        value: The value to normalize, which can be of various data types (e.g., str, int, dict).

    Returns:
    -------
        The normalized value, ready for use in SQL queries. For dictionaries, it returns a Jsonb object.
    """
    if isinstance(value, dict):
        return Jsonb(value)
    return value


def build_column(column):
    """Build a SQL identifier for a column, handling potential table prefixes.

    Parameters:
    ----------
        column (str): The column name, which may include a table prefix (e.g., "table.column").

    Returns:
    --------
        SQL: A SQL identifier for the column, properly formatted for use in queries.
    """
    if "." in column:
        table, col = column.split(".")
        return SQL("{}.{}").format(Identifier(table), Identifier(col))
    return Identifier(column)


def generate_select_query(table, columns=None, filter=None):
    """Generate a SQL SELECT query.

    Parameters:
    ----------
        table (str): The name of the table to select from.
        columns (list, optional): A list of column names to select. Defaults to None (select all).
        filter (dict, optional): A dictionary of column-value pairs for the WHERE clause. Defaults to None.

    Returns:
    -------
        tuple: A tuple containing the SQL query and a tuple of values for parameterized queries.
    """
    query = "SELECT {} FROM {}"
    columns_sql = SQL('*')
    if columns:
        columns_sql = SQL(', ').join(build_column(col) for col in columns)
    query = SQL(query).format(
        columns_sql,
        Identifier(table)
    )
    values = []
    if filter:
        where_clauses = []
        for key, value in filter.items():
            where_clauses.append(SQL("{} = {}").format(
                Identifier(key), SQL("%s")))
            values.append(normalize_value(value))
        where_sql = SQL(" AND ").join(where_clauses)
        query += SQL(" WHERE ") + where_sql
    return query, tuple(values)


def generate_select_query_with_join(table, join_table, join_condition, columns=None, filter=None):
    """Generate a SQL SELECT query with a JOIN clause.

    Parameters:
    ----------
        table (str): The name of the main table to select from.
        join_table (str): The name of the table to join with.
        join_condition (str): The condition for the JOIN clause (e.g., "table.id = join_table.table_id").   
        columns (list, optional): A list of column names to select. Defaults to None (select all).
        filter (dict, optional): A dictionary of column-value pairs for the WHERE clause. Defaults to None.

    Returns:
    -------
        tuple: A tuple containing the SQL query and a tuple of values for parameterized queries.
    """
    query = "SELECT {} FROM {} JOIN {} ON {}"
    columns_sql = SQL('*')
    if columns:
        columns_sql = SQL(', ').join(build_column(col) for col in columns)
    query = SQL(query).format(
        columns_sql,
        Identifier(table),
        Identifier(join_table),
        SQL(join_condition)
    )
    values = []
    if filter:
        where_clauses = []
        for key, value in filter.items():
            column_sql = build_column(key)
            where_clauses.append(SQL("{} = {}").format(
                column_sql, SQL("%s")))
            values.append(normalize_value(value))
        where_sql = SQL(" AND ").join(where_clauses)
        query += SQL(" WHERE ") + where_sql
    return query, tuple(values)


def generate_multiple_joins_query(table, joins, columns=None, filter=None):
    """Generate a SQL SELECT query with multiple JOIN clauses.

    Parameters:
    ----------
        table (str): The name of the main table to select from.
        joins (list): A list of dictionaries, each containing 'join_table' and 'join_condition' keys for the JOIN clauses.
        columns (list, optional): A list of column names to select. Defaults to None (select all).
        filter (dict, optional): A dictionary of column-value pairs for the WHERE clause. Defaults to None.

    Returns:
    -------
        tuple: A tuple containing the SQL query and a tuple of values for parameterized queries.
    """
    query = SQL("SELECT {} FROM {}")

    columns_sql = SQL('*')
    if columns:
        columns_sql = SQL(', ').join(build_column(col) for col in columns)

    query = query.format(
        columns_sql,
        Identifier(table)
    )

    for join in joins:
        query += SQL(" JOIN {} ON {}").format(
            Identifier(join['join_table']),
            SQL(join['join_condition'])
        )

    values = []
    if filter:
        where_clauses = []
        for key, value in filter.items():
            column_sql = build_column(key)
            where_clauses.append(SQL("{} = {}").format(
                column_sql, SQL("%s")))
            values.append(normalize_value(value))

        where_sql = SQL(" AND ").join(where_clauses)
        query += SQL(" WHERE ") + where_sql

    return query, tuple(values)


def generate_insert_query(table, data):
    """Generate a SQL INSERT query.

    Parameters:
    ----------
        table (str): The name of the table to insert into.
        data (dict): A dictionary of column-value pairs for the INSERT clause.

    Returns:
    -------
        tuple: A tuple containing the SQL query and a tuple of values for parameterized queries.
    """

    columns = data.keys()
    values = [normalize_value(value) for value in data.values()]
    query = SQL("INSERT INTO {} ({}) VALUES ({})").format(
        Identifier(table),
        SQL(', ').join(build_column(col) for col in columns),
        SQL(', ').join(SQL("%s") for _ in values)
    )
    return query, tuple(values)


def generate_update_query(table, data, filter):
    """Generate a SQL UPDATE query.

    Parameters:
    ----------
        table (str): The name of the table to update.
        data (dict): A dictionary of column-value pairs for the SET clause.
        filter (dict, optional): A dictionary of column-value pairs for the WHERE clause. Defaults to None.

    Returns:
    -------
        tuple: A tuple containing the SQL query and a tuple of values for parameterized queries.
    """
    set_clauses = []
    values = []
    for key, value in data.items():
        set_clauses.append(SQL("{} = {}").format(
            Identifier(key), SQL("%s")))
        values.append(normalize_value(value))
    set_sql = SQL(", ").join(set_clauses)
    query = SQL("UPDATE {} SET {}").format(
        Identifier(table),
        set_sql
    )
    if filter:
        where_clauses = []
        for key, value in filter.items():
            column_sql = build_column(key)
            where_clauses.append(SQL("{} = {}").format(
                column_sql, SQL("%s")))
            values.append(normalize_value(value))
        where_sql = SQL(" AND ").join(where_clauses)
        query += SQL(" WHERE ") + where_sql
    query += SQL(" RETURNING *")
    return query, tuple(values)


def generate_delete_query(table, filter):
    """Generate a SQL DELETE query.

    Parameters:
    ----------
        table (str): The name of the table to delete from.
        filter (dict, optional): A dictionary of column-value pairs for the WHERE clause. Defaults to None.

    Returns:
    -------
        tuple: A tuple containing the SQL query and a tuple of values for parameterized queries.
    """

    query = SQL("DELETE FROM {}").format(Identifier(table))
    values = []
    if filter:
        where_clauses = []
        for key, value in filter.items():
            column_sql = build_column(key)
            where_clauses.append(SQL("{} = {}").format(
                column_sql, SQL("%s")))
            values.append(normalize_value(value))
        where_sql = SQL(" AND ").join(where_clauses)
        query += SQL(" WHERE ") + where_sql
    query += SQL(" RETURNING id")
    return query, tuple(values)
