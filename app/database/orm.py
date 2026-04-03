
from psycopg import Connection
from psycopg.sql import SQL, Identifier
from psycopg.rows import dict_row
from app.database.generate_sql_queries import (
    generate_select_query,
    generate_select_query_with_join,
    generate_multiple_joins_query,
    generate_insert_query,
    generate_update_query,
    generate_delete_query)


def select(db: Connection, table, columns=None, filter=None):
    try:
        query, values = generate_select_query(table, columns, filter)
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            result = cur.fetchall()
        return result
    except Exception as e:
        raise e


def select_with_join(db: Connection, table, join_table, join_condition, columns=None, filter=None):
    try:
        query, values = generate_select_query_with_join(
            table, join_table, join_condition, columns, filter)
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            result = cur.fetchall()
        return result
    except Exception as e:
        raise e


def select_with_multiple_joins(db: Connection, table, joins, columns=None, filter=None):
    try:
        query, values = generate_multiple_joins_query(
            table, joins, columns, filter)
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(query, values)
            result = cur.fetchall()
        return result
    except Exception as e:
        raise e


def insert(db: Connection, table, data):
    try:
        exit = select(db, table, filter=data)
        if exit:
            raise ValueError("Record already exists")

        query, values = generate_insert_query(table, data)
        with db.cursor() as cur:
            cur.execute(query, values)
            db.commit()
    except Exception as e:
        raise e


def update(db: Connection, table, data, filter):
    try:
        query, values = generate_update_query(table, data, filter)
        with db.cursor() as cur:
            cur.execute(query, values)
            db.commit()
    except Exception as e:
        print(f"Error executing update query: {e}")
        raise e


def delete(db: Connection, table, filter):
    try:
        query, values = generate_delete_query(table, filter)
        with db.cursor() as cur:
            cur.execute(query, values)
            db.commit()
    except Exception as e:
        print(f"Error executing delete query: {e}")
        raise e
