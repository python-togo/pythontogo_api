
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
from app.core.settings import logger
from app.utils.helpers import remove_null_values


async def select(db: Connection, table, columns=None, filter=None):
    try:
        query, values = generate_select_query(table, columns, filter)
        async with db.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, values)
            result = await cur.fetchall()
        return result
    except Exception as e:
        await db.rollback()
        logger.error(f"Error executing select query on {table}: {str(e)}")
        # TODO: sent email to admin about error during select query execution


async def select_with_join(db: Connection, table, join_table, join_condition, columns=None, filter=None):
    try:
        query, values = generate_select_query_with_join(
            table, join_table, join_condition, columns, filter)
        async with db.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, values)
            result = await cur.fetchall()
        return result
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Error executing select with join query on {table} and {join_table}: {str(e)}")
        # TODO: sent email to admin about error during select with join query execution


async def select_with_multiple_joins(db: Connection, table, joins, columns=None, filter=None):
    try:

        query, values = generate_multiple_joins_query(
            table, joins, columns, filter)
        async with db.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, values)
            result = await cur.fetchall()
        return result
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Error executing select with multiple joins query on {table}: {str(e)}")
        # TODO: sent email to admin about error during select with multiple joins query execution


async def insert(db: Connection, table, data):
    try:
        exit = await select(db, table, filter=data)
        if exit:
            raise ValueError("Record already exists")

        query, values = generate_insert_query(table, data)
        async with db.cursor() as cur:
            await cur.execute(query, values)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error inserting record into {table}: {str(e)}")
        # TODO: sent email to admin about error during insert query execution


async def update(db: Connection, table, data, filter):
    try:
        data = remove_null_values(data)
        query, values = generate_update_query(table, data, filter)
        async with db.cursor() as cur:
            await cur.execute(query, values)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating record in {table}: {str(e)}")
        # TODO: Log the error can be done here
        # TODO: sent email to admin about error during update query execution


async def delete(db: Connection, table, filter):
    try:
        query, values = generate_delete_query(table, filter)
        async with db.cursor() as cur:
            await cur.execute(query, values)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting record from {table}: {str(e)}")
        # TODO: Log the error can be done here
        # TODO: sent email to admin about error during delete query execution
