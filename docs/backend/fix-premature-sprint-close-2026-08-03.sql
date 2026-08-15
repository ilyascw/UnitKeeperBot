-- One-off production data fix for the prematurely settled sprint window
-- 2026-08-03..2026-08-09 (see issue #28).
--
-- The old scheduler closed that window at 2026-08-09 00:05 UTC — 03:05 Moscow
-- on its FINAL day, ~21 hours early. Balances were written while the Mini App
-- still accepted completions, so the settlement reflects a partial sprint.
--
-- This script writes the sprint off rather than re-settling it: the run row is
-- kept as CLOSED with zeroed totals, so the fixed scheduler will NOT rediscover
-- the window and close it again. See the note at the bottom for the
-- re-settle-instead alternative.
--
-- NOTHING here is hardcoded from the incident report: every amount is derived
-- from the ledger rows the bad close actually wrote. The reported figures
-- (groups 1 and 4, -20.00 and -8.00) are used only as an assertion in step 1.
--
-- HOW TO RUN
--   1. Take a backup first:  pg_dump -Fc -f before-fix.dump <db>
--   2. Run step 0 and step 1 alone and read the output.
--   3. Only then run the transaction block. It ends with ROLLBACK on purpose —
--      read the verification output, and change ROLLBACK to COMMIT to apply.

-- ---------------------------------------------------------------------------
-- Step 0: identify the affected runs. Expect one row per affected group.
-- ---------------------------------------------------------------------------
SELECT
    sr.id            AS sprint_run_id,
    sr.group_id,
    g.name           AS group_name,
    g.timezone,
    sr.status,
    sr.total_planned_units,
    sr.total_completed_units,
    sr.bonus_units,
    sr.balance_delta,
    sr.closed_at
FROM sprint_runs sr
JOIN groups g ON g.id = sr.group_id
WHERE sr.period_start = DATE '2026-08-03'
  AND sr.period_end   = DATE '2026-08-09'
ORDER BY sr.group_id;

-- ---------------------------------------------------------------------------
-- Step 1: what the bad close actually posted to the ledger, per group.
-- Sanity-check this against the incident report before continuing:
-- groups 1 and 4 should show user-leg totals of -20.00 and -8.00.
-- ---------------------------------------------------------------------------
SELECT
    bt.group_id,
    bt.account_type,
    count(*)              AS legs,
    sum(bt.amount_delta)  AS total_delta
FROM balance_transactions bt
JOIN sprint_runs sr ON sr.id = bt.sprint_run_id
WHERE sr.period_start = DATE '2026-08-03'
  AND sr.period_end   = DATE '2026-08-09'
  AND bt.transaction_type = 'sprint_settlement'
GROUP BY bt.group_id, bt.account_type
ORDER BY bt.group_id, bt.account_type;

-- ---------------------------------------------------------------------------
-- Step 2: the fix itself. Reverses every leg the bad close wrote, zeroes the
-- run, and leaves a compensating ledger entry so the history stays auditable.
-- ---------------------------------------------------------------------------
BEGIN;

-- Lock the affected rows for the duration of the fix.
CREATE TEMP TABLE bad_runs ON COMMIT DROP AS
SELECT sr.id, sr.group_id
FROM sprint_runs sr
WHERE sr.period_start = DATE '2026-08-03'
  AND sr.period_end   = DATE '2026-08-09'
  AND sr.status = 'closed'
FOR UPDATE;

-- 2a. Roll back per-user balances by the exact amount each user was credited.
UPDATE balances b
SET current_balance = b.current_balance - reversal.total_delta
FROM (
    SELECT bt.group_id, bt.user_id, sum(bt.amount_delta) AS total_delta
    FROM balance_transactions bt
    JOIN bad_runs br ON br.id = bt.sprint_run_id
    WHERE bt.account_type = 'user'
      AND bt.transaction_type = 'sprint_settlement'
    GROUP BY bt.group_id, bt.user_id
) AS reversal
WHERE b.group_id = reversal.group_id
  AND b.user_id  = reversal.user_id;

-- 2b. Roll back the group pool leg the same way.
UPDATE groups g
SET balance = g.balance - reversal.total_delta
FROM (
    SELECT bt.group_id, sum(bt.amount_delta) AS total_delta
    FROM balance_transactions bt
    JOIN bad_runs br ON br.id = bt.sprint_run_id
    WHERE bt.account_type = 'group_pool'
      AND bt.transaction_type = 'sprint_settlement'
    GROUP BY bt.group_id
) AS reversal
WHERE g.id = reversal.group_id;

-- 2c. Post compensating ledger legs instead of deleting the originals, so the
-- double-entry history stays intact and still sums to zero per group. Each
-- reversal shares a fresh transaction_group_id per affected sprint run.
--
-- NOTE: balance_transactions has CHECK (amount_delta <> 0), so zero-valued
-- legs from the original posting are skipped here — they never existed.
WITH reversal_groups AS (
    SELECT br.id AS sprint_run_id, gen_random_uuid() AS transaction_group_id
    FROM bad_runs br
)
INSERT INTO balance_transactions (
    group_id, account_type, user_id, transaction_type, amount_delta,
    transaction_group_id, sprint_run_id, description, created_at, updated_at
)
SELECT
    bt.group_id,
    bt.account_type,
    bt.user_id,
    'sprint_settlement',
    -bt.amount_delta,
    rg.transaction_group_id,
    bt.sprint_run_id,
    'Reversal of premature 2026-08-03..2026-08-09 settlement (issue #28)',
    now(),
    now()
FROM balance_transactions bt
JOIN bad_runs br ON br.id = bt.sprint_run_id
JOIN reversal_groups rg ON rg.sprint_run_id = bt.sprint_run_id
WHERE bt.transaction_type = 'sprint_settlement'
  AND bt.amount_delta <> 0;

-- 2d. Zero the member results so the sprint report shows nothing was settled.
UPDATE sprint_member_results smr
SET planned_units      = 0,
    completed_units    = 0,
    efficiency_percent = 0,
    bonus_units        = 0,
    balance_delta      = 0,
    balance_after      = b.current_balance,
    updated_at         = now()
FROM bad_runs br
JOIN balances b ON b.group_id = br.group_id
WHERE smr.sprint_run_id = br.id
  AND b.user_id = smr.user_id;

-- 2e. Zero the run itself. Status stays CLOSED so the fixed scheduler's
-- backward walk treats the window as already settled and skips it.
UPDATE sprint_runs sr
SET total_planned_units   = 0,
    total_completed_units = 0,
    bonus_units           = 0,
    balance_delta         = 0,
    updated_at            = now()
FROM bad_runs br
WHERE sr.id = br.id;

-- ---------------------------------------------------------------------------
-- Step 3: verification. Read this output BEFORE deciding to commit.
-- ---------------------------------------------------------------------------

-- Every affected group's ledger must still sum to zero across all legs.
SELECT bt.group_id, sum(bt.amount_delta) AS must_be_zero
FROM balance_transactions bt
WHERE bt.group_id IN (SELECT group_id FROM bad_runs)
GROUP BY bt.group_id
ORDER BY bt.group_id;

-- The read-model balances must match the ledger for every affected group.
SELECT
    b.group_id,
    b.user_id,
    b.current_balance,
    coalesce(sum(bt.amount_delta), 0) AS ledger_balance,
    b.current_balance - coalesce(sum(bt.amount_delta), 0) AS must_be_zero
FROM balances b
LEFT JOIN balance_transactions bt
       ON bt.group_id = b.group_id
      AND bt.user_id  = b.user_id
      AND bt.account_type = 'user'
WHERE b.group_id IN (SELECT group_id FROM bad_runs)
GROUP BY b.group_id, b.user_id, b.current_balance
ORDER BY b.group_id, b.user_id;

-- The run is zeroed but still present and CLOSED.
SELECT id, group_id, status, total_planned_units, total_completed_units,
       bonus_units, balance_delta
FROM sprint_runs
WHERE id IN (SELECT id FROM bad_runs);

-- Change to COMMIT once the three checks above look right.
ROLLBACK;

-- ---------------------------------------------------------------------------
-- ALTERNATIVE, if you would rather the sprint be settled CORRECTLY instead of
-- written off: run steps 2a-2c only, then DELETE the sprint_runs rows (member
-- results cascade). The fixed scheduler's backward walk will find the window
-- ended and unsettled on its next 5-minute pass and re-close it using every
-- completion actually recorded through 2026-08-09 23:59 Moscow time.
--
-- Trade-off: members get a second settlement report for an old sprint, and the
-- post-deploy check "the first pass settles nothing" no longer holds. Upside:
-- the work people did in that window is actually paid out rather than voided.
-- ---------------------------------------------------------------------------
