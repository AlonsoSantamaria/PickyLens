# VESTA deployment

Canonical URL: https://pickylens.neovantia.live. Same-origin browser API; no separate API domain.

Installed release df01953 lives in /srv/neovantia/apps/pickylens with an isolated Python 3.12 virtual environment. systemd pickylens.service runs as pickylens on loopback port 8062, one worker. Apache uses the existing wildcard TLS certificate and redirects HTTP to HTTPS. The authoritative DNS A record points to VESTA.

## Configuration and persistence

EnvironmentFile=/etc/neovantia/secrets/pickylens/runtime.env is root-owned mode 0600. PICKYLENS_ENV=production disables repository dotenv loading. OPENAI_API_KEY, PICKYLENS_MODEL and PICKYLENS_REASONING_EFFORT remain external. Current model configuration: gpt-5.6-sol / low.

SQLite files reside under /var/lib/neovantia/pickylens, owned by the service user. Preserve both interactions.sqlite3 and judge-access.sqlite3 across releases. Never replace the access ledger to reset spending. Back up live SQLite using its backup API or stop the service before copying databases.

Current limits: PICKYLENS_GLOBAL_OPERATIONS=200, PICKYLENS_GLOBAL_TOKEN_BUDGET=2000000, PICKYLENS_OPERATIONS_PER_MINUTE=6. Operator-issued passes default to 30 operations / 72 hours. Both call and token capacity must permit every call; unknown usage retains its reservation. No billing system is implied.

## Verification and operation

External HTTPS verification passed: access, authenticated workspace and History 200; invalid pass 401; exhausted pass 429; Secure HttpOnly cookie; no public Replay/test labels. Zero provider calls were added. Deployed inference was not repeated after the authorized local live acceptance.

Inspect with systemctl status pickylens and apache2ctl configtest. Restart pickylens only after updating the release and checking dependencies. Roll back to a known release while preserving external configuration and both databases; do not reset the ledger. The existing host resolver briefly cached the new hostname negatively; public recursive DNS and external HTTPS succeeded. Shared DNS settings were not changed.

The operator pass is protected at /etc/neovantia/secrets/pickylens/judge-pass.txt. Share through an appropriate private channel, never Git/chat logs/screenshots. It expires; issue a fresh bounded pass for judging when needed.

The release package work/pickylens-browser-v0.1.zip targets this HTTPS origin. Extract and load unpacked, then use the normal toolbar popup to configure the bounded pass. The source extension remains localhost-only for development.

verify_deployed.py under devtools performs external non-inference access checks with operator SSH access; it creates an exhausted test pass and keeps credentials in memory. verify_http.py is an on-server alternative requiring working server DNS. Neither is a model validation script.


## Anonymous Web correction

Public Web access now opens directly without a pass. Extension APIs alone require Judge Pass. Anonymous defaults are 12 operations/24-hour session, 6/minute per session and IP, and 30/IP/rolling day; the existing global call/token ledger is shared and preserved. The service auto-migrates the access schema, retaining existing passes and reservations. Session History is isolated; prior unowned records remain stored and hidden. Apache supplies client addresses to the loopback-only trusted Uvicorn proxy. Do not expose port 8062 publicly or trust arbitrary forwarded headers.


## Devpost referral allowance — 2026-10-24

Preferred judging URL: https://pickylens.neovantia.live/?ref=devpost. The normal URL still works without credentials. A new anonymous session arriving via GET /?ref=devpost is tagged as Devpost traffic: 30 calls/session over 72 hours, 6/minute per session and IP, 60/IP over rolling 72 hours. Normal defaults remain 12/session over 24 hours, 6/minute, 30/IP over rolling 24 hours.

Configuration: PICKYLENS_DEVPOST_OPERATIONS, PICKYLENS_DEVPOST_HOURS, PICKYLENS_DEVPOST_PER_MINUTE, PICKYLENS_DEVPOST_IP_OPERATIONS, PICKYLENS_DEVPOST_IP_HOURS; normal IP window uses PICKYLENS_ANONYMOUS_IP_HOURS. Supply process/systemd environment values. Existing valid sessions are never upgraded/reset by a query parameter; classification, used count and absolute expiry persist. Refresh does not renew the cookie. Clearing cookies still encounters the shared IP usage history. IP windows count both anonymous classes rather than independent referral buckets.

The referral is public traffic classification, not authentication. Anonymous tokens never authorize extension routes. Judge Pass expiration/limits remain unchanged. Both anonymous classes and extension calls share the persistent 200-call / 2,000,000-token breakers and fail closed. No UI branding or model behavior changes.

Verification: 104 deterministic tests pass, worker protocol and whitespace checks pass; zero inference calls. This is the explicitly authorized shipping configuration exception, not reopened product development.

## UX polish deployment — 2026-10-25 11:38 CST (UTC-06:00)

Deployed `b107b17` from `main`: UX bounded-scroll + Markdown rendering polish. Previous production commit: `a145513`; rollback archive preserved at `/srv/neovantia/apps/pickylens/rollback-a145513-before-b107b17.tar`. Only PickyLens was restarted; configuration, secrets, SQLite data, allowances, Judge Pass, provider routing and service topology were preserved.

Health: service active; loopback and public HTTPS return 200; deployed app matches the commit (archive line endings normalized). Browser smoke passed at desktop and 390px: prompt/answer internal scrolling, headings, emphasis, lists, rendered table, table-only horizontal overflow, summary counters outside scrolling requirement lists, and expanded evidence. Public landing page checked directly; populated-state rendering used production HTML/HTTPS assets in an isolated deterministic harness without production data edits. Zero provider calls; no production-only issue observed.

## PRE incident — 2026-10-25 17:56 UTC

Production `b107b17`: live PRE was rejected by the configured OpenAI endpoint (`api.openai.com`) with HTTP 429, type `insufficient_quota`, code `credit_balance_exhausted`. Runtime configuration was present: production environment, OpenAI provider, `gpt-5.6-sol`, reasoning `low`, 120-second timeout, key present (never logged). UX/Markdown changes did not touch the provider path. No application/configuration rollback or code fix was warranted; the provider account credit balance must be restored by its owner.

One authorized diagnostic retry of the saved failed PRE made exactly one provider request, rejected in 1,139.92 ms; no response/token usage was returned. The conservative 300,000-token reservation remains charged, not represented as actual usage. Ledger afterward: 10 reservations / 1,228,493 reserved-or-settled tokens, below the unchanged 200-call / 2,000,000-token breakers. Failure and retry events persisted correctly, with no automatic/duplicate call; successful live PRE verification remains blocked pending provider credit restoration and fresh call authorization.

Regression checks: 104 Python tests, 4 Node tests (Markdown and worker protocol), JavaScript syntax and whitespace checks passed. Service active and HTTPS 200. No UI files or runtime settings changed; rollback `a145513` remains at `/srv/neovantia/apps/pickylens/rollback-a145513-before-b107b17.tar`.

## PRE validation handling — 2026-10-26

A saved live PRE failed with SDK ValidationError after 47.34 seconds; the old parse-before-record sequence discarded response status/usage and validation detail. The provider now uses the pinned SDK strict schema unchanged, records response metadata before typed parsing, and logs only validation error codes and allowlisted field paths (no prompts, output values or credentials). Incomplete/refused results still fail closed; no automatic retry or schema relaxation. This corrects handling/observability, not a claim that the original unrecorded validation defect is resolved. Verification: 108 Python tests and 4 Node/worker tests passed; no live calls. A single production PRE retry remains subject to fresh authorization. UX, access controls, model and persistence are unchanged. Rollback: b107b17 app archive, plus the original a145513 archive.

Production PRE verification — 2026-10-26 16:57 UTC: user authorized one retry; activated the normal Retry failed step control in the existing Chrome interaction. PRE succeeded on deployed `896bacf`, saved as Recovered after retry (revision 4), with Amber readiness and 9 requirements visible. Exactly one OpenAI `gpt-5.6-sol` call, reasoning low: 16,564.91 ms, 499 input + 1,193 output = 1,692 total tokens; 92 reasoning tokens included in output. No answer/follow-up or further calls. Successful retry confirms recovery for this interaction; the exact original validation field was not recorded and cannot be retrospectively established.
