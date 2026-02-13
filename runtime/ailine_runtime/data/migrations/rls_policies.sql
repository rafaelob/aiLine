-- =============================================================================
-- Row Level Security (RLS) policies for AiLine multi-tenancy
-- =============================================================================
--
-- PURPOSE:
--   Defense-in-depth tenant isolation at the PostgreSQL level. Even if
--   application code has a bug that omits a WHERE teacher_id = ... clause,
--   RLS ensures one teacher cannot read or modify another teacher's data.
--
-- WHEN TO APPLY:
--   This is a REFERENCE migration for the production hardening phase.
--   It should be applied AFTER:
--   1. The application sets `app.teacher_id` via SET LOCAL on every
--      connection/transaction (see note below).
--   2. The database role used by the application is NOT a superuser
--      (superusers bypass RLS).
--
-- HOW IT WORKS:
--   1. The application middleware sets a session-local variable:
--        SET LOCAL app.teacher_id = '<uuid>';
--      This is done at the start of each database transaction.
--   2. RLS policies use current_setting('app.teacher_id') to filter rows.
--   3. SELECT/INSERT/UPDATE/DELETE are all scoped to the authenticated tenant.
--
-- APPLICATION INTEGRATION:
--   In the SQLAlchemy session factory, add an event listener:
--
--     @event.listens_for(engine.sync_engine, "connect")
--     def set_tenant_id(dbapi_conn, connection_record):
--         # Called at connection checkout time
--         pass
--
--     @event.listens_for(Session, "after_begin")
--     def set_tenant_context(session, transaction, connection):
--         teacher_id = get_current_teacher_id_or_none()
--         if teacher_id:
--             connection.execute(
--                 text("SET LOCAL app.teacher_id = :tid"),
--                 {"tid": teacher_id},
--             )
--
-- ROLLBACK:
--   To remove all RLS policies and disable RLS:
--     ALTER TABLE <table> DISABLE ROW LEVEL SECURITY;
--     DROP POLICY IF EXISTS <policy_name> ON <table>;
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Materials
-- ---------------------------------------------------------------------------

ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

-- Allow teachers to see only their own materials
CREATE POLICY materials_tenant_isolation ON materials
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- 2. Chunks (material chunks for vector search)
-- ---------------------------------------------------------------------------

ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY chunks_tenant_isolation ON chunks
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- 3. Courses
-- ---------------------------------------------------------------------------

ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

CREATE POLICY courses_tenant_isolation ON courses
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- 4. Lessons
-- ---------------------------------------------------------------------------

ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;

CREATE POLICY lessons_tenant_isolation ON lessons
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- 5. Pipeline Runs
-- ---------------------------------------------------------------------------

ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY pipeline_runs_tenant_isolation ON pipeline_runs
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- 6. Tutor Agents
-- ---------------------------------------------------------------------------

ALTER TABLE tutor_agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tutor_agents_tenant_isolation ON tutor_agents
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- 7. Tutor Sessions
-- ---------------------------------------------------------------------------

ALTER TABLE tutor_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tutor_sessions_tenant_isolation ON tutor_sessions
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- 8. Accessibility Profiles
-- ---------------------------------------------------------------------------

ALTER TABLE accessibility_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY accessibility_profiles_tenant_isolation ON accessibility_profiles
    USING (teacher_id = current_setting('app.teacher_id', true))
    WITH CHECK (teacher_id = current_setting('app.teacher_id', true));

-- ---------------------------------------------------------------------------
-- Notes:
-- ---------------------------------------------------------------------------
--
-- * current_setting('app.teacher_id', true) returns NULL if the variable
--   is not set (the `true` parameter means "missing_ok"). This means that
--   if the application forgets to SET LOCAL, NO rows will be visible --
--   a safe default (deny by default).
--
-- * The `teachers` table itself does NOT have RLS because it is the
--   identity table. Access to it should be controlled at the application
--   level (a teacher can only read their own row).
--
-- * The `curriculum_objectives` table does NOT have RLS because curriculum
--   data is shared across all tenants (it is system reference data).
--
-- * The `run_events` table inherits isolation through its FK to
--   pipeline_runs. An explicit RLS policy is not strictly necessary but
--   could be added for defense-in-depth if the table grows.
--
-- * For admin/support access, create a separate PostgreSQL role that
--   bypasses RLS (ALTER ROLE admin_role BYPASSRLS) -- never use the
--   application role for admin queries.
