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
    CREATE TABLE IF NOT EXISTS topics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        name_fr VARCHAR(255) NOT NULL,
        name_en VARCHAR(255) NOT NULL,
        description_fr TEXT,
        description_en TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_topics_event
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
        topic_id UUID,
        format VARCHAR(64) NOT NULL,
        python_percentage INTEGER CHECK (python_percentage >= 0 AND python_percentage <= 100),
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        phone_number VARCHAR(40),
        organization VARCHAR(255),
        bio TEXT,
        country VARCHAR(64),
        experience TEXT,
        photo_url TEXT,
        social_media_links JSONB,
        language VARCHAR(64) NOT NULL DEFAULT 'French',
        level VARCHAR(64),
        needs_equipment BOOLEAN NOT NULL DEFAULT FALSE,
        equipment_details TEXT,
        delivery_mode delivery_method_enum NOT NULL DEFAULT 'onsite',
        status submission_status_enum NOT NULL DEFAULT 'draft',
        agreed_to_code_of_conduct BOOLEAN NOT NULL DEFAULT FALSE,
        agreed_to_privacy_policy BOOLEAN NOT NULL DEFAULT FALSE,
        shared_with_sponsors BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_proposals_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_proposals_topic
            FOREIGN KEY (topic_id)
            REFERENCES topics(id)
            ON DELETE SET NULL
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
    CREATE TABLE IF NOT EXISTS draft_proposals (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        email VARCHAR(255) NOT NULL,
        password_hash TEXT NOT NULL,
        proposal_data JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_draft_proposals_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",

    """
    CREATE TABLE IF NOT EXISTS proposal_formats (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        name_fr VARCHAR(255) NOT NULL,
        name_en VARCHAR(255) NOT NULL,
        description_fr TEXT,
        description_en TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_proposal_formats_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",
]


CREATE_INDEX_QUERIES = [
    "CREATE INDEX IF NOT EXISTS idx_sponsors_partners_event_id ON sponsors_partners(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_event_id ON api_keys(event_id);",
]


ALTER_TABLE_QUERIES = [
    "ALTER TABLE sponsors_partners ADD COLUMN IF NOT EXISTS package_tier package_tier_enum;",
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
    )


def run_migrations():
    """Compatibility wrapper returning queries for external migration runners."""
    result = create_tables()
    logger.info("Migrations completed successfully.")
    return result


if __name__ == "__main__":
    run_migrations()
