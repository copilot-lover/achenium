# Event Telemetry Specification

This document defines canonical event names, required fields, correlation ID rules, and severity mapping for:

- onboarding flows
- research runs
- scheduler ticks
- provider failures

## 1) Shared schema (required on every event)

All events must include these fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `event_name` | string | yes | Canonical snake_case event name from this spec. |
| `occurred_at` | string (ISO-8601 UTC) | yes | Event timestamp at emission time (example: `2026-04-17T12:34:56Z`). |
| `severity` | string enum | yes | One of `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`. |
| `correlation_id` | string | yes | Trace identifier tying all events in one logical workflow. |
| `component` | string | yes | Logical source such as `web`, `research_service`, `scheduler`, `polymarket`, `openai`. |
| `environment` | string | yes | Runtime env label (example: `dev`, `staging`, `prod`). |
| `version` | string | yes | App/release version or git SHA. |

### Correlation ID format and propagation

- Required format: lowercase UUIDv4 string.
- Never regenerate inside the same workflow; reuse and propagate.
- Propagation boundaries:
  - **Onboarding**: created at first user request if absent, reused through completion.
  - **Research run**: inherited from triggering request or scheduler tick; if manually created, generated at run start.
  - **Scheduler tick**: generated once per tick execution and attached to all child run events.
  - **Provider calls/failures**: always inherit parent correlation ID from caller context.

### Optional but recommended shared fields

- `request_id` (HTTP or job-run ID)
- `user_id` (if authenticated)
- `session_id`
- `market_id` / `market_slug`
- `job_name`
- `attempt`
- `duration_ms`

## 2) Event catalog

> Naming convention: `<domain>_<object>_<action>` in snake_case.

### A) Onboarding events

| Event name | Required domain fields (in addition to shared schema) | Default severity |
|---|---|---|
| `onboarding_started` | `onboarding_step`, `entrypoint` | `INFO` |
| `onboarding_profile_submitted` | `onboarding_step`, `profile_fields_present` (array), `validation_passed` (bool) | `INFO` if valid, `WARN` if invalid |
| `onboarding_market_preferences_saved` | `onboarding_step`, `preferences_count`, `selected_categories` (array) | `INFO` |
| `onboarding_completed` | `onboarding_step`, `completion_ms`, `selected_market_count` | `INFO` |
| `onboarding_abandoned` | `onboarding_step`, `abandon_reason`, `last_activity_at` | `WARN` |
| `onboarding_failed` | `onboarding_step`, `error_code`, `error_message`, `is_retryable` (bool) | `ERROR` |

### B) Research run events

| Event name | Required domain fields (in addition to shared schema) | Default severity |
|---|---|---|
| `research_run_queued` | `run_id`, `trigger_type` (`manual`/`scheduled`), `market_count` | `INFO` |
| `research_run_started` | `run_id`, `trigger_type`, `market_count`, `model` | `INFO` |
| `research_market_started` | `run_id`, `market_id`, `market_slug` | `DEBUG` |
| `research_market_completed` | `run_id`, `market_id`, `market_slug`, `confidence`, `risk_level`, `duration_ms` | `INFO` |
| `research_run_completed` | `run_id`, `markets_succeeded`, `markets_failed`, `duration_ms` | `INFO` |
| `research_run_degraded` | `run_id`, `degraded_mode` (e.g., `fallback`), `degraded_reason` | `WARN` |
| `research_run_failed` | `run_id`, `error_code`, `error_message`, `failed_stage`, `is_retryable` (bool) | `ERROR` |

### C) Scheduler tick events

| Event name | Required domain fields (in addition to shared schema) | Default severity |
|---|---|---|
| `scheduler_tick_started` | `job_name`, `schedule_type`, `scheduled_for`, `tick_id` | `INFO` |
| `scheduler_tick_skipped` | `job_name`, `tick_id`, `skip_reason` | `WARN` |
| `scheduler_tick_completed` | `job_name`, `tick_id`, `duration_ms`, `tasks_triggered` | `INFO` |
| `scheduler_tick_failed` | `job_name`, `tick_id`, `error_code`, `error_message`, `is_retryable` (bool) | `ERROR` |
| `scheduler_lag_detected` | `job_name`, `tick_id`, `lag_ms`, `scheduled_for`, `started_at` | `WARN` |

### D) Provider failure events

| Event name | Required domain fields (in addition to shared schema) | Default severity |
|---|---|---|
| `provider_request_failed` | `provider_name`, `provider_operation`, `http_status` (nullable), `provider_error_code` (nullable), `error_message`, `attempt`, `is_retryable` (bool) | `ERROR` |
| `provider_timeout` | `provider_name`, `provider_operation`, `timeout_ms`, `attempt`, `is_retryable` (bool) | `ERROR` |
| `provider_rate_limited` | `provider_name`, `provider_operation`, `http_status`, `retry_after_s` (nullable), `attempt` | `WARN` |
| `provider_auth_failed` | `provider_name`, `provider_operation`, `http_status`, `credential_scope` | `CRITICAL` |
| `provider_circuit_opened` | `provider_name`, `provider_operation`, `open_until`, `failure_rate` | `WARN` |
| `provider_fallback_used` | `provider_name`, `provider_operation`, `fallback_mode`, `reason` | `WARN` |

## 3) Severity mapping rules

When in doubt, use these rules to avoid inconsistent severity assignments:

- `DEBUG`: high-volume internal progress checkpoints with no user impact.
- `INFO`: expected lifecycle transitions (start/complete/queued).
- `WARN`: degraded but non-fatal behavior (fallback, skip, rate limit, lag, validation failure).
- `ERROR`: operation failure requiring retry/manual review but isolated in scope.
- `CRITICAL`: systemic/security-sensitive failures requiring immediate action (for example auth failures due to invalid credentials or revoked access).

### Escalation matrix

- Repeated identical `ERROR` events for same `provider_name + provider_operation` at or above 5 occurrences in 10 minutes SHOULD be escalated to `CRITICAL` alerting (event severity stays `ERROR`; alert priority escalates).
- Any `provider_auth_failed` event is immediately `CRITICAL`.
- `research_run_failed` is `ERROR`; escalate alerting priority when consecutive failures >= 3.

## 4) Correlation examples

- User starts onboarding and later triggers a manual research run:
  - all onboarding + research events share one `correlation_id` unless user starts a completely new session.
- Scheduler launches daily job:
  - one `correlation_id` at `scheduler_tick_started`, reused for spawned `research_run_*` and provider failure events.
- Provider timeout during market analysis:
  - emit `provider_timeout` with the same `correlation_id` as `research_market_started` / `research_run_started`.

## 5) Validation requirements

An event payload is considered valid only if:

1. `event_name` exists in this catalog.
2. all shared schema fields are present and non-empty (except enum-specific nullable fields explicitly marked nullable).
3. all event-specific required fields for that `event_name` are present.
4. `severity` matches the default mapping unless an explicit override rule applies.
5. `correlation_id` is present and conforms to UUIDv4 format.
