# Bot Recovery Operations

The bot remains a delivery and routing surface. It must not reconstruct group,
task, balance, or sprint flows while the Mini App is unavailable.

## User-facing fallback

- `/start`, unsupported legacy commands, and temporary Mini App failures return a
  concise redirect to the Mini App.
- The only safe fallback action is reopening the Mini App. The bot must not
  accept task CRUD, transfers, or sprint close commands.
- Owner departure uses a prompt that routes to `/group`; owner handover stays a
  backend-authorized Mini App flow.

## Operator recovery

- Inspect backend outbox events by event id and correlation id before retrying.
- Retry only pending or failed deliveries through the backend delivery worker.
  Do not manually resend a payload from the bot process.
- Dead-letter events require an explicit backend replay after the underlying
  Telegram error is resolved; keep the original event id for auditability.
- If the Mini App is unavailable, pause deep-link campaign sends and retain
  events in the backend outbox. The bot may send the standard availability
  notice but must not substitute product workflows.
