from fastapi import HTTPException, Request

from typing import cast


async def get_db_connection(request: Request):

    db_pool = request.app.state.db_pool
    async with db_pool.connection() as connection:
        yield connection


async def get_redis_client(request: Request):
    try:
        redis_client = request.app.state.redis_client
        yield redis_client
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
