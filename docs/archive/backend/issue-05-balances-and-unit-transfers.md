# Issue 05: Balances And Unit Transfers

**Status:** Closed and archived

## Priority

`P0`

## Why

Баланс и переводы уже есть в legacy и прямо указаны в `backend/PLAN.md`, но backend этого пока не даёт.

Без этого miniapp не сможет закрыть один из основных пользовательских сценариев, а bot fallback тоже останется на старой логике.

## Goal

Перенести personal balance read model и unit transfer use case в backend services и API.

## Scope

- `GET` current personal balance.
- `GET` transfer candidates внутри текущей группы.
- `POST` transfer units между участниками группы.
- Валидации:
  - только внутри одной активной группы;
  - нельзя переводить самому себе;
  - amount > 0;
  - нельзя уйти в минус, если продукт не разрешает это явно;
  - обе стороны должны иметь active membership.
- Запись ledger transaction через `balance_transactions`.
- Определить формат user-visible transfer history, если это дешёво добавить сейчас.

## Suggested API

- `GET /balances/me`
- `GET /balances/transfer-candidates`
- `POST /balances/transfers`
- optionally `GET /balances/transactions`

## Acceptance Criteria

- backend сам проводит и валидирует переводы;
- баланс пользователя читается без legacy bot DB logic;
- все переводы отражаются в ledger;
- есть tests на insufficient funds, cross-group guard и self-transfer guard.

## Dependencies

- Лучше после Issue 02.

## Legacy References

- `UnitKeeperBot/handlers/balance.py`

## Existing Backend References

- `common/src/db/models.py` (`Balance`, `BalanceTransaction`)
