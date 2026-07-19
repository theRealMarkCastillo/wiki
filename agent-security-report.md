# Agent Harness Security Features — Verified Report

> Fact-checking claims from the "4 Layers of AI Agent Security" blog post.
> Researched: July 19, 2026 | Sources: GitHub source code, official docs, READMEs.

---

## 1. Claude Code CLI (Anthropic)

| Feature | Claimed | Verified | Evidence |
|---|---|---|---|
| **Secret redaction** | ❌ No | ✅ **Confirmed: No** | No built-in output scrubber found. Credentials stored in macOS Keychain / file permissions. Permission system blocks access to sensitive files. |
| **Docker/sandbox backend** | ❌ No | ✅ **Confirmed: Yes** (OS sandbox) | Built-in Bash sandbox using **Seatbelt** (macOS) or **bubblewrap+socat** (Linux/WSL2). Not Docker — OS-level namespace/process isolation. Cloud execution uses isolated VMs. Dev containers also supported. |
| **Runs on host** | ✅ Yes | ✅ **Confirmed: Yes** | Runs on host with optional OS-level sandbox (opt-in via `/sandbox`). |

### Layer 3 Defenses (Command/Execution)
- **Permission-based architecture**: read-only commands (`ls`, `cat`, `git status`) auto-approved; write/edit/execute requires explicit approval
- **Permission modes**: `default` (prompt on first use), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`
- **Wildcard allow/deny rules** per tool (`Bash(npm run *)`, `Bash(git commit *)`, `Read(./.env)`)
- **Compound command detection**: a rule `Bash(safe-cmd *)` won't match `safe-cmd && other-cmd`
- **Process wrapper stripping**: `timeout`, `time`, `nice`, `nohup`, `stdbuf` stripped before matching rules
- **Command injection detection**: suspicious commands require manual approval even if allowlisted
- **Network command approval**: `curl`, `wget` not auto-approved by default
- **Fail-closed matching**: unmatched commands default to manual approval

### Layer 4 Defenses (System/Policy)
- **Working directory boundary**: can only write to starting directory and subfolders without explicit permission
- **Isolated context windows**: web fetch uses separate context window
- **Trust verification**: first-time codebase runs and new MCP servers require verification
- **Secure credential storage**: macOS Keychain, file permissions on Windows/Linux
- **SOC 2 Type 2 / ISO 27001** certified (via Anthropic)
- **Audit logging**: OpenTelemetry metrics
- **Output sanitization**: None at the harness level — relies on model safety (Layer 1)

**Blog verdict**: Mostly accurate. Sandboxing exists but is OS-level, not Docker. Secret redaction truly absent.

---

## 2. Codex CLI (OpenAI)

| Feature | Claimed | Verified | Evidence |
|---|---|---|---|
| **Secret redaction** | ❌ No | 🔴 **FALSE** — **YES, exists** | `codex-rs/secrets/src/sanitizer.rs` has `redact_secrets()` regex-based output scrubber: OpenAI keys (`sk-...`), AWS access keys, Bearer tokens, credential assignments (`api_key`, `token`, `secret`, `password`). Used in `thread_resume_redaction.rs`. |
| **Docker/sandbox backend** | ❌ No | 🔴 **FALSE** — **YES, extensive** | `linux-sandbox` (bubblewrap + Landlock LSM), `windows-sandbox-rs` (Windows Sandbox, WFP firewall, ACLs, desktop isolation), `sandboxing/` crate (Seatbelt, policy transforms). Sandbox modes: `danger-full-access`, `read-only`, `workspace-write`. Exec-server has `fs_sandbox.rs` + `process_sandbox.rs`. `.devcontainer/Dockerfile` + `.devcontainer/Dockerfile.secure`. |
| **Runs on host** | ✅ Yes | ⚠️ **Partially** | Runs on host BY DEFAULT but sandboxing is a core feature. CLI has `--sandbox` flag, config-based sandbox modes. |

### Layer 3 Defenses (Command/Execution)
- **Sandbox modes**: `danger-full-access` (no restrictions), `read-only`, `workspace-write` (can only write to workspace)
- **Approval policies**: `never`, `on-request`, `always`
- **Execution policy**: config-based rules (`docs/execpolicy.md`)
- **Windows Sandbox**: separate desktop, firewall (WFP), ACL-based deny-read, elevated process isolation
- **Network controls**: per-domain allow/block in sandbox
- **Auto-review**: eligible approval requests can go to a reviewer agent

### Layer 4 Defenses (System/Policy)
- **Secret redaction on output**: YES — regex-based sanitizer covers OpenAI keys, AWS keys, Bearer tokens, credential patterns
- **Keyring-based secret storage**: `codex-keyring-store` for credential management
- **Managed settings**: `allow_managed_hooks_only` for admin-enforced config
- **Organizational policies**: sandboxing and approvals can be organization-mandated
- **Dockerfile.secure**: hardened container build
- **SECURITY.md**: published security policy

**Blog verdict**: Significantly inaccurate. Codex CLI has both explicit output secret redaction AND extensive sandbox infrastructure (Linux, Windows, macOS Seatbelt). This is the most security-feature-rich harness of all five.

---

## 3. OpenClaw

| Feature | Claimed | Verified | Evidence |
|---|---|---|---|
| **Secret redaction** | ❌ No | ⚠️ **Partially** — `logging.redactSensitive: "tools"` setting exists. Output sanitizer strips leaked `<tool_call>`, `<function_calls>`, chat-template tokens. No general secret pattern-based redactor. |
| **Docker/sandbox backend** | ❌ No | 🔴 **FALSE** — **YES, Docker is primary backend** | Docker is the default sandbox backend. Also supports SSH and OpenShell backends. Sandbox modes: `off`, `non-main` (sandbox everything except main session), `all`. Scope: `agent`, `session`, `shared`. Network: `none` by default. |
| **Runs on host** | ✅ Yes | ⚠️ **Partially** | Main session runs on host by default. Non-main/group sessions can sandbox. Tool execution moves to sandbox; Gateway stays on host. |

### Layer 3 Defenses (Command/Execution)
- **DM pairing** (`dmPolicy="pairing"`): unknown senders get pairing code; ignored until approved (codes expire 1hr)
- **DM isolation**: `session.dmScope` — `main`, `per-channel-peer`, `per-account-channel-peer`, `per-peer`
- **Allowlists**: DM allowlist (`allowFrom`) + group allowlists + mention gating
- **Tool profiles**: `messaging`, `minimal`, `full` — control which tools are available
- **Exec security levels**: `full` (no approval), `deny`, with `ask=always` option
- **Elevated mode**: some tools can bypass sandbox explicitly
- **Browser sandboxing**: Docker-backed browser isolation with CDP access control
- **Context visibility**: controls what supplemental context reaches the model

### Layer 4 Defenses (System/Policy)
- **`openclaw security audit`**: comprehensive audit with `--fix`, `--deep`, `--json` modes
- **Redaction**: `logging.redactSensitive: "tools"` — redacts tool args from logs
- **Output sanitizer**: strips leaked `<tool_call>`, `<function_calls>`, `<system-reminder>` from user-visible replies
- **Token sanitization**: strips chat-template special tokens from untrusted content
- **Blocked sandbox paths**: `/etc`, `/proc`, `/sys`, `/dev`, `/root`, `/boot`, Docker socket paths, credential subpaths (`.aws`, `.ssh`, `.config`, etc.)
- **Gateway auth**: token/password/trusted-proxy/device auth modes
- **Node pairing**: SSH-verified device enrollment
- **Tailscale integration**: Serve/Funnel awareness
- **Credential files**: `600` permissions on state/config files

**Blog verdict**: Inaccurate. OpenClaw has Docker sandboxing as its core isolation mechanism, redaction for tool output in logs, and an extensive security audit framework. The main session runs on host, but sandboxing is a first-class feature.

---

## 4. AutoGPT (Classic)

| Feature | Claimed | Verified | Evidence |
|---|---|---|---|
| **Secret redaction** | ❌ No | ✅ **Confirmed: No** | No output redaction system. `.env` file handling exists but no runtime secret scrubber. |
| **Docker/sandbox backend** | ❌ No | ✅ **Confirmed: No** (for Classic) | Workspace sandboxing (filesystem-level via `permissions.yaml`), not Docker containerization. Self-hosting uses Docker for deployment, not sandbox enforcement. Modern Platform is hosted/managed. |
| **Runs on host** | ✅ Yes | ✅ **Confirmed: Yes** | Classic runs on host with filesystem-level workspace restrictions. |

### Layer 3 Defenses (Command/Execution)
- **Layered permission system** with pattern matching:
  - Workspace-level: `.autogpt/autogpt.yaml`
  - Agent-level: `.autogpt/agents/{id}/permissions.yaml`
- **Allow/deny with globs**: `read_file({workspace}/**)`, `execute_shell(sudo:*)`
- **First-match-wins**: Agent deny → Workspace deny → Agent allow → Workspace allow → Prompt user
- **Interactive approval**: Once / Agent-scope / Workspace-scope / Deny
- **Denied by default**: `.env`, `.key`, `.pem` files; `rm -rf`, `sudo` commands; operations outside workspace

### Layer 4 Defenses (System/Policy)
- **Workspace sandboxing**: agent files restricted to `workspace/` subdirectory
- **Security notice**: Known vulnerabilities; "educational purposes only"
- No modern secret redaction, container sandboxing, or credential management
- Unsupported project — dependencies not updated

**Blog verdict**: Accurate. Classic AutoGPT has no secret redaction, no Docker sandbox, and runs on host. The permission system is filesystem-pattern-based, not container-level isolation.

---

## 5. Cline

| Feature | Claimed | Verified | Evidence |
|---|---|---|---|
| **Secret redaction** | ❌ No | ⚠️ **Partially** — `api-secrets-parser.mjs` exists in VS Code extension for API key handling. SDK has plugin sandboxing. No general-purpose output redactor. |
| **Docker/sandbox backend** | ❌ No | ✅ **Confirmed: No Docker** | Has subprocess sandboxing in SDK (`subprocess-sandbox.ts`, `plugin-sandbox.ts`) but no Docker-based sandbox. Plugin sandbox is process-level, not container-level. |
| **Runs on host** | ✅ Yes | ✅ **Confirmed: Yes** | Runs directly on host. Plugin sandboxing is for SDK plugins, not general execution. |

### Layer 3 Defenses (Command/Execution)
- **Plan/Act modes**: toggle between planning-only and execution modes
- **Tool approval system**: every tool call requires approval by default
- **`--yolo` mode**: skips all approval prompts (opt-in, intended for CI/CD)
- **`--auto-approve` flag**: controls whether tool calls require approval
- **`.clinerules`**: project-specific rules for coding standards and deployment
- **Checkpoints**: `/undo` to rewind workspace state
- **MCP server management**: interactive MCP server configuration

### Layer 4 Defenses (System/Policy)
- **OAuth support**: for Cline, ChatGPT Subscription, and OCA
- **API key authentication**: provider-based auth
- **SECURITY.md**: published in repo
- **Plugin sandbox**: process-level isolation for SDK plugins
- **No general secret redaction, no Docker sandbox, no credential vault**

**Blog verdict**: Largely accurate. No Docker backend, no comprehensive secret redactor. Runs on host. Has approval gates and sandbox for SDK plugins specifically.

---

## 6. Aider

| Feature | Claimed | Verified | Evidence |
|---|---|---|---|
| **Secret redaction** | ❌ No | ⚠️ **Partially** — `scrub_sensitive_info()` in `format_settings.py` redacts OpenAI and Anthropic API keys from settings output (shows last 4 chars). No general output redactor. |
| **Docker/sandbox backend** | ❌ No | ⚠️ **Partially** — Docker images available (`paulgauthier/aider`, `paulgauthier/aider-full`) for running Aider in containers. These are **deployment images, not sandbox enforcement**. No Docker-based sandbox isolation. |
| **Runs on host** | ✅ Yes | ✅ **Confirmed: Yes** | Runs on host. Docker images are for convenience, not security isolation. |

### Layer 3 Defenses (Command/Execution)
- **Git integration**: auto-commits changes — provides rollback capability
- **Approval prompt**: yes/no for adding command output to chat (not tool execution approval)
- **Linting/testing auto-fix**: detects and fixes problems automatically
- **Config-based model selection**: `.aider.conf.yml` for settings
- **No command execution sandbox, no tool-level permission system**

### Layer 4 Defenses (System/Policy)
- **API key redaction**: `scrub_sensitive_info()` redacts API keys from settings display
- **Environment variable config**: `.env` file support for API keys
- No container sandbox, no network controls, no credential vault

**Blog verdict**: Mostly accurate. No Docker sandbox, no general secret redactor (though API keys are scrubbed from settings output). Runs on host.

---

## Summary Comparison Table

| Feature | Claude Code | Codex CLI | OpenClaw | AutoGPT | Cline | Aider |
|---|---|---|---|---|---|---|
| **Secret redaction** | ❌ None | ✅ Regex-based | ⚠️ Log redaction | ❌ None | ⚠️ API secret parser | ⚠️ API key scrub |
| **Docker sandbox** | ❌ (OS sandbox) | ✅ Full sandbox | ✅ Docker default | ❌ (workspace only) | ❌ (subprocess only) | ❌ (deploy images only) |
| **Host execution** | ✅ With OS sandbox | ⚠️ Sandboxed by default | ⚠️ Main=host, others sandboxed | ✅ Workspace-restricted | ✅ With approval gates | ✅ |
| **Command approval** | ✅ Granular | ✅ Sandbox+approval | ✅ Pairing+allowlists | ✅ Pattern matching | ✅ Per tool call | ❌ Ask for output only |
| **Network controls** | ✅ Per-domain | ✅ Sandbox network | ✅ Docker none default | ❌ None | ❌ None | ❌ None |
| **Credential management** | ✅ Keychain | ✅ Keyring | ✅ File perms+audit | ❌ .env only | ✅ OAuth | ❌ .env only |
| **Security certs** | SOC2/ISO27001 | ❌ Not public | ❌ Not public | ❌ None | ❌ None | ❌ None |

## Key Blog Post Corrections

1. **Claude Code CLI**: No secret redactor (✅ correct); no Docker backend (⚠️ correct — uses OS sandbox instead); runs on host (✅ correct but sandboxable)

2. **Codex CLI**: **Significantly understated**. Has explicit output secret redaction, Linux/macOS/Windows sandbox infrastructure, and credential management. This is the most security-complete harness.

3. **OpenClaw**: **Understated**. Has Docker sandboxing as primary backend, output sanitizers, and a comprehensive `security audit` framework.

4. **AutoGPT Classic**: **Accurate**. Truly lacks redaction, Docker sandboxing, and runs on host.

5. **Cline**: **Largely accurate**. No Docker backend, no comprehensive redactor. Has approval gates.

6. **Aider**: **Mostly accurate**. Has API key scrubbing (not general redaction) and Docker deployment images (not sandbox).
