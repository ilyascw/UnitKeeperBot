from unitkeeper_bot.recovery import (
    miniapp_unavailable,
    owner_handover_required,
    unsupported_legacy_command,
)
from unitkeeper_bot.rendering import NotificationEvent, render_notification


def test_personal_sprint_report_is_rendered_from_backend_payload() -> None:
    rendered = render_notification(
        NotificationEvent(
            id="evt-1",
            event_type="sprint_personal_report",
            recipient_user_id=10,
            payload={
                "period": "1-7 July",
                "planned_units": "12",
                "completed_units": "15",
                "balance_delta": "+3",
            },
            deep_link_path="/progress",
        ),
        app_url="https://app.example/",
    )

    assert "<b>Итоги спринта</b>" in rendered.text
    assert "15" in rendered.text
    assert rendered.miniapp_url == "https://app.example/progress?notification=evt-1"


def test_renderer_escapes_backend_supplied_text() -> None:
    rendered = render_notification(
        NotificationEvent(
            id="evt-2",
            event_type="membership_event",
            recipient_user_id=10,
            payload={"group_name": "<team>", "message": "<joined>"},
        ),
        app_url="https://app.example",
    )

    assert "&lt;team&gt;" in rendered.text
    assert "&lt;joined&gt;" in rendered.text


def test_recovery_responses_only_redirect_to_miniapp() -> None:
    replies = [miniapp_unavailable(), unsupported_legacy_command(), owner_handover_required()]

    assert [reply.miniapp_path for reply in replies] == ["/", "/", "/group"]
    assert miniapp_unavailable().retry_after_seconds == 60
