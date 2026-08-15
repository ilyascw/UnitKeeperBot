-- One-off production data fix: write the missing opening entry for the
-- balance that was seeded straight into `balances` on 2026-08-02 (see #37).
--
-- An opening balance carried in from the legacy bot is a first-class concept
-- here: the initial migration inserts the balance AND pairs it with a
-- `manual_adjustment` entry described as a migrated opening balance
-- (common/alembic/versions/20260315_0001_initial_unitkeeper_schema.py:289-319).
-- Production was seeded by a script instead, which wrote the balance and
-- skipped the entry. The balance is correct and is NOT touched here; only the
-- missing entry is added, so the ledger can reconstruct it.
--
-- Affected: group 1, user 315174024, opening balance 5.00. Every other user
-- reconciles against the ledger exactly, so nothing else needs an entry.
--
-- The entry is single-sided, exactly like the migration's: a legacy carry-in
-- enters from outside this system's double-entry universe, and the schema has
-- no equity/opening account to book the other leg against. Consequence, by
-- design and not a defect: after this runs, the group-wide ledger sum is +5.00
-- rather than 0.00, matching what the migration would have produced.
--
-- Run this AFTER fix-premature-sprint-close-2026-08-03.sql. That script's
-- per-user reconciliation check cannot pass until this entry exists.
--
-- HOW TO RUN
--   1. Back up first:  pg_dump -Fc -f before-fix.dump <db>
--   2. Run as-is. It ends with ROLLBACK on purpose - read the verification
--      output, then change ROLLBACK to COMMIT to apply.

BEGIN;

-- Step 1: the drift this entry is meant to close. Expect exactly one row,
-- group 1 / user 315174024, with missing_entry = 5.00.
SELECT
    b.group_id,
    b.user_id,
    b.current_balance,
    coalesce(sum(bt.amount_delta), 0)                        AS ledger_balance,
    b.current_balance - coalesce(sum(bt.amount_delta), 0)    AS missing_entry
FROM balances b
LEFT JOIN balance_transactions bt
       ON bt.group_id = b.group_id
      AND bt.user_id  = b.user_id
      AND bt.account_type = 'user'
GROUP BY b.group_id, b.user_id, b.current_balance
HAVING b.current_balance - coalesce(sum(bt.amount_delta), 0) <> 0
ORDER BY b.group_id, b.user_id;

-- Step 2: insert one opening entry per drifting balance, for exactly the
-- amount the ledger is missing. Derived from the data, nothing hardcoded.
--
-- created_at is backdated to the balance row's own creation timestamp: an
-- opening entry belongs at the opening, otherwise the per-user history reads
-- as if the balance appeared out of nowhere and was topped up two weeks later.
INSERT INTO balance_transactions (
    group_id, account_type, user_id, transaction_type, amount_delta,
    description, created_at, updated_at
)
SELECT
    drift.group_id,
    'user',
    drift.user_id,
    'manual_adjustment',
    drift.missing_entry,
    'Opening balance carried in at group bootstrap',
    drift.created_at,
    now()
FROM (
    SELECT
        b.group_id,
        b.user_id,
        b.created_at,
        b.current_balance - coalesce(sum(bt.amount_delta), 0) AS missing_entry
    FROM balances b
    LEFT JOIN balance_transactions bt
           ON bt.group_id = b.group_id
          AND bt.user_id  = b.user_id
          AND bt.account_type = 'user'
    GROUP BY b.group_id, b.user_id, b.created_at, b.current_balance
    HAVING b.current_balance - coalesce(sum(bt.amount_delta), 0) <> 0
) AS drift;

-- ---------------------------------------------------------------------------
-- Step 3: verification. Read this BEFORE deciding to commit.
-- ---------------------------------------------------------------------------

-- Every user balance must now reconcile against the ledger. Zero rows = good.
SELECT
    b.group_id,
    b.user_id,
    b.current_balance,
    coalesce(sum(bt.amount_delta), 0)                     AS ledger_balance,
    b.current_balance - coalesce(sum(bt.amount_delta), 0) AS drift
FROM balances b
LEFT JOIN balance_transactions bt
       ON bt.group_id = b.group_id
      AND bt.user_id  = b.user_id
      AND bt.account_type = 'user'
GROUP BY b.group_id, b.user_id, b.current_balance
HAVING b.current_balance - coalesce(sum(bt.amount_delta), 0) <> 0
ORDER BY b.group_id, b.user_id;

-- The new entries, for the record.
SELECT id, group_id, user_id, transaction_type, amount_delta, description, created_at
FROM balance_transactions
WHERE description = 'Opening balance carried in at group bootstrap'
ORDER BY id;

-- Change to COMMIT once the reconciliation query above returns no rows.
ROLLBACK;
