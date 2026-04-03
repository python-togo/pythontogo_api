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
        CREATE TYPE partner_type_enum AS ENUM ('partnership', 'sponsorship');
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
        CREATE TYPE event_type_enum AS ENUM ('workshop', 'conference', 'dinner', 'community');
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

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'adjustment_status_enum') THEN
        CREATE TYPE adjustment_status_enum AS ENUM (
            'pending',
            'approved',
            'rejected'
        );
    END IF;
END
$$;
"""


CREATE_TABLE_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS pycon_editions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        code VARCHAR(32) NOT NULL UNIQUE,
        year INT NOT NULL UNIQUE,
        title VARCHAR(255) NOT NULL,
        tagline TEXT,
        location VARCHAR(255) NOT NULL,
        country VARCHAR(120) DEFAULT 'Togo',
        city VARCHAR(120) DEFAULT 'Lome',
        timezone VARCHAR(64) NOT NULL DEFAULT 'Africa/Lome',
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        website_url TEXT,
        report_url TEXT,
        cfp_open_at TIMESTAMPTZ,
        cfp_close_at TIMESTAMPTZ,
        ticket_sales_open_at TIMESTAMPTZ,
        ticket_sales_close_at TIMESTAMPTZ,
        is_active BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CHECK (end_date >= start_date)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS roles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        name VARCHAR(80) NOT NULL,
        description TEXT,
        is_system BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_roles_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_roles_edition_name UNIQUE (pycon_edition_id, name)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS permissions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        code VARCHAR(120) NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id UUID NOT NULL,
        permission_id UUID NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (role_id, permission_id),
        CONSTRAINT fk_role_permissions_role
            FOREIGN KEY (role_id)
            REFERENCES roles(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_role_permissions_permission
            FOREIGN KEY (permission_id)
            REFERENCES permissions(id)
            ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS team_members (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        role_id UUID,
        first_name VARCHAR(120) NOT NULL,
        last_name VARCHAR(120) NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password_hash TEXT NOT NULL,
        phone VARCHAR(40),
        title VARCHAR(120),
        bio TEXT,
        photo_url TEXT,
        social_links JSONB NOT NULL DEFAULT '{}'::jsonb,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        last_login_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_team_members_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_team_members_role
            FOREIGN KEY (role_id)
            REFERENCES roles(id)
            ON DELETE SET NULL,
        CONSTRAINT uq_team_members_edition_email UNIQUE (pycon_edition_id, email)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS team_member_permissions (
        team_member_id UUID NOT NULL,
        permission_id UUID NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (team_member_id, permission_id),
        CONSTRAINT fk_team_member_permissions_member
            FOREIGN KEY (team_member_id)
            REFERENCES team_members(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_team_member_permissions_permission
            FOREIGN KEY (permission_id)
            REFERENCES permissions(id)
            ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS venues (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        address TEXT,
        city VARCHAR(120),
        country VARCHAR(120),
        capacity INT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_venues_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_venues_edition_name UNIQUE (pycon_edition_id, name)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        venue_id UUID,
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(255) NOT NULL,
        event_type event_type_enum NOT NULL,
        starts_at TIMESTAMPTZ NOT NULL,
        ends_at TIMESTAMPTZ NOT NULL,
        description TEXT,
        is_public BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_events_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_events_venue
            FOREIGN KEY (venue_id)
            REFERENCES venues(id)
            ON DELETE SET NULL,
        CONSTRAINT uq_events_edition_slug UNIQUE (pycon_edition_id, slug),
        CHECK (ends_at > starts_at)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tracks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        name VARCHAR(120) NOT NULL,
        description TEXT,
        color VARCHAR(20),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_tracks_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_tracks_edition_name UNIQUE (pycon_edition_id, name)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS speakers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        first_name VARCHAR(120) NOT NULL,
        last_name VARCHAR(120) NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        headline VARCHAR(255),
        organization VARCHAR(255),
        country VARCHAR(120),
        bio TEXT,
        photo_url TEXT,
        social_links JSONB NOT NULL DEFAULT '{}'::jsonb,
        website_url TEXT,
        is_keynote BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_speakers_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_speakers_edition_email UNIQUE (pycon_edition_id, email)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS session_proposals (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        primary_speaker_id UUID,
        title VARCHAR(255) NOT NULL,
        abstract TEXT NOT NULL,
        level VARCHAR(40),
        language VARCHAR(40) NOT NULL DEFAULT 'en',
        session_type session_type_enum NOT NULL,
        duration_minutes INT NOT NULL DEFAULT 30,
        status submission_status_enum NOT NULL DEFAULT 'submitted',
        reviewer_notes TEXT,
        submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        decided_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_session_proposals_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_session_proposals_speaker
            FOREIGN KEY (primary_speaker_id)
            REFERENCES speakers(id)
            ON DELETE SET NULL,
        CHECK (duration_minutes > 0)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        event_id UUID,
        track_id UUID,
        venue_id UUID,
        proposal_id UUID,
        title VARCHAR(255) NOT NULL,
        slug VARCHAR(255) NOT NULL,
        session_type session_type_enum NOT NULL,
        summary TEXT,
        starts_at TIMESTAMPTZ NOT NULL,
        ends_at TIMESTAMPTZ NOT NULL,
        capacity INT,
        is_recorded BOOLEAN NOT NULL DEFAULT FALSE,
        livestream_url TEXT,
        slides_url TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_sessions_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_sessions_event
            FOREIGN KEY (event_id)
            REFERENCES events(id)
            ON DELETE SET NULL,
        CONSTRAINT fk_sessions_track
            FOREIGN KEY (track_id)
            REFERENCES tracks(id)
            ON DELETE SET NULL,
        CONSTRAINT fk_sessions_venue
            FOREIGN KEY (venue_id)
            REFERENCES venues(id)
            ON DELETE SET NULL,
        CONSTRAINT fk_sessions_proposal
            FOREIGN KEY (proposal_id)
            REFERENCES session_proposals(id)
            ON DELETE SET NULL,
        CONSTRAINT uq_sessions_edition_slug UNIQUE (pycon_edition_id, slug),
        CHECK (ends_at > starts_at)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS session_speakers (
        session_id UUID NOT NULL,
        speaker_id UUID NOT NULL,
        is_primary BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (session_id, speaker_id),
        CONSTRAINT fk_session_speakers_session
            FOREIGN KEY (session_id)
            REFERENCES sessions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_session_speakers_speaker
            FOREIGN KEY (speaker_id)
            REFERENCES speakers(id)
            ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sponsors_partners (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        website_url TEXT,
        contact_name VARCHAR(255),
        contact_email VARCHAR(255) NOT NULL,
        contact_phone VARCHAR(40),
        description TEXT,
        logo_url TEXT,
        partner_type partner_type_enum NOT NULL,
        is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_sponsors_partners_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_sponsors_partners_edition_name UNIQUE (pycon_edition_id, name)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sponsorship_packages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        tier package_tier_enum NOT NULL,
        title VARCHAR(120) NOT NULL,
        price NUMERIC(12, 2) NOT NULL,
        currency VARCHAR(3) NOT NULL DEFAULT 'USD',
        benefits JSONB NOT NULL DEFAULT '[]'::jsonb,
        max_slots INT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_sponsorship_packages_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_sponsorship_packages_edition_tier UNIQUE (pycon_edition_id, tier),
        CHECK (price >= 0)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sponsorships (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        partner_id UUID NOT NULL,
        package_id UUID,
        amount NUMERIC(12, 2),
        currency VARCHAR(3) DEFAULT 'USD',
        signed_at TIMESTAMPTZ,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_sponsorships_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_sponsorships_partner
            FOREIGN KEY (partner_id)
            REFERENCES sponsors_partners(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_sponsorships_package
            FOREIGN KEY (package_id)
            REFERENCES sponsorship_packages(id)
            ON DELETE SET NULL,
        CHECK (amount IS NULL OR amount >= 0)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ticket_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        name VARCHAR(120) NOT NULL,
        description TEXT,
        price NUMERIC(12, 2) NOT NULL,
        currency VARCHAR(3) NOT NULL DEFAULT 'USD',
        quantity_total INT,
        quantity_sold INT NOT NULL DEFAULT 0,
        sales_start_at TIMESTAMPTZ,
        sales_end_at TIMESTAMPTZ,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_ticket_types_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_ticket_types_edition_name UNIQUE (pycon_edition_id, name),
        CHECK (price >= 0),
        CHECK (quantity_total IS NULL OR quantity_total >= 0),
        CHECK (quantity_sold >= 0),
        CHECK (quantity_total IS NULL OR quantity_sold <= quantity_total)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS attendees (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        first_name VARCHAR(120) NOT NULL,
        last_name VARCHAR(120) NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        whatsapp_number VARCHAR(40) NOT NULL,
        discord_handle VARCHAR(80),
        phone VARCHAR(40),
        company VARCHAR(255),
        job_title VARCHAR(255),
        country VARCHAR(120),
        city VARCHAR(120),
        dietary_requirements TEXT,
        accessibility_requirements TEXT,
        consent_marketing BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_attendees_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT uq_attendees_edition_email UNIQUE (pycon_edition_id, email)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS registrations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        attendee_id UUID NOT NULL,
        ticket_type_id UUID NOT NULL,
        registration_code VARCHAR(32) NOT NULL,
        contact_email VARCHAR(255) NOT NULL,
        contact_whatsapp VARCHAR(40) NOT NULL,
        contact_discord_handle VARCHAR(80),
        status registration_status_enum NOT NULL DEFAULT 'pending',
        total_amount_due NUMERIC(12, 2) NOT NULL DEFAULT 0,
        total_amount_paid NUMERIC(12, 2) NOT NULL DEFAULT 0,
        manual_validation_required BOOLEAN NOT NULL DEFAULT TRUE,
        validation_note TEXT,
        validated_by_team_member_id UUID,
        validated_at TIMESTAMPTZ,
        checked_in_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_registrations_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_registrations_attendee
            FOREIGN KEY (attendee_id)
            REFERENCES attendees(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_registrations_ticket_type
            FOREIGN KEY (ticket_type_id)
            REFERENCES ticket_types(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_registrations_validated_by
            FOREIGN KEY (validated_by_team_member_id)
            REFERENCES team_members(id)
            ON DELETE SET NULL,
        CONSTRAINT uq_registrations_code UNIQUE (registration_code),
        CONSTRAINT uq_registrations_edition_attendee UNIQUE (pycon_edition_id, attendee_id),
        CHECK (total_amount_due >= 0),
        CHECK (total_amount_paid >= 0)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        registration_id UUID NOT NULL,
        amount NUMERIC(12, 2) NOT NULL,
        currency VARCHAR(3) NOT NULL DEFAULT 'USD',
        provider VARCHAR(80),
        provider_reference VARCHAR(255),
        status payment_status_enum NOT NULL DEFAULT 'pending',
        submitted_proof_url TEXT,
        submitted_note TEXT,
        payer_email VARCHAR(255),
        payer_whatsapp VARCHAR(40),
        payer_discord_handle VARCHAR(80),
        confirmation_message_sent_at TIMESTAMPTZ,
        confirmed_by_team_member_id UUID,
        confirmed_at TIMESTAMPTZ,
        confirmation_note TEXT,
        paid_at TIMESTAMPTZ,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_payments_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_payments_registration
            FOREIGN KEY (registration_id)
            REFERENCES registrations(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_payments_confirmed_by
            FOREIGN KEY (confirmed_by_team_member_id)
            REFERENCES team_members(id)
            ON DELETE SET NULL,
        CHECK (amount >= 0)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS registration_payment_adjustments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID NOT NULL,
        registration_id UUID NOT NULL,
        adjustment_type adjustment_type_enum NOT NULL,
        amount_delta NUMERIC(12, 2) NOT NULL,
        reason TEXT NOT NULL,
        status adjustment_status_enum NOT NULL DEFAULT 'pending',
        created_by_team_member_id UUID,
        approved_by_team_member_id UUID,
        approved_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_registration_adjustments_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_registration_adjustments_registration
            FOREIGN KEY (registration_id)
            REFERENCES registrations(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_registration_adjustments_created_by
            FOREIGN KEY (created_by_team_member_id)
            REFERENCES team_members(id)
            ON DELETE SET NULL,
        CONSTRAINT fk_registration_adjustments_approved_by
            FOREIGN KEY (approved_by_team_member_id)
            REFERENCES team_members(id)
            ON DELETE SET NULL,
        CHECK (amount_delta <> 0)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS contact_messages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pycon_edition_id UUID,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        subject VARCHAR(255),
        message TEXT NOT NULL,
        is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_contact_messages_edition
            FOREIGN KEY (pycon_edition_id)
            REFERENCES pycon_editions(id)
            ON DELETE SET NULL
    );
    """,
]


CREATE_INDEX_QUERIES = [
    "CREATE INDEX IF NOT EXISTS idx_events_edition_starts_at ON events(pycon_edition_id, starts_at);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_edition_starts_at ON sessions(pycon_edition_id, starts_at);",
    "CREATE INDEX IF NOT EXISTS idx_registrations_edition_status ON registrations(pycon_edition_id, status);",
    "CREATE INDEX IF NOT EXISTS idx_payments_edition_status ON payments(pycon_edition_id, status);",
    "CREATE INDEX IF NOT EXISTS idx_adjustments_registration_status ON registration_payment_adjustments(registration_id, status);",
    "CREATE INDEX IF NOT EXISTS idx_team_members_edition_active ON team_members(pycon_edition_id, is_active);",
]


def create_tables():
    """Return SQL queries in execution order for creating the schema."""
    conn = connect(settings.db_url)
    with conn.cursor() as cur:
        cur.execute(CREATE_EXTENSIONS_QUERY)
        cur.execute(CREATE_TYPES_QUERY)
        for query in CREATE_TABLE_QUERIES:
            cur.execute(query)
        for query in CREATE_INDEX_QUERIES:
            cur.execute(query)
    conn.commit()
    return CREATE_EXTENSIONS_QUERY + "\n" + CREATE_TYPES_QUERY + "\n" + "\n".join(CREATE_TABLE_QUERIES) + "\n" + "\n".join(CREATE_INDEX_QUERIES)


def run_migrations():
    """Compatibility wrapper returning queries for external migration runners."""
    result = create_tables()
    logger.info("Migrations completed successfully.")
    return result


if __name__ == "__main__":
    run_migrations()
