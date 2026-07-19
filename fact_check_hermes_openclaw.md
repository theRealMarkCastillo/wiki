# Fact-check: Hermes Agent & OpenClaw claims

Verified against current `main` source on GitHub, 2026-07-19.
Repos cloned at full HEAD for direct source inspection:
- `NousResearch/hermes-agent` → `/tmp/hermes-source`
- `openclaw/openclaw` → `/tmp/openclaw-source`

## Claim 1 — Hermes redactor covers API keys, private keys, JWTs, DB URLs, Telegram tokens

**Verdict: TRUE.** All five categories have explicit regex patterns in
`agent/redact.py`.

Evidence (file: `agent/redact.py` in `NousResearch/hermes-agent`):

- **API keys** — `_PREFIX_PATTERNS` at lines 71–104 covers
  `sk-…`, `sk-ant-…`, `ghp_…`, `github_pat_…`, `gho_/ghu_/ghs_/ghr_…`,
  `xapp-…`, `xox[baprs]-…`, `AIza…` (Google), `pplx-…`, `fal_…`,
  `AKIA…` (AWS), `sk_live_…` / `sk_test_…` / `rk_live_…` (Stripe),
  `SG.…` (SendGrid), `hf_…`, `r8_…`, `npm_…`, `pypi-…`,
  `dop_v1_…` / `doo_v1_…` (DigitalOcean), `am_…`,
  `sk_…` (ElevenLabs), `tvly-…`, `exa_…`, `gsk_…`, `syt_…`,
  `retaindb_…`, plus a `fc-…` Firecrawl entry, plus generic
  `_SECRET_HEADER_NAMES` for `x-api-key`, `x-goog-api-key`,
  `api-key`, `apikey`, `x-api-token`, `x-auth-token`, `x-access-token`
  (lines 205–211).
- **Private keys** — `_PRIVATE_KEY_RE` at lines 220–222:
  `-----BEGIN[A-Z ]*PRIVATE KEY-----[\s\S]*?-----END[A-Z ]*PRIVATE KEY-----`
  → replaced with literal `[REDACTED PRIVATE KEY]`.
- **JWTs** — `_JWT_RE` at lines 261–264:
  `eyJ[A-Za-z0-9_-]{10,}(?:\.[A-Za-z0-9_=-]{4,}){0,2}` (1-, 2-, or 3-part).
- **DB URLs** — `_DB_CONNSTR_RE` at lines 232–235:
  `(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s]+:[^@\s]+@`
  — strips the password segment from the connstring.
- **Telegram tokens** — `_TELEGRAM_RE` at lines 215–217:
  `(bot)?(\d{8,}):([-A-Za-z0-9_]{30,})`.

The module is wired into the rest of the codebase via
`redact_sensitive_text()` (imported from `agent/redact`) at 43+
call sites including `tools/approval.py:138` (smart-approval
observer payload), `agent/tool_executor.py`, `agent/display.py`,
`hermes_cli/session_export_md.py`, `tools/code_execution_tool.py`,
`tools/kanban_tools.py`, `tools/send_message_tool.py`,
`tui_gateway/server.py`, and platform adapters like
`plugins/platforms/telegram/adapter.py`.

## Claim 2 — Hermes has command approval modes (manual/smart)

**Verdict: TRUE.** Exact modes are `manual`, `smart`, `off`.

Evidence:

- `tools/approval.py:2436` defines `_VALID_MODES = ("manual", "smart", "off")`
  inside `_normalize_approval_mode()`. Unknown values fall back to `"manual"`.
- `tui_gateway/server.py:2784`: `_APPROVAL_MODES = frozenset({"manual", "smart", "off"})`.
- `tui_gateway/server.py:3758-3771`: status payload exposes
  `approval_mode` from `_load_approval_mode()`.
- The config key is `approvals.mode` (see
  `tui_gateway/server.py:11435`, `11444`, `11490`).
- The "smart" mode uses an auxiliary LLM to decide approve/deny —
  `tools/approval.py:123` (`_prepare_smart_approval_observer`) and
  the docstring at the top of the module ("Smart approval via
  auxiliary LLM (auto-approve low-risk commands)").

A separate **hardline blocklist** at
`tools/approval.py:417-454` (`HARDLINE_PATTERNS`) is unconditional —
even `approvals.mode=off` cannot bypass it (rm of `/`, `mkfs`,
`dd of=/dev/sd*`, fork bomb, `kill -1`, shutdown/reboot).

## Claim 3 — OpenClaw uses Docker as primary backend

**Verdict: TRUE.** Docker is the default sandbox backend.

Evidence:

- `src/agents/sandbox/config.ts:256`:
  `backend: agentSandbox?.backend?.trim() || agent?.backend?.trim() || "docker"`
  — `"docker"` is the fallback when no override is set.
- `docs/gateway/sandboxing.md:33` (Backends table):
  `| Backend | agents.defaults.sandbox.backend | docker, ssh, openshell | docker |`
  (default column reads `docker`).
- `docs/gateway/sandboxing.md:61`:
  "Docker is the default backend once sandboxing is enabled. It runs
  tools and sandbox browsers locally through the Docker daemon socket
  (`/var/run/docker.sock`); isolation comes from Docker namespaces."
- `docker-compose.yml` at the repo root ships an `openclaw-gateway`
  service image and binds `/var/run/docker.sock` for the sandbox path
  (commented by default).

## Claim 4 — OpenClaw has `logging.redactSensitive`

**Verdict: TRUE.** Validated in source code, schema, defaults, tests, docs.

Evidence:

- `src/config/defaults.ts:470-477`:
  ```
  if (logging.redactSensitive) {
      ...
      redactSensitive: "tools",
      ...
  ```
  Default value is `"tools"`.
- `src/config/schema.labels.ts:49`: `"logging.redactSensitive": "Sensitive Data Redaction Mode"`.
- `src/config/schema.help.core.ts:86`: help-text key `"logging.redactSensitive"`.
- `src/config/sessions/transcript-append-redact.test.ts:63`:
  `const config: OpenClawConfig = { logging: { redactSensitive: "tools" } };`
  — exercised in tests.
- `src/infra/errors.ts:3,71,82` and
  `src/infra/exec-approval-command-display.ts:6,102,104` import
  `redactSensitiveText` from `../logging/redact.js` and call it with
  `{ mode: "tools" }`.
- `docs/logging.md:286`:
  "`logging.redactSensitive`: `off` | `tools` (default: `tools`)".
- `docs/gateway/security/audit-checks.md:84`: an audit check
  `logging.redact_off` warns when redaction is off, fix is to set
  `logging.redactSensitive` to a non-`off` value.
- Implementation file: `src/logging/redact.ts` (with
  `src/logging/redact.test.ts`).

## Claim 5 — OpenClaw blocks paths /etc, /proc, .ssh, .aws

**Verdict: TRUE.** All four paths are explicit entries in the
blocklist that guards sandbox Docker bind mounts.

Evidence in `src/agents/sandbox/validate-sandbox-security.ts`:

- Lines 23–38 — `BLOCKED_HOST_PATHS`:
  ```
  "/etc",
  "/private/etc",     // macOS alias
  "/proc",
  "/sys",
  "/dev",
  "/root",
  "/boot",
  "/run",
  "/var/run",
  "/private/var/run",
  "/var/run/docker.sock",
  "/private/var/run/docker.sock",
  "/run/docker.sock",
  ```
- Lines 40–49 — `BLOCKED_HOME_SUBPATHS`:
  ```
  ".aws",
  ".cargo",
  ".config",
  ".docker",
  ".gnupg",
  ".netrc",
  ".npm",
  ".ssh",
  ```

Behavior: `getBlockedReasonForSourcePath()` at lines 141–155 walks
both lists; any sandbox bind whose source path equals or sits inside a
blocked host path is rejected with `formatBindBlockedError()` (line 312).
The function is invoked from `validateSandboxBind()` at line 342 and
`validateSandboxBinds()` at lines 332–343. Test coverage:

- `src/agents/sandbox/validate-sandbox-security.test.ts:66-81`
  exercises `.aws/credentials` and `.ssh/config` blocks.
- `src/agents/sandbox/validate-sandbox-security.test.ts:212`
  asserts `/covers blocked path "\/home\/tester\/.aws"/`.
- `src/agents/sandbox/validate-sandbox-security.test.ts:271`
  uses `/etc` symlink to verify parent-mount coverage detection.

Scope note: this blocklist is enforced on **sandbox container bind
mounts** specifically (it's in `validate-sandbox-security.ts`),
not on arbitrary file reads from the gateway process. Combined with
the docker default backend (claim 3) this means default OpenClaw
sandboxed runs cannot mount these paths into agent containers.

## Summary

| # | Claim                                | Verdict | Primary evidence file                                  |
|---|--------------------------------------|---------|--------------------------------------------------------|
| 1 | Hermes redactor covers 5 categories  | TRUE    | `NousResearch/hermes-agent/agent/redact.py`            |
| 2 | Hermes approval modes manual/smart   | TRUE    | `NousResearch/hermes-agent/tools/approval.py:2436`     |
| 3 | OpenClaw primary backend is Docker   | TRUE    | `openclaw/openclaw/src/agents/sandbox/config.ts:256`   |
| 4 | OpenClaw has `logging.redactSensitive`| TRUE    | `openclaw/openclaw/src/config/defaults.ts:470-477`     |
| 5 | OpenClaw blocks /etc, /proc, .ssh, .aws | TRUE  | `openclaw/openclaw/src/agents/sandbox/validate-sandbox-security.ts:23-49` |