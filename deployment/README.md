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
