# OpenClaw Security Features Research

**Source:** GitHub repo [openclaw/openclaw](https://github.com/openclaw/openclaw) (main branch)
**Docs:** https://docs.openclaw.ai
**Stars:** ~383k
**Last verified:** July 19, 2026

---

## 1. Secret Redaction / Output Filtering

**YES** — OpenClaw has built-in secret redaction for logs and transcripts.

### Mechanism: `logging.redactSensitive` and `logging.redactPatterns`

From the [logging docs](https://docs.openclaw.ai/gateway/logging#redaction):

> "OpenClaw masks sensitive tokens before log or transcript output leaves the process. This redaction policy applies at console, file-log, OTLP log-record, and session transcript text sinks, so matching secret values are masked before JSONL lines or messages are written to disk."
>
> - `logging.redactSensitive`: `off` | `tools` (default: `tools`)
> - `logging.redactPatterns`: array of regex strings (overrides defaults)
>   - Matches are masked keeping the first 6 + last 4 chars (values >= 18 chars); shorter values become `***`.
>   - Defaults cover common key assignments, CLI flags, JSON fields, bearer headers, PEM blocks, popular vendor token prefixes, and payment credential field names.

Additionally, some surfaces **always** redact regardless of the setting:

> "Some safety boundaries always redact regardless of `logging.redactSensitive`: Control UI tool-call events, `sessions_history` tool output, diagnostics support exports, provider error observations, exec approval command display, and Gateway WebSocket protocol logs."

### External content wrapping (indirect prompt injection mitigation)

From the [threat model](https://docs.openclaw.ai/security/THREAT-MODEL-ATLAS):

> **T-EXEC-002: Indirect prompt injection** — mitigations include "Content wrapping with random-boundary XML-style markers, homoglyph/special-token normalization, and a security notice."

> **T-EVADE-002: Content wrapper escape** — mitigations: "Random-boundary XML-style markers + security notice, plus homoglyph/whitespace-variant marker-spoof detection."

### Security notice injection for fetched content

From the threat model's data flow diagram (Trust Boundary 4: External Content):
> "External content wrapping (random-boundary XML tags)" and "Security notice injection"

### No classical "output filtering" (LLM response scanning)

OpenClaw does **not** filter LLM output for disallowed content before sending it to channels. The threat model acknowledges this gap:

> **T-IMPACT-003: Reputation damage** — "Attacker causes the agent to send harmful/offensive content" ... Current mitigations: "LLM provider content policies" ... Residual risk: "Medium - provider filters are imperfect" ... Recommendations: "Output filtering layer, user controls"

**Summary:** Secret redaction (log/transcript sanitization) is a mature, built-in feature with configurable regex patterns. However, there is no agent-side output content filtering for LLM responses — that's acknowledged as a gap.

---

## 2. Docker Backend / Sandboxed Execution

**YES** — OpenClaw has a **comprehensive sandboxing system** with Docker as the default backend.

### Sandboxing architecture

From the [sandboxing docs](https://docs.openclaw.ai/gateway/sandboxing):

> "OpenClaw can run tool execution inside a sandbox backend to reduce blast radius. Sandboxing is off by default and controlled by `agents.defaults.sandbox` (global) or `agents.list[].sandbox` (per-agent). The Gateway process always stays on the host; only tool execution moves into the sandbox when enabled."
>
> "This is not a perfect security boundary, but it materially limits filesystem and process access when the model does something dumb."

### Three sandbox backends

| Backend | Description |
|---------|-------------|
| **Docker** (default) | Local containers with namespaced isolation |
| **SSH** | Remote machine via SSH |
| **OpenShell** | Managed remote sandbox with optional two-way sync |

### Modes

| Mode | Behavior |
|------|----------|
| `off` (default) | No sandboxing |
| `non-main` | Sandbox every session except the agent's main session |
| `all` | Every session runs in a sandbox |

### Docker security defaults

From the sandboxing docs:

> "Defaults: `network: "none"` (no egress), `readOnlyRoot: true`, `capDrop: ["ALL"]`, image `openclaw-sandbox:bookworm-slim`."

Docker-specific security controls:
- `network: "none"` — no egress by default
- `network: "host"` is blocked
- `network: "container:<id>"` is blocked by default (namespace join bypass risk)
- Break-glass override: `dangerouslyAllowContainerNamespaceJoin: true`
- `readOnlyRoot: true` — read-only root filesystem
- `capDrop: ["ALL"]` — no Linux capabilities
- Bind source validation: blocks dangerous sources (system paths, Docker socket directories, credential roots like `~/.aws`, `~/.ssh`, etc.)
- Reserved container mount targets (`/workspace`, `/agent`) are blocked from shadowing

### Workspace access levels

| Value | Behavior |
|-------|----------|
| `none` (default) | Isolated sandbox workspace |
| `ro` | Mounts workspace read-only |
| `rw` | Mounts workspace read/write |

### Sandbox browser

- Uses dedicated Docker network (`openclaw-sandbox-browser`)
- noVNC observer access is password-protected by default
- CDP ingress restricted via CIDR allowlist

### Tool policy within sandbox

From the README:
> "Typical sandbox default: allow `bash`, `process`, `read`, `write`, `edit`, `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`; deny `browser`, `canvas`, `nodes`, `cron`, `discord`, `gateway`."

---

## 3. Command Approval Gates

**YES** — OpenClaw has a comprehensive exec approval system.

### Exec approval mechanism

From the [threat model](https://docs.openclaw.ai/security/THREAT-MODEL-ATLAS):

> **T-EXEC-003: Tool argument injection** — Mitigations: "Exec approvals for dangerous commands"
>
> **T-EXEC-004: Exec approval bypass** — Mitigations: "Allowlist + ask mode, plus command normalization (dispatch-wrapper unwrapping, inline-eval detection, shell-chain analysis)"

### Configurable exec security

From the security docs and README:
- `tools.exec.security`: Sets approval posture (e.g., `"full"`, `"deny"`)
- `tools.exec.ask`: `"off"` | `"always"` — prompts for confirmation
- `tools.elevated`: Escape hatch to run `exec` outside the sandbox

From the formal verification docs:
> "**Claim:** `exec host=node` requires (a) a node command allowlist plus declared commands and (b) live approval when configured; approvals are tokenized to prevent replay, in the model."

### Hardened baseline

From the security docs:
> ```json5
> tools: {
>   exec: { security: "deny", ask: "always" },
>   elevated: { enabled: false },
> },
> ```

### Key security file

From the threat model appendix:
> `src/infra/exec-approvals.ts` — "Command approval logic" — **Critical** risk level

---

## 4. User Allowlists / Authentication

**YES** — OpenClaw has a multi-layered authentication and allowlist system.

### Gateway authentication

From the [configuration docs](https://docs.openclaw.ai/gateway/configuration):

- `gateway.auth.mode`: `"token"` | `"password"` | `"trusted-proxy"` | `"device-auth"`
- Token/password authentication for gateway API access
- Trusted proxy auth for SSO/OIDC setups

From the security docs:
> "`gateway.auth` (token/password/trusted-proxy/device auth) — Authenticates callers to gateway APIs"

### DM Access Policies (per-channel)

| Policy | Behavior |
|--------|----------|
| `pairing` (default) | Unknown senders get a pairing code; bot ignores them until approved. Codes expire after 1 hour; pending requests capped at 3 per channel |
| `allowlist` | Unknown senders blocked, no pairing handshake |
| `open` | Anyone can DM (public). Requires `"*"` in allowlist |
| `disabled` | Inbound DMs ignored entirely |

### Two-layer allowlists

1. **DM allowlist** (`allowFrom` / `channels.discord.allowFrom` / `channels.slack.allowFrom`): who can DM the bot
2. **Group allowlist** (channel-specific): which groups/channels/guilds the bot accepts

From the security docs:
> "Check order: `groupPolicy`/group allowlists first, then mention/reply activation."

### Group policies

- `groupPolicy`: per-group access control
- `groupAllowFrom`: restrict who can trigger the bot inside a group session
- `requireMention`: bot only responds when @mentioned
- Discord: `channels.discord.guilds` allowlist
- Slack: `channels.slack.channels` allowlist

### Pairing system

From the README:
> "**DM pairing** (`dmPolicy="pairing"`): unknown senders receive a short pairing code and the bot does not process their message."
> "Approve with: `openclaw pairing approve <channel> <code>` (then the sender is added to a local allowlist store)."

From the formal verification docs:
> "**Claim:** pairing requests respect TTL and pending-request caps." — Formally verified with TLA+.

### Ingress gating

From the formal verification docs:
> "**Claim:** in group contexts requiring mention, an unauthorized control command cannot bypass mention gating." — Formally verified.

### SSRF protection (execution-level access control)

From the threat model:
> **T-EXFIL-001: Data theft via web_fetch** — "Current mitigations: SSRF blocking for internal/private networks (DNS pinning + IP blocking)"

---

## 5. Summary: Security Layers 2, 3, and 4

### Layer 2: Sandboxed Execution (Docker Backend + Sandboxing)

**Fully implemented.** OpenClaw provides a sophisticated sandboxing system with three backends (Docker, SSH, OpenShell). Docker is the default with conservative security defaults: no network egress, read-only root, all capabilities dropped. Sandboxing can be configured per-mode (`off`, `non-main`, `all`), per-scope (`agent`, `session`, `shared`), and per-agent. The sandbox browser uses an isolated Docker network with password-protected access. However, sandboxing is **off by default**, and even when on, skills downloaded from ClawHub still run with agent privileges (no skill execution sandboxing — identified as a gap in the threat model, T-PERSIST-001).

### Layer 3: Command Approval Gates

**Fully implemented.** OpenClaw has configurable exec approval gates with allowlist + ask modes. The system includes command normalization to detect obfuscation attempts (dispatch-wrapper unwrapping, inline-eval detection, shell-chain analysis). Approvals are tokenized to prevent replay. The formal verifiation provides a machine-checked model for the exec pipeline including approvals. However, by default in single-operator mode, `security="full"` with `ask="off"` means **no approval prompts** — the default is permissive, requiring explicit hardening. The threat model notes T-EXEC-004 (exec approval bypass) as "High" residual risk despite command normalization.

### Layer 4: User Allowlists & Authentication

**Fully implemented.** OpenClaw implements a comprehensive, layered access control system:
1. **Gateway authentication** (token/password/trusted-proxy) authenticates API callers
2. **Per-channel DM policies** (pairing/allowlist/open/disabled) gate who can message the bot
3. **Two-layer allowlists** (DM-level and group-level) provide fine-grained access control
4. **Pairing system** with 1-hour TTL and per-channel pending caps
5. **Group mention gating** (`requireMention`) for group channels
6. **Node pairing** with optional SSH key verification and CIDR-based auto-approval
7. **TLA+ formal verification** of pairing, ingress gating, and routing isolation models

The system defaults to `dmPolicy="pairing"` (pairing code required for unknown senders), which provides a reasonable default. The formal verification of pairing and ingress gating is a notable security engineering investment.

### Overall Assessment

OpenClaw has **Layers 2, 3, and 4 implemented** (sandboxing, exec approvals, and authentication/allowlists), but all three require explicit configuration — the defaults are permissive (sandbox off, exec approvals off in single-user mode). The project maintains a formal threat model (MITRE ATLAS), supporting security docs, a formal verification suite (TLA+/TLC), and a `openclaw security audit` command. Notable gaps include no per-sender rate limiting, no skill execution sandboxing, no URL allowlisting for web_fetch, and no output content filtering for LLM responses.

---

**Sources:**
- https://github.com/openclaw/openclaw
- https://docs.openclaw.ai/gateway/security
- https://docs.openclaw.ai/gateway/sandboxing
- https://docs.openclaw.ai/gateway/logging#redaction
- https://docs.openclaw.ai/security/THREAT-MODEL-ATLAS
- https://docs.openclaw.ai/security/formal-verification
- https://docs.openclaw.ai/gateway/authentication
- https://docs.openclaw.ai/gateway/security/exposure-runbook
