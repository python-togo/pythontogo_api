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
        CREATE TYPE partner_type_enum AS ENUM ('partnership', 'sponsorship', 'media_partner', 'python_community_partner', 'community_partner', 'institutional_support', 'venue_support', 'other');
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

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attendance_status_enum') THEN
        CREATE TYPE attendance_status_enum AS ENUM (
            'pending',
            'confirmed',
            'cancelled',
            'checked_in'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status_enum') THEN
        CREATE TYPE payment_status_enum AS ENUM (
            'pending',
            'completed',
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

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_location_enum') THEN
        CREATE TYPE job_location_enum AS ENUM ('remote', 'onsite', 'hybrid');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contract_type_enum') THEN
        CREATE TYPE contract_type_enum AS ENUM ('full-time', 'part-time', 'internship', 'contract');
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
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        headline VARCHAR(255),
        organization VARCHAR(255),
        company_logo_url TEXT,
        country VARCHAR(120),
        bio TEXT NOT NULL,
        photo_url TEXT NOT NULL,
        social_links JSONB,
        sessions JSONB,
        is_featured BOOLEAN NOT NULL DEFAULT FALSE,
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
            REFERENCES venues(id)
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
        benefits_fr TEXT,
        benefits_en TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_proposal_formats_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",
    """
    CREATE TABLE IF NOT EXISTS tickets (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
        quantity INTEGER NOT NULL CHECK (quantity >= 0),
        sales_start TIMESTAMPTZ,
        sales_end TIMESTAMPTZ,
        early_bird_price NUMERIC(10, 2) CHECK (early_bird_price >= 0),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_tickets_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",

    """CREATE TABLE IF NOT EXISTS vouchers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        code VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        discount_percentage NUMERIC(5, 2) CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
        discount_amount NUMERIC(10, 2) CHECK (discount_amount >= 0),
        number_of_uses INTEGER CHECK (number_of_uses >= 0),
        number_of_uses_left INTEGER CHECK (number_of_uses_left >= 0),
        applicable_ticket_ids JSONB,
        applicable_event_ids JSONB,
        applicable_user_emails JSONB,
        applicable_user_ids JSONB,
        already_used_by_user_emails JSONB,
        referer_info JSONB,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        valid_from TIMESTAMPTZ,
        valid_until TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );""",

    """
    CREATE TABLE IF NOT EXISTS registrations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id UUID NOT NULL,
        ticket_id UUID,
        ticket_price NUMERIC(10, 2) NOT NULL CHECK (ticket_price >= 0),
        ticket_quantity INTEGER NOT NULL CHECK (ticket_quantity >= 1),
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        whatsapp_number VARCHAR(40),
        ticket_type VARCHAR(255) NOT NULL,
        attendance_status attendance_status_enum NOT NULL DEFAULT 'pending',
        payment_status payment_status_enum NOT NULL DEFAULT 'pending',
        dietary_restrictions TEXT,
        payment_reference TEXT,
        payment_link TEXT,
        voucher_id UUID,
        voucher_code VARCHAR(255),
        agreed_to_code_of_conduct BOOLEAN NOT NULL DEFAULT FALSE,
        agreed_to_privacy_policy BOOLEAN NOT NULL DEFAULT FALSE,
        shared_with_sponsors BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        description TEXT,
        CONSTRAINT fk_registrations_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_registrations_voucher
            FOREIGN KEY (voucher_id)
            REFERENCES vouchers(id)
            ON DELETE SET NULL,
        CONSTRAINT fk_registrations_ticket
            FOREIGN KEY (ticket_id)
            REFERENCES tickets(id)
            ON DELETE SET NULL


    );""",
    """CREATE TABLE IF NOT EXISTS student_proofs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        registration_id UUID NOT NULL,
        file_url TEXT NOT NULL,
        file_type VARCHAR(255) NOT NULL,
        is_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
        is_approved BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_student_proofs_registration
            FOREIGN KEY (registration_id)
            REFERENCES registrations(id)
            ON DELETE CASCADE
    );""",

    """
    CREATE TABLE IF NOT EXISTS job_offers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        company VARCHAR(255) NOT NULL,
        logo_url TEXT,
        location job_location_enum NOT NULL,
        contract_type contract_type_enum NOT NULL,
        country VARCHAR(255),
        apply_url TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        salary_range VARCHAR(255),
        application_deadline TIMESTAMPTZ,
        tags JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );""",

    """
    CREATE TABLE IF NOT EXISTS team_members (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        role VARCHAR(255) NOT NULL,
        bio TEXT,
        photo_url TEXT,
        social_links JSONB,
        is_volunteer BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        position INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        event_id UUID NOT NULL,
        CONSTRAINT fk_team_members_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
    );""",
    """CREATE TABLE IF NOT EXISTS access_grants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        first_name VARCHAR(255) NOT NULL,
        last_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        gender VARCHAR(20) NOT NULL DEFAULT 'Not specified',
        phone_number VARCHAR(40) NOT NULL,
        location VARCHAR(255) NOT NULL,
        country VARCHAR(120) NOT NULL DEFAULT 'Togo',
        python_journey TEXT,
        need_ticket BOOLEAN NOT NULL DEFAULT FALSE,
        need_transport BOOLEAN NOT NULL DEFAULT FALSE,
        need_accommodation BOOLEAN NOT NULL DEFAULT FALSE,
        support_details TEXT,
        grant_consent BOOLEAN NOT NULL DEFAULT FALSE,
        event_id UUID NOT NULL,
        is_student BOOLEAN NOT NULL DEFAULT FALSE,
        student_proof_url TEXT,
        is_approved BOOLEAN NOT NULL DEFAULT FALSE,
        is_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
        comment TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_access_grants_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE CASCADE
        );""",
    """
    CREATE TABLE IF NOT EXISTS feedbacks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        sex VARCHAR(64),
        age VARCHAR(32),
        profession VARCHAR(255),
        country VARCHAR(120),
        python_level VARCHAR(120),
        heard TEXT,
        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
        overall TEXT,
        favorite TEXT,
        improvements TEXT,
        comments TEXT,
         is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
         created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
         updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
     );""",
     """
     CREATE TABLE IF NOT EXISTS users (
         id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
         email VARCHAR(255) NOT NULL UNIQUE,
         full_name VARCHAR(255) NOT NULL,
         hashed_password TEXT NOT NULL,
         is_active BOOLEAN NOT NULL DEFAULT TRUE,
         is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
         created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
         updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
     );""",
     """
     CREATE TABLE IF NOT EXISTS refresh_tokens (
         id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
         user_id UUID NOT NULL,
         token TEXT NOT NULL UNIQUE,
         expires_at TIMESTAMPTZ NOT NULL,
         revoked BOOLEAN NOT NULL DEFAULT FALSE,
         created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
         CONSTRAINT fk_refresh_tokens_user
             FOREIGN KEY (user_id)
             REFERENCES users(id)
             ON DELETE CASCADE
     );""",

 ]

CREATE_INDEX_QUERIES = [
    "CREATE INDEX IF NOT EXISTS idx_sponsors_partners_event_id ON sponsors_partners(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_event_id ON api_keys(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_job_offers_is_active ON job_offers(is_active);",
    "CREATE INDEX IF NOT EXISTS idx_job_offers_company ON job_offers(company);",
    "CREATE INDEX IF NOT EXISTS idx_team_members_event_id ON team_members(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_team_members_is_active ON team_members(is_active);",
    "CREATE INDEX IF NOT EXISTS idx_team_members_position ON team_members(position);",
    "CREATE INDEX IF NOT EXISTS idx_access_grants_event_id ON access_grants(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_access_grants_email ON access_grants(email);",
]


ALTER_TABLE_QUERIES = [
    "ALTER TABLE sponsors_partners ADD COLUMN IF NOT EXISTS package_tier package_tier_enum;",
    "ALTER TABLE feedbacks DROP COLUMN IF EXISTS event_code;",
    "ALTER TABLE feedbacks DROP COLUMN IF EXISTS name;",
    "ALTER TABLE feedbacks DROP COLUMN IF EXISTS email;",
    "ALTER TABLE feedbacks DROP COLUMN IF EXISTS subject;",
    "ALTER TABLE feedbacks DROP COLUMN IF EXISTS message;",
    "ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS days JSONB DEFAULT '[]'::jsonb;",
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
