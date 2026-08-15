## Purpose

Defines when a group's sprint window is considered finished and eligible for settlement, which window a scheduled or manual close settles, and how each group's own timezone determines those boundaries. Settlement arithmetic itself is out of scope; this capability governs only timing and window selection.

## ADDED Requirements

### Requirement: Sprint windows are bounded by group-local time

The system SHALL derive sprint window boundaries from the group's stored IANA timezone. A window covering `period_start..period_end` SHALL begin at `00:00` local time on `period_start` and end at `00:00` local time on the day after `period_end`. Every query for logs belonging to a window SHALL use those same bounds.

#### Scenario: Window bounds follow a non-UTC group

- **WHEN** a group in `Europe/Moscow` has a window ending `2026-08-16`
- **THEN** the window covers `2026-08-10T00:00+03:00` up to but excluding `2026-08-17T00:00+03:00`
- **AND** completions recorded at `2026-08-16T23:30+03:00` count toward that window

#### Scenario: Boundary instant belongs to the next window

- **WHEN** a completion is recorded at exactly `00:00:00` local time on the day after `period_end`
- **THEN** it counts toward the following window, not the one that just ended

#### Scenario: The end of a sprint is reported in group-local terms

- **WHEN** a client requests the current group card
- **THEN** the reported sprint end instant is `00:00` local time on the day after `period_end`, expressed as a timezone-aware value

### Requirement: A sprint closes only after its window has fully ended

The system SHALL settle a window only once the current instant is at or after that window's end boundary in group-local time. A window that is still running SHALL NOT be settled, whether closure is triggered by the scheduler or manually.

#### Scenario: No settlement during the final day

- **WHEN** the scheduler runs at `2026-08-16T00:05Z`, while the `Europe/Moscow` group's window `2026-08-10..2026-08-16` is still in its final local day
- **THEN** no sprint is closed for that group
- **AND** members can still record completions for that window

#### Scenario: Settlement once the final day has passed

- **WHEN** the scheduler runs at or after `2026-08-16T21:00Z` (`2026-08-17T00:00+03:00`)
- **THEN** the window `2026-08-10..2026-08-16` is settled
- **AND** the settlement counts every completion made through the end of `2026-08-16` local time

#### Scenario: Manual close of a running sprint is refused

- **WHEN** a caller requests closure of a group whose window has not yet ended locally
- **THEN** the request is rejected with a business-rule error
- **AND** no balances, sprint run records, or log statuses change

### Requirement: Closure targets ended, unsettled windows

The system SHALL identify the windows that have ended and have no settled record, rather than assuming the currently running window. When more than one such window exists, the system SHALL settle them in chronological order, oldest first, each with the completions belonging to its own bounds.

#### Scenario: Catch-up after scheduler downtime

- **WHEN** the scheduler has been unavailable across two whole sprint windows and starts again
- **THEN** both windows are settled, oldest first
- **AND** each settlement reflects only the completions recorded inside its own window

#### Scenario: Already-settled windows are left alone

- **WHEN** a closure pass encounters a window that already has a settled record
- **THEN** that window is skipped
- **AND** no balances are adjusted a second time

#### Scenario: Repeated passes are safe

- **WHEN** closure runs repeatedly while no new window has ended
- **THEN** the first pass settles the eligible window and later passes settle nothing

### Requirement: Pending completions are resolved against their own window

When settling a window, the system SHALL auto-reject only the pending completions whose recorded time falls inside that window's bounds. Pending completions belonging to a later window SHALL remain pending and SHALL stay eligible for approval.

#### Scenario: Stale marks from the settled window are rejected

- **WHEN** a window is settled while it still holds pending completions recorded inside it
- **THEN** those completions are rejected by the system
- **AND** they cannot later be approved into another window's totals

#### Scenario: Marks from the next window survive

- **WHEN** a delayed catch-up settles an earlier window, and completions were recorded during the window that followed it
- **THEN** those later completions remain pending
- **AND** they can still be approved and counted toward their own window

### Requirement: Group timezone is a valid IANA zone

The system SHALL reject a group timezone that is not a recognized IANA identifier when a group is created or its timezone is set. When a stored timezone cannot be resolved at closure time, the system SHALL fall back to UTC for that group, record a warning identifying the group, and continue processing other groups.

#### Scenario: Unrecognized timezone is refused on input

- **WHEN** a group is created with a timezone that is not a known IANA identifier
- **THEN** the request is rejected with a validation error
- **AND** no group is created

#### Scenario: A broken stored value does not stall closure

- **WHEN** a closure pass encounters a group whose stored timezone cannot be resolved
- **THEN** that group's window is evaluated in UTC
- **AND** a warning identifying the group is recorded
- **AND** the remaining groups are processed normally
