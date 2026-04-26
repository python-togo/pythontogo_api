"""Idempotent seed: permissions, system roles, and super admin user.

Run automatically on server startup via the lifespan hook in main.py.
Every INSERT uses ON CONFLICT DO NOTHING — safe to call multiple times.

Super admin credentials are read from env vars:
  SUPERADMIN_EMAIL, SUPERADMIN_USERNAME, SUPERADMIN_PASSWORD, SUPERADMIN_FULL_NAME
"""

from app.core.settings import logger, settings
from app.core.security import hash_password

# ---------------------------------------------------------------------------
# Permissions catalogue  (resource, action, description)
# ---------------------------------------------------------------------------

PERMISSIONS = [
    # dashboard
    ("dashboard", "read", "View global admin overview"),

    # users
    ("users", "read",   "List and view users"),
    ("users", "update", "Edit user role or status"),
    ("users", "delete", "Delete a user account"),

    # events
    ("events", "read",   "View events and their overview"),
    ("events", "create", "Create a new event"),
    ("events", "update", "Edit an existing event"),
    ("events", "delete", "Delete an event"),

    # proposals
    ("proposals", "read",   "View CFP proposals"),
    ("proposals", "review", "Submit a review score for a CFP proposal"),
    ("proposals", "update", "Change proposal status"),

    # registrations
    ("registrations", "read",   "View registrations"),
    ("registrations", "create", "Register an attendee manually"),
    ("registrations", "update", "Edit or check-in a registration"),
    ("registrations", "delete", "Delete a registration"),

    # speakers
    ("speakers", "read",   "View speakers"),
    ("speakers", "create", "Add a new speaker"),
    ("speakers", "update", "Edit speaker info or photo"),
    ("speakers", "delete", "Remove a speaker"),

    # sessions (conference schedule)
    ("sessions", "read",   "View scheduled sessions"),
    ("sessions", "create", "Create a session"),
    ("sessions", "update", "Edit a session"),
    ("sessions", "delete", "Delete a session"),

    # outreach (contacts + partners)
    ("outreach", "read",   "View contact messages and partners"),
    ("outreach", "update", "Mark messages resolved / confirm partners"),

    # sponsor packages
    ("sponsor_packages", "read",   "View sponsorship packages"),
    ("sponsor_packages", "create", "Create a sponsorship package"),
    ("sponsor_packages", "update", "Edit a sponsorship package"),
    ("sponsor_packages", "delete", "Delete a sponsorship package"),

    # security (API keys + sessions)
    ("security", "read",   "View API keys and active sessions"),
    ("security", "create", "Generate a new API key"),
    ("security", "delete", "Revoke an API key or session"),

    # shop — products & variants
    ("shop_products", "read",   "View shop products and variants"),
    ("shop_products", "create", "Add a product or variant"),
    ("shop_products", "update", "Edit a product or variant"),
    ("shop_products", "delete", "Delete a product or variant"),

    # shop — orders
    ("shop_orders", "read",   "View shop orders"),
    ("shop_orders", "update", "Update an order status"),

    # shop — categories
    ("shop_categories", "read",   "View product categories"),
    ("shop_categories", "create", "Create a category"),
    ("shop_categories", "update", "Edit a category"),
    ("shop_categories", "delete", "Delete a category"),

    # shop — coupons
    ("shop_coupons", "read",   "View discount coupons"),
    ("shop_coupons", "create", "Create a coupon"),
    ("shop_coupons", "update", "Edit a coupon"),
    ("shop_coupons", "delete", "Delete a coupon"),

    # shop — customers
    ("shop_customers", "read",   "View shop customers"),
    ("shop_customers", "update", "Toggle customer active status"),

    # shop — dashboard / analytics
    ("shop_dashboard", "read", "View shop dashboard and analytics"),

    # roles (RBAC self-management)
    ("roles", "read",   "View roles and their permissions"),
    ("roles", "create", "Create a new role"),
    ("roles", "update", "Edit a role or its permission set"),
    ("roles", "delete", "Delete a non-system role"),
]

ALL_PERMISSIONS = {f"{r}:{a}" for r, a, _ in PERMISSIONS}

# ---------------------------------------------------------------------------
# System roles
# ---------------------------------------------------------------------------

SYSTEM_ROLES = {
    "super_admin": {
        "description": "Unrestricted access to everything",
        "permissions": ALL_PERMISSIONS,
    },
    "admin": {
        "description": "Full access except deleting system roles",
        "permissions": ALL_PERMISSIONS - {"roles:delete"},
    },
    "staff": {
        "description": "Read-only access plus event operations",
        "permissions": {
            "dashboard:read",
            "users:read",
            "events:read",
            "proposals:read", "proposals:update",
            "registrations:read", "registrations:create", "registrations:update",
            "speakers:read", "speakers:create", "speakers:update",
            "sessions:read",
            "outreach:read",
            "sponsor_packages:read",
            "security:read",
            "shop_products:read",
            "shop_orders:read", "shop_orders:update",
            "shop_categories:read",
            "shop_coupons:read",
            "shop_customers:read",
            "shop_dashboard:read",
            "roles:read",
        },
    },
    "reviewer": {
        "description": "CFP reviewer — can score and comment on submitted proposals",
        "permissions": {"proposals:read", "proposals:review"},
    },
    "member": {
        "description": "Regular community member — no admin permissions",
        "permissions": set(),
    },
}


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

async def run_seed(db_pool) -> None:
    """Insert missing permissions, system roles, and super admin. Idempotent."""
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:

            # 1. Upsert permissions
            for resource, action, description in PERMISSIONS:
                await cur.execute(
                    """
                    INSERT INTO permissions (name, description, resource, action)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                    """,
                    (f"{resource}:{action}", description, resource, action),
                )

            # 2. Build permission name → id map
            await cur.execute("SELECT id, name FROM permissions")
            rows = await cur.fetchall()
            perm_id_by_name: dict[str, str] = {row[1]: str(row[0]) for row in rows}

            # 3. Upsert system roles and their permissions
            role_ids: dict[str, str] = {}
            for role_name, role_cfg in SYSTEM_ROLES.items():
                await cur.execute(
                    """
                    INSERT INTO roles (name, description, is_system)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (name) DO UPDATE
                        SET description = EXCLUDED.description,
                            updated_at  = NOW()
                    RETURNING id
                    """,
                    (role_name, role_cfg["description"]),
                )
                role_ids[role_name] = str((await cur.fetchone())[0])

                for perm_name in role_cfg["permissions"]:
                    perm_id = perm_id_by_name.get(perm_name)
                    if not perm_id:
                        continue
                    await cur.execute(
                        """
                        INSERT INTO role_permissions (role_id, permission_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (role_ids[role_name], perm_id),
                    )

            # 4. Create super admin user (unique — skip if already exists)
            await cur.execute(
                "SELECT id FROM users WHERE email = %s OR username = %s",
                (settings.superadmin_email, settings.superadmin_username),
            )
            existing_sa = await cur.fetchone()

            if not existing_sa:
                await cur.execute(
                    """
                    INSERT INTO users
                        (username, email, full_name, password_hash, role, is_active)
                    VALUES (%s, %s, %s, %s, 'admin', TRUE)
                    RETURNING id
                    """,
                    (
                        settings.superadmin_username,
                        settings.superadmin_email,
                        settings.superadmin_full_name,
                        hash_password(settings.superadmin_password),
                    ),
                )
                sa_user_id = str((await cur.fetchone())[0])
                logger.info("Super admin user created: %s", settings.superadmin_email)
            else:
                sa_user_id = str(existing_sa[0])

            # 5. Assign super_admin role to the super admin user
            await cur.execute(
                """
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (sa_user_id, role_ids["super_admin"]),
            )

        await conn.commit()

    logger.info(
        "Seed completed — %d permissions | %d system roles | super admin: %s",
        len(PERMISSIONS),
        len(SYSTEM_ROLES),
        settings.superadmin_email,
    )
