from app.core.settings import logger
from psycopg import connect
from app.core.settings import settings

"""PostgreSQL create-table queries for the PyCon multi-edition API.

This module intentionally exposes SQL strings so you can execute them in your own
migration flow.
"""


CREATE_EXTENSIONS_QUERY = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;
"""


CREATE_TYPES_QUERY = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'partner_type_enum') THEN
        CREATE TYPE partner_type_enum AS ENUM ('partnership', 'sponsorship', 'media_partner', 'python_community_partner', 'community_partner', 'other');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'delivery_method_enum') THEN
        CREATE TYPE delivery_method_enum AS ENUM ('online', 'onsite', 'hybrid');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'package_tier_enum') THEN
        CREATE TYPE package_tier_enum AS ENUM (
            'headline',
            'platinum',
            'gold',
            'silver',
            'bronze',
            'heart',
            'custom'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_type_enum') THEN
        CREATE TYPE event_type_enum AS ENUM ('workshop', 'conference', 'dinner', 'community', 'other');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_type_enum') THEN
        CREATE TYPE session_type_enum AS ENUM (
            'talk',
            'workshop',
            'panel',
            'keynote',
            'lightning'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'submission_status_enum') THEN
        CREATE TYPE submission_status_enum AS ENUM (
            'draft',
            'submitted',
            'accepted',
            'rejected',
            'waitlisted'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'registration_status_enum') THEN
        CREATE TYPE registration_status_enum AS ENUM (
            'pending',
            'confirmed',
            'cancelled',
            'checked_in'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status_enum') THEN
        CREATE TYPE payment_status_enum AS ENUM (
            'pending',
            'succeeded',
            'failed',
            'refunded'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'adjustment_type_enum') THEN
        CREATE TYPE adjustment_type_enum AS ENUM (
            'extra_charge',
            'discount',
            'manual_correction'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
        CREATE TYPE user_role_enum AS ENUM ('admin', 'member', 'staff');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status_enum') THEN
        CREATE TYPE order_status_enum AS ENUM (
            'pending',
            'paid',
            'shipped',
            'delivered',
            'cancelled'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coupon_type_enum') THEN
        CREATE TYPE coupon_type_enum AS ENUM ('percentage', 'fixed_amount');
    END IF;
END
$$;
"""


CREATE_TABLE_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        code VARCHAR(32) NOT NULL UNIQUE,
        title VARCHAR(255) NOT NULL,
        tagline TEXT,
        description TEXT,
        type event_type_enum NOT NULL DEFAULT 'conference',
        format delivery_method_enum NOT NULL DEFAULT 'hybrid',
        location VARCHAR(255) NOT NULL,
        country VARCHAR(120) DEFAULT 'Togo',
        city VARCHAR(120) DEFAULT 'Lome',
        google_maps_url TEXT,
        timezone VARCHAR(64) NOT NULL DEFAULT 'Africa/Lome',
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        website_url TEXT,
        report_url TEXT,
        cfp_open_at TIMESTAMPTZ,
        cfp_close_at TIMESTAMPTZ,
        early_bird_sales_open_at TIMESTAMPTZ,
        early_bird_sales_close_at TIMESTAMPTZ,
        ticket_sales_open_at TIMESTAMPTZ,
        ticket_sales_close_at TIMESTAMPTZ,
        is_active BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CHECK (end_date >= start_date)
    );
    """,

    """CREATE TABLE IF NOT EXISTS venues (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        address TEXT NOT NULL,
        google_maps_url TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_venues_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",

    """
    CREATE TABLE IF NOT EXISTS sponsors_partners (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        website_url TEXT,
        contact_name VARCHAR(255),
        contact_email VARCHAR(255) NOT NULL,
        contact_phone VARCHAR(40),
        description TEXT,
        logo_url TEXT,
        partner_type partner_type_enum NOT NULL,
        package_tier package_tier_enum,
        is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_sponsors_partners_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_sponsors_partners_event_name UNIQUE (event_id, name)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS contact_messages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_code VARCHAR(32),
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        subject VARCHAR(255),
        message TEXT NOT NULL,
        organization VARCHAR(255),
        is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID,
        name VARCHAR(255) NOT NULL,
        key_value TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_api_keys_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE SET NULL
    );""",
    """
    CREATE TABLE IF NOT EXISTS tracks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        color VARCHAR(7),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_track_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",
    """
    CREATE TABLE IF NOT EXISTS proposals (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        abstract TEXT,
        track_id UUID,
        speaker_full_name VARCHAR(255) NOT NULL,
        speaker_email VARCHAR(255) NOT NULL,
        speaker_phone VARCHAR(40),
        speaker_organization VARCHAR(255),
        speaker_bio TEXT,
        speaker_photo_url TEXT,
        speaker_social_links JSONB,
        session_type session_type_enum NOT NULL,
        language VARCHAR(64) NOT NULL DEFAULT 'French',
        level VARCHAR(64),
        needs_equipment BOOLEAN NOT NULL DEFAULT FALSE,
        equipment_details TEXT,
        format delivery_method_enum NOT NULL DEFAULT 'onsite',
        status submission_status_enum NOT NULL DEFAULT 'draft',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_proposals_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",
    """
    CREATE TABLE IF NOT EXISTS speakers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        proposal_id UUID,
        first_name VARCHAR(255) NOT NULL,
        last_name VARCHAR(255) NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        headline VARCHAR(255),
        organization VARCHAR(255),
        country VARCHAR(120),
        bio TEXT,
        photo_url TEXT,
        social_links JSONB,
        website_url TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_speakers_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_speakers_proposal
            FOREIGN KEY (proposal_id)
            REFERENCES proposals(id)
            ON DELETE SET NULL
    );""",

    """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(100) NOT NULL UNIQUE,
        email VARCHAR(255) NOT NULL UNIQUE,
        full_name VARCHAR(255),
        password_hash TEXT NOT NULL,
        role user_role_enum NOT NULL DEFAULT 'member',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        venue_id UUID NOT NULL,
        track_id UUID,
        speaker_id UUID,
        title VARCHAR(255) NOT NULL,
        slug VARCHAR(255) NOT NULL UNIQUE,
        session_type session_type_enum NOT NULL,
        starts_at TIMESTAMPTZ NOT NULL,
        ends_at TIMESTAMPTZ NOT NULL,
        description TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_sessions_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_sessions_venue
            FOREIGN KEY (venue_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_sessions_track
            FOREIGN KEY (track_id)
            REFERENCES tracks(id)
            ON DELETE SET NULL,
        CONSTRAINT fk_sessions_speaker
            FOREIGN KEY (speaker_id)
            REFERENCES speakers(id)
            ON DELETE SET NULL,
        CHECK (ends_at > starts_at)
    );""",

    """
    CREATE TABLE IF NOT EXISTS registrations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        user_id UUID,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(40),
        organization VARCHAR(255),
        ticket_type VARCHAR(100) NOT NULL DEFAULT 'general',
        status registration_status_enum NOT NULL DEFAULT 'pending',
        checked_in_at TIMESTAMPTZ,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_registrations_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_registrations_user
            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE SET NULL,
        CONSTRAINT uq_registrations_event_email UNIQUE (event_id, email)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS sponsor_packages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        tier package_tier_enum NOT NULL,
        description TEXT,
        price NUMERIC(10, 2) NOT NULL DEFAULT 0,
        benefits JSONB DEFAULT '[]',
        max_slots INT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_sponsor_packages_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_sponsor_packages_event_tier UNIQUE (event_id, tier)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS permissions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        resource VARCHAR(50) NOT NULL,
        action VARCHAR(50) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_permissions_resource_action UNIQUE (resource, action)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS roles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        is_system BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id UUID NOT NULL,
        permission_id UUID NOT NULL,
        PRIMARY KEY (role_id, permission_id),
        CONSTRAINT fk_rp_role
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
        CONSTRAINT fk_rp_permission
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id UUID NOT NULL,
        role_id UUID NOT NULL,
        assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        assigned_by UUID,
        PRIMARY KEY (user_id, role_id),
        CONSTRAINT fk_ur_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_ur_role
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
        CONSTRAINT fk_ur_assigned_by
            FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS talk_reviews (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        proposal_id UUID NOT NULL,
        reviewer_id UUID NOT NULL,
        score SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_tr_proposal
            FOREIGN KEY (proposal_id) REFERENCES proposals(id) ON DELETE CASCADE,
        CONSTRAINT fk_tr_reviewer
            FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT uq_tr_proposal_reviewer UNIQUE (proposal_id, reviewer_id)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS categories (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        parent_id UUID,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_categories_parent
            FOREIGN KEY (parent_id)
            REFERENCES categories(id)
            ON DELETE SET NULL
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        category_id UUID,
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        image_url TEXT,
        base_price NUMERIC(10, 2) NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_products_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_products_category
            FOREIGN KEY (category_id)
            REFERENCES categories(id)
            ON DELETE SET NULL
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS product_variants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        product_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        sku VARCHAR(100) NOT NULL UNIQUE,
        price_override NUMERIC(10, 2),
        stock_quantity INT NOT NULL DEFAULT 0,
        attributes JSONB DEFAULT '{}',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_variants_product
            FOREIGN KEY (product_id)
            REFERENCES products(id)
            ON DELETE CASCADE
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS coupons (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID,
        code VARCHAR(50) NOT NULL UNIQUE,
        type coupon_type_enum NOT NULL,
        value NUMERIC(10, 2) NOT NULL,
        max_uses INT,
        uses_count INT NOT NULL DEFAULT 0,
        expires_at TIMESTAMPTZ,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_coupons_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE SET NULL
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS shop_orders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        user_id UUID NOT NULL,
        coupon_id UUID,
        status order_status_enum NOT NULL DEFAULT 'pending',
        total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
        discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
        shipping_address JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_orders_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE RESTRICT,
        CONSTRAINT fk_orders_user
            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE RESTRICT,
        CONSTRAINT fk_orders_coupon
            FOREIGN KEY (coupon_id)
            REFERENCES coupons(id)
            ON DELETE SET NULL
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS order_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL,
        product_variant_id UUID NOT NULL,
        quantity INT NOT NULL DEFAULT 1,
        unit_price NUMERIC(10, 2) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_items_order
            FOREIGN KEY (order_id)
            REFERENCES shop_orders(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_items_variant
            FOREIGN KEY (product_variant_id)
            REFERENCES product_variants(id)
            ON DELETE RESTRICT
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS shop_payments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        order_id UUID NOT NULL UNIQUE,
        amount NUMERIC(10, 2) NOT NULL,
        status payment_status_enum NOT NULL DEFAULT 'pending',
        method VARCHAR(100),
        reference VARCHAR(255),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_payments_order
            FOREIGN KEY (order_id)
            REFERENCES shop_orders(id)
            ON DELETE CASCADE
    );
    """,
]


CREATE_INDEX_QUERIES = [
    "CREATE INDEX IF NOT EXISTS idx_sponsor_packages_event_id ON sponsor_packages(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_registrations_event_id ON registrations(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_registrations_email ON registrations(email);",
    "CREATE INDEX IF NOT EXISTS idx_sponsors_partners_event_id ON sponsors_partners(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_event_id ON api_keys(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX IF NOT EXISTS idx_products_event_id ON products(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);",
    "CREATE INDEX IF NOT EXISTS idx_variants_product_id ON product_variants(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_event_id ON shop_orders(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON shop_orders(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);",
    "CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);",
    "CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);",
    "CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);",
    "CREATE INDEX IF NOT EXISTS idx_talk_reviews_proposal_id ON talk_reviews(proposal_id);",
    "CREATE INDEX IF NOT EXISTS idx_talk_reviews_reviewer_id ON talk_reviews(reviewer_id);",
]


CREATE_VIEW_QUERIES = [
    """
    CREATE OR REPLACE VIEW talk_avg_scores AS
    SELECT
        proposal_id,
        ROUND(AVG(score)::numeric, 2) AS avg_score,
        COUNT(*) AS review_count
    FROM talk_reviews
    GROUP BY proposal_id;
    """,
]


ALTER_TABLE_QUERIES = [
    "ALTER TABLE sponsors_partners ADD COLUMN IF NOT EXISTS package_tier package_tier_enum;",
    "ALTER TABLE sponsors_partners ADD COLUMN IF NOT EXISTS package_id UUID REFERENCES sponsor_packages(id) ON DELETE SET NULL;",
]


def create_tables():
    """Return SQL queries in execution order for creating the schema."""
    conn = connect(settings.db_url)
    with conn.cursor() as cur:
        cur.execute(CREATE_EXTENSIONS_QUERY)
        cur.execute(CREATE_TYPES_QUERY)
        for query in CREATE_TABLE_QUERIES:
            cur.execute(query)
        for query in ALTER_TABLE_QUERIES:
            cur.execute(query)
        for query in CREATE_INDEX_QUERIES:
            cur.execute(query)
        for query in CREATE_VIEW_QUERIES:
            cur.execute(query)
    conn.commit()
    return (
        CREATE_EXTENSIONS_QUERY
        + "\n"
        + CREATE_TYPES_QUERY
        + "\n"
        + "\n".join(CREATE_TABLE_QUERIES)
        + "\n"
        + "\n".join(ALTER_TABLE_QUERIES)
        + "\n"
        + "\n".join(CREATE_INDEX_QUERIES)
        + "\n"
        + "\n".join(CREATE_VIEW_QUERIES)
    )


def run_migrations():
    """Compatibility wrapper returning queries for external migration runners."""
    result = create_tables()
    logger.info("Migrations completed successfully.")
    return result


if __name__ == "__main__":
    run_migrations()
