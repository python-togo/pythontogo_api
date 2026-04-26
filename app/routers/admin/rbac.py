"""Admin RBAC management — roles, permissions, user-role assignments.

All operations are performed via UUIDs.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.rows import dict_row

from app.core.security import require_permission
from app.database.connection import get_db_connection
from app.schemas.models import AssignPermissionsRequest, AssignRoleRequest, PermissionSummary, RoleCreate, RoleDetail, RoleSummary, RoleUpdate, UserRoleAssignment
from app.utils.responses import success

api_router = APIRouter(tags=["admin-rbac"])


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

@api_router.get("/permissions")
async def list_permissions(db=Depends(get_db_connection), _=Depends(require_permission("roles:read"))):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM permissions ORDER BY resource, action")
        rows = await cur.fetchall()
    return success([PermissionSummary(**r) for r in rows])


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

@api_router.get("/roles")
async def list_roles(db=Depends(get_db_connection), _=Depends(require_permission("roles:read"))):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM roles ORDER BY name")
        rows = await cur.fetchall()
    return success([RoleSummary(**r) for r in rows])


@api_router.get("/roles/{role_id}")
async def get_role(role_id: UUID, db=Depends(get_db_connection), _=Depends(require_permission("roles:read"))):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM roles WHERE id = %s", (str(role_id),))
        role = await cur.fetchone()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        await cur.execute(
            """
            SELECT p.*
            FROM permissions p
            JOIN role_permissions rp ON rp.permission_id = p.id
            WHERE rp.role_id = %s
            ORDER BY p.resource, p.action
            """,
            (str(role_id),),
        )
        perms = await cur.fetchall()

    return success(RoleDetail(**role, permissions=[PermissionSummary(**p) for p in perms]))


@api_router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(body: RoleCreate, db=Depends(get_db_connection), _=Depends(require_permission("roles:create"))):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO roles (name, description, is_system)
            VALUES (%s, %s, FALSE)
            ON CONFLICT (name) DO NOTHING
            RETURNING *
            """,
            (body.name, body.description),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Role '{body.name}' already exists")
    await db.commit()
    return success(RoleSummary(**row), code=201)


@api_router.put("/roles/{role_id}")
async def update_role(role_id: UUID, body: RoleUpdate, db=Depends(get_db_connection), _=Depends(require_permission("roles:update"))):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM roles WHERE id = %s", (str(role_id),))
        role = await cur.fetchone()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if not updates:
            return success(RoleSummary(**role))

        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [str(role_id)]
        await cur.execute(
            f"UPDATE roles SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
            values,
        )
        updated = await cur.fetchone()
    await db.commit()
    return success(RoleSummary(**updated))


@api_router.delete("/roles/{role_id}")
async def delete_role(role_id: UUID, db=Depends(get_db_connection), _=Depends(require_permission("roles:delete"))):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT is_system FROM roles WHERE id = %s", (str(role_id),))
        role = await cur.fetchone()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if role["is_system"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System roles cannot be deleted")
        await cur.execute("DELETE FROM roles WHERE id = %s", (str(role_id),))
    await db.commit()
    return success({"message": "Role deleted"})


# ---------------------------------------------------------------------------
# Role ↔ Permission
# ---------------------------------------------------------------------------

@api_router.post("/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: UUID,
    body: AssignPermissionsRequest,
    db=Depends(get_db_connection),
    _=Depends(require_permission("roles:update")),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT id FROM roles WHERE id = %s", (str(role_id),))
        if not await cur.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        for perm_id in body.permission_ids:
            await cur.execute("SELECT id FROM permissions WHERE id = %s", (str(perm_id),))
            if not await cur.fetchone():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Permission {perm_id} not found")
            await cur.execute(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (str(role_id), str(perm_id)),
            )
    await db.commit()

    # return updated role detail
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM roles WHERE id = %s", (str(role_id),))
        role = await cur.fetchone()
        await cur.execute(
            "SELECT p.* FROM permissions p JOIN role_permissions rp ON rp.permission_id = p.id WHERE rp.role_id = %s ORDER BY p.resource, p.action",
            (str(role_id),),
        )
        perms = await cur.fetchall()
    return success(RoleDetail(**role, permissions=[PermissionSummary(**p) for p in perms]))


@api_router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_permission("roles:update")),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "DELETE FROM role_permissions WHERE role_id = %s AND permission_id = %s",
            (str(role_id), str(permission_id)),
        )
    await db.commit()
    return success({"message": "Permission removed from role"})


# ---------------------------------------------------------------------------
# User ↔ Role
# ---------------------------------------------------------------------------

@api_router.get("/users/{user_id}/roles")
async def get_user_roles(user_id: UUID, db=Depends(get_db_connection), _=Depends(require_permission("users:read"))):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT ur.user_id, ur.role_id, r.name AS role_name, ur.assigned_at
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = %s
            ORDER BY ur.assigned_at
            """,
            (str(user_id),),
        )
        rows = await cur.fetchall()
    return success([UserRoleAssignment(**r) for r in rows])


@api_router.post("/users/{user_id}/roles", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: UUID,
    body: AssignRoleRequest,
    db=Depends(get_db_connection),
    current_user=Depends(require_permission("users:update")),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT id FROM users WHERE id = %s", (str(user_id),))
        if not await cur.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await cur.execute("SELECT id, name FROM roles WHERE id = %s", (str(body.role_id),))
        role = await cur.fetchone()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

        await cur.execute(
            "INSERT INTO user_roles (user_id, role_id, assigned_by) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING assigned_at",
            (str(user_id), str(body.role_id), str(current_user.id)),
        )
        row = await cur.fetchone()

        if not row:
            await cur.execute(
                "SELECT assigned_at FROM user_roles WHERE user_id = %s AND role_id = %s",
                (str(user_id), str(body.role_id)),
            )
            row = await cur.fetchone()

    await db.commit()
    return success(UserRoleAssignment(
        user_id=user_id,
        role_id=body.role_id,
        role_name=role["name"],
        assigned_at=row["assigned_at"],
    ), code=201)


@api_router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    db=Depends(get_db_connection),
    _=Depends(require_permission("users:update")),
):
    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "DELETE FROM user_roles WHERE user_id = %s AND role_id = %s",
            (str(user_id), str(role_id)),
        )
    await db.commit()
    return success({"message": "Role removed from user"})
