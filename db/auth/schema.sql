-- Production-oriented auth schema.
-- This schema is intentionally separate from robo_app because robo_app is
-- rebuilt from views during development.

CREATE SCHEMA IF NOT EXISTS robo_auth;

CREATE TABLE IF NOT EXISTS robo_auth.accounts (
  id text PRIMARY KEY,
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  password_algorithm text NOT NULL DEFAULT 'pbkdf2_sha256',
  status text NOT NULL DEFAULT 'active',
  failed_login_count integer NOT NULL DEFAULT 0,
  locked_until timestamptz,
  last_login_at timestamptz,
  password_updated_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_accounts_email_lower
ON robo_auth.accounts (lower(email));

CREATE TABLE IF NOT EXISTS robo_auth.account_identities (
  id text PRIMARY KEY,
  account_id text NOT NULL REFERENCES robo_auth.accounts(id) ON DELETE CASCADE,
  identity_type text NOT NULL,
  user_id text,
  profile_id text,
  patient_id text,
  staff_id text,
  doctor_id text,
  clinic_id text,
  organization_id text,
  is_primary boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_account_identities_account_id
ON robo_auth.account_identities (account_id);

CREATE INDEX IF NOT EXISTS idx_auth_account_identities_patient_id
ON robo_auth.account_identities (patient_id);

CREATE INDEX IF NOT EXISTS idx_auth_account_identities_staff_id
ON robo_auth.account_identities (staff_id);

CREATE TABLE IF NOT EXISTS robo_auth.account_roles (
  id text PRIMARY KEY,
  account_id text NOT NULL REFERENCES robo_auth.accounts(id) ON DELETE CASCADE,
  role text NOT NULL,
  clinic_id text,
  organization_id text,
  is_primary boolean NOT NULL DEFAULT false,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_account_roles_account_id
ON robo_auth.account_roles (account_id);

CREATE INDEX IF NOT EXISTS idx_auth_account_roles_scope
ON robo_auth.account_roles (role, clinic_id, organization_id);

CREATE TABLE IF NOT EXISTS robo_auth.sessions (
  id text PRIMARY KEY,
  account_id text NOT NULL REFERENCES robo_auth.accounts(id) ON DELETE CASCADE,
  refresh_token_hash text,
  user_agent text,
  ip_address text,
  expires_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_account_id
ON robo_auth.sessions (account_id);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_active
ON robo_auth.sessions (account_id, revoked_at, expires_at);
