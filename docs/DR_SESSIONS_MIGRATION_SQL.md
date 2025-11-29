# Director Sessions Table Migration - SQL Queries

**Date:** 2025-11-28
**Purpose:** Migrate from broken `sessions` table to new `dr_sessions` table with complete schema
**Status:** Phase 1 ✅ Complete | Phase 2-4 ⏳ Pending

---

## ✅ Phase 1: Archive Old Sessions Table (COMPLETED)

Old `sessions` table renamed to `dr_sessions_archive_pre_nov2025`

---

## Phase 2: Create New `dr_sessions` Table

**Copy and paste this entire block into Supabase SQL Editor:**

```sql
-- Create Director-specific sessions table with COMPLETE schema
CREATE TABLE public.dr_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    current_state TEXT NOT NULL DEFAULT 'PROVIDE_GREETING',
    conversation_history JSONB DEFAULT '[]'::jsonb,
    user_initial_request TEXT,
    clarifying_answers JSONB,
    confirmation_plan JSONB,
    presentation_strawman JSONB,
    presentation_url TEXT,
    refinement_feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for query performance
CREATE INDEX idx_dr_sessions_user_id ON dr_sessions(user_id);
CREATE INDEX idx_dr_sessions_composite ON dr_sessions(id, user_id);
CREATE INDEX idx_dr_sessions_updated_at ON dr_sessions(updated_at DESC);
CREATE INDEX idx_dr_sessions_state ON dr_sessions(current_state);

-- Enable Row Level Security with permissive policy
ALTER TABLE dr_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all access for dr_sessions"
ON dr_sessions
FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);

-- Grant permissions to all roles (Director uses anon key)
GRANT ALL ON dr_sessions TO anon;
GRANT ALL ON dr_sessions TO authenticated;
GRANT ALL ON dr_sessions TO service_role;
GRANT ALL ON dr_sessions TO postgres;
```

**Expected Result:** Table created successfully with 12 columns and 4 indexes.

---

## Phase 3: Verify Table Structure

**Step 3A: Check all columns exist**

```sql
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'dr_sessions'
ORDER BY ordinal_position;
```

**Expected Output:** Should show 12 columns:
1. id (text, NOT NULL)
2. user_id (text, NOT NULL) ← CRITICAL: Was missing in old table
3. current_state (text, NOT NULL, default 'PROVIDE_GREETING')
4. conversation_history (jsonb, nullable, default '[]')
5. user_initial_request (text, nullable)
6. clarifying_answers (jsonb, nullable)
7. confirmation_plan (jsonb, nullable)
8. presentation_strawman (jsonb, nullable)
9. presentation_url (text, nullable) ← Was missing in old table
10. refinement_feedback (text, nullable)
11. created_at (timestamptz, default NOW())
12. updated_at (timestamptz, default NOW())

---

**Step 3B: Verify indexes were created**

```sql
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'dr_sessions';
```

**Expected Output:** Should show 5 indexes (1 primary key + 4 performance indexes)

---

**Step 3C: Verify RLS policy**

```sql
SELECT
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'dr_sessions';
```

**Expected Output:** Should show "Enable all access for dr_sessions" policy for anon and authenticated roles.

---

**Step 3D: Verify permissions**

```sql
SELECT
    grantee,
    privilege_type
FROM information_schema.table_privileges
WHERE table_schema = 'public'
  AND table_name = 'dr_sessions'
  AND grantee IN ('anon', 'authenticated', 'service_role', 'postgres')
ORDER BY grantee, privilege_type;
```

**Expected Output:** Should show INSERT, SELECT, UPDATE, DELETE for anon, authenticated, service_role, and postgres.

---

## Phase 4: Test Operations

**Test 4A: INSERT operation**

```sql
INSERT INTO dr_sessions (
    id,
    user_id,
    current_state,
    conversation_history,
    created_at,
    updated_at
) VALUES (
    'test-' || gen_random_uuid()::text,
    'test-user-123',
    'PROVIDE_GREETING',
    '[]'::jsonb,
    NOW(),
    NOW()
)
RETURNING id, user_id, current_state, created_at;
```

**Expected Result:** Returns 1 row with the inserted data.

---

**Test 4B: SELECT with user_id filter (Director's main query pattern)**

```sql
SELECT *
FROM dr_sessions
WHERE user_id = 'test-user-123';
```

**Expected Result:** Returns the test row just inserted.

---

**Test 4C: UPDATE operation**

```sql
UPDATE dr_sessions
SET current_state = 'ASK_CLARIFYING_QUESTIONS',
    updated_at = NOW()
WHERE user_id = 'test-user-123'
RETURNING id, user_id, current_state, updated_at;
```

**Expected Result:** Returns 1 row showing updated state.

---

**Test 4D: SELECT with composite filter (exact Director query)**

```sql
SELECT *
FROM dr_sessions
WHERE id IN (SELECT id FROM dr_sessions WHERE user_id = 'test-user-123')
  AND user_id = 'test-user-123';
```

**Expected Result:** Returns the test row.

---

**Test 4E: Clean up test data**

```sql
DELETE FROM dr_sessions WHERE user_id = 'test-user-123';
```

**Expected Result:** 1 row deleted.

---

**Test 4F: Verify table is empty and ready for production**

```sql
SELECT COUNT(*) as row_count FROM dr_sessions;
```

**Expected Result:** 0 rows (clean slate for production).

---

## Phase 5: Verify Archive Table

**Check archived data is still accessible:**

```sql
SELECT
    COUNT(*) as total_archived_sessions,
    MIN(created_at) as oldest_session,
    MAX(created_at) as newest_session
FROM dr_sessions_archive_pre_nov2025;
```

**Expected Result:** Should show 41 rows from July 2025 (preserved for reference).

---

## Post-Migration Verification

**After deploying code changes, run this to verify Director is using new table:**

```sql
-- Check recent activity in dr_sessions
SELECT
    id,
    user_id,
    current_state,
    created_at,
    updated_at
FROM dr_sessions
ORDER BY created_at DESC
LIMIT 10;
```

**Expected Result:** Should show new sessions being created by Director after deployment.

---

## Rollback Plan (If Needed)

**Only use if migration fails and you need to revert:**

```sql
-- Drop new table
DROP TABLE IF EXISTS dr_sessions CASCADE;

-- Restore old table name
ALTER TABLE dr_sessions_archive_pre_nov2025 RENAME TO sessions;
```

**WARNING:** This will lose any new sessions created after migration. Only use as emergency rollback.

---

## Summary

- ✅ Phase 1: Old table archived
- ⏳ Phase 2: Create new `dr_sessions` table (run SQL above)
- ⏳ Phase 3: Verify schema (4 verification queries)
- ⏳ Phase 4: Test operations (6 test queries)
- ⏳ Phase 5: Verify archive accessible

**Next Steps After SQL:**
1. Update code to use `dr_sessions` table name
2. Fix async/sync mismatch in Supabase client
3. Deploy to Railway
4. Monitor logs for successful database operations
