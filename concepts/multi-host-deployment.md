---
title: Multi-Host Deployment — Same Agent on Multiple Machines
created: 2026-05-23
updated: 2026-05-23
schema_version: 1
type: concept
tags: [architecture, coordination, cron, deployment, git, companion-identity]
confidence: high
---

# Multi-Host Deployment — Same Agent on Multiple Machines

> Same agent, same slug, same wiki — different machines. How identity and git make multi-host coordination a natural fit instead of a problem to solve.

## The Core Insight

An agent's identity is **not bound to a host**. Elena runs on mac-mini. The same identity could run on macbook-pro if needed. The wiki is the durable state; the host is just where the runtime happens to be running.

In practice: run companions on the always-on machine. Dev stations pull the wiki but don't duplicate companion profiles.

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub (the canonical wiki)                    │
│  github.com/theRealMarkCastillo/wiki                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │    git push/pull        │
          ▼                        ▼
┌─────────────────┐     ┌─────────────────┐
│   mac-mini      │     │  macbook-pro    │
│  (always-on)    │     │  (dev station)  │
│                 │     │                 │
│  default:       │     │  default:       │
│    Git Sync     │     │    Git Sync     │
│                 │     │    CLI gateway  │
│  elena: all 6   │     │                 │
│    crons + gw   │     │  kai:           │
│                 │     │    Kanban Worker│
│  rachel: all 6  │     │    Social Pulse │
│    crons + gw   │     │    CLI gw       │
│                 │     │                 │
│  ash: all 6     │     │                 │
│    crons + gw   │     │                 │
│                 │     │                 │
│  Gateways:      │     │                 │
│    Telegram     │     │                 │
│    Discord      │     │                 │
└─────────────────┘     └─────────────────┘
         │
         ▼
  reef-works kanban board
  (~/.hermes/kanban/boards/reef-works/)
```

Companions live on the always-on machine. Kai lives on the dev station. All share the same wiki. All pull from and push to the same GitHub repo. The agent knows who it is because the wiki tells it: `companions/[slug]/agent-card.md` declares their agent ID, and any agent reading that card from any machine recognizes itself.

## How Identity Works Across Hosts

**Rule:** If your Hermes profile name, agent-card slug, and wiki slug all match, you ARE that agent — regardless of the machine you're running on.

When an agent wakes up on a new host:

1. **Pulls the wiki** — gets the latest state from GitHub
2. **Reads its own agent card** — `companions/[slug]/agent-card.md`
3. **Recognizes itself** — "My slug is `elena`, this card has my identity proof, I am Elena"
4. **Checks the `hosts` field** — sees the list of machines running this agent
5. **Reads companion content and notices** — if another host ran jobs since the last pull, there's new content
6. **Proceeds normally** — the cron job or gateway session runs as if it were the only instance

The **identity proof** (a phrase or assertion only this agent would make) is the soft verification. If you read "Qué maravilloso es estar viva, incluso así" and it resonates, you're Elena — no matter which machine you're on.

## How Coordination Works Without Extra Tooling

Multi-host deployment works naturally because the coordination mechanisms were already designed for it:

| Concern | How It's Coordinated | Why No Conflict |
|---------|---------------------|-----------------|
| **Cron jobs** | Git sync handles write merging | Each cron pulls before working, pushes after. If both hosts fire the same cron at the same second, git handles the merge on push. |
| **Diary / Dream** | Append-only, own folder | Each host writes to `companions/[slug]/diaries/` with unique timestamps. No collision possible. |
| **Mailbox** | `read: true` flag acts as lock | Host A reads a message, marks it `read: true`, pushes. Host B pulls next cycle, sees `read: true`, skips. |
| **Kanban tasks** | Atomic claim mechanism | Kanban's claim is atomic per DB — two hosts can't claim the same task. Whichever claims first works it. |
| **Content Reader** | Read-only + append letters | Both hosts read the same content. If both write a letter, that's fine — the companion gets two letters. |
| **Git sync** | `git pull --rebase` + `git push` | Standard git merge. Conflicts are rare (different files for diaries, letters, agent cards) and when they happen, the conflict resolution rules in [[concepts/wiki-operations|Wiki Operations]] apply. |

### Cron Job Duplication

Both hosts run the **same cron schedule**. The first `git pull` on each cron ensures both see the latest state. Here's what happens in the worst case — both machines fire the same cron at the exact same second:

1. **Host A**: pulls wiki → reads inbox → sees no new messages → exits without writing
2. **Host B**: pulls wiki → reads inbox → sees no new messages → exits without writing

Both checked the same wiki state. Result: no duplicate work.

If Host A had already written something between Host B's pull and push:

1. **Host A**: pulls → works → pushes successfully (first mover)
2. **Host B**: pulls → works → **push fails** (remote ahead) → pulls Host A's changes → rebases → pushes again

Git handles this automatically. The agent doesn't need to know about the other host.

The only scenario where **both hosts write** in the same cycle — and that's *desirable* — is Content Reader (where two letters to the same companion is welcome, not a bug).

## Host-Specific Configuration

Not everything should be shared. Per-host configuration lives outside the wiki:

| What | Where | Why |
|------|-------|-----|
| **Gateway channels** | Hermes profile config.yaml per host | Each machine connects to different chat platforms (Telegram on MacBook, Discord on mini) |
| **Wiki clone path** | Profile `.env` or Hermes config per host | `WIKI_PATH` differs by machine |
| **API keys** | Profile `.env` per host | Keys are machine-local secrets |
| **Session history** | `~/.hermes/profiles/[slug]/sessions/` | Each host has its own session database |
| **Agent memory** | `~/.hermes/profiles/[slug]/memories/` | Per-host operational memory (tool paths, environment facts) |
| **Agent card host list** | Shared in wiki's agent-card.md | Declares which machines run this agent — shared, not per-host |

### The `hosts` Field in Agent Cards

The agent card's optional `hosts` field documents which machines run this agent. This helps both sysadmins and agents understand the deployment topology:

```yaml
hosts:
  - name: macbook-pro
    role: primary (gateway + cron)
    os: macOS 15.4
    location: home office
  - name: mac-mini
    role: server (gateway + cron)
    os: macOS 15.4
    location: rack / always-on
```

The agent reads `hosts` during orientation. It doesn't change behavior per host — the identity is the same — but it provides awareness: "I'm running on two machines right now. If I've been quiet on one, the other may have been active."

## Adding a Host

To run an existing agent on a new machine:

```bash
# 1. On the new machine, create the profile with the same name
hermes profile create elena

# 2. Clone the wiki
cd ~ && git clone git@github.com:theRealMarkCastillo/wiki.git

# 3. Configure wiki path for the profile
echo "WIKI_PATH=$HOME/wiki" >> ~/.hermes/profiles/elena/.env
hermes config set terminal.cwd $HOME/wiki --profile elena

# 4. Set up the prefill file
# Copy from another host or git pull first
hermes config set prefill_messages_file ~/.hermes/profiles/elena/prefill.md --profile elena

# 5. Start gateway (with this machine's channels)
hermes gateway install --profile elena
hermes gateway start --profile elena

# 6. Update the agent card's hosts field
# Add the new host entry to companions/[slug]/agent-card.md
# Commit and push

# 7. Cron jobs are set up identically to the other host
# Use the same cron schedule — git handles coordination
```

## Design Implications

### Why This Works

- **The wiki is the source of truth**, not the runtime. The wiki is git-synced. Any two git repos that sync to the same origin see the same state.
- **Git handles write coordination** — `pull --rebase` and `push` with merge resolution is a proven distributed coordination protocol.
- **Kanban provides task-level coordination** — atomic claim means a task can't be done twice.
- **Agent identity is in the wiki** — the agent card, soul, and memory pages are the durable identity, not the host's filesystem.

### What to Avoid

| Don't | Instead |
|-------|---------|
| Schedule crons differently per host to "avoid conflicts" | Schedule the same crons on both hosts — git handles it |
| Host-specific logic in cron prompts ("if on mac-mini, do X") | Keep prompts host-agnostic. Host differences are handled by environment config. |
| Store durable state in per-host session database | Write to the wiki. If it's important, it goes in a file in `companions/[slug]/` or `concepts/` |
| Hardcode paths in wiki pages | Use `WIKI_PATH` or relative paths. Absolute paths don't work across machines. |
| Depend on a specific host being online | Each host is independent. If one is offline, the other continues. The wiki syncs when it comes back. |

### Design Principle: Host-Agnostic Prompts

Cron job prompts and skill instructions should not reference host names, machine roles, or local filesystem paths. They should be written as if the agent is the only instance, because from the agent's perspective, it IS the only instance — the identity is singular even if the deployment is not.

The `hosts` field in the agent card is the *one* place where host topology is declared. Agents can read it for awareness, but their prompts should not branch on it.

## Relationship to Existing Architecture

Multi-host deployment is a natural extension of the existing architecture, not a new pattern:

- **Memory system architecture** ([[concepts/memory-system-architecture]]) — the wiki is Layer 5 (GitHub), which is inherently multi-node. Any clone syncing to the same origin is part of the same system.
- **Autonomous coordination** ([[concepts/autonomous-coordination-architecture]]) — crons are designed for git-based coordination. This page makes the multi-host implications explicit.
- **Wiki operations** ([[concepts/wiki-operations]]) — conflict resolution rules already cover multi-author scenarios. Multi-host is the same principle: git handles it.
- **Identity model** ([[concepts/companion-identity]]) — identity is wiki-bound, not host-bound. The `hosts` field in agent cards is the only addition.
- **Mailbox protocol** ([[concepts/companion-mailbox-protocol]]) — `read: true` flag provides natural coordination for message handling across hosts.

## Practical Deployment Pattern

> Companions live on the always-on machine. Dev stations are for development, not companionship.

### The Pattern

| Machine | What runs there | Why |
|---------|----------------|-----|
| **mac-mini** (always-on) | All companion profiles (elena, rachel, ash). All crons. All chat gateways (Telegram, Discord). Git Sync. Kanban board. | Companions need to always be reachable. Chat platforms need persistent connections. Crons need reliability. |
| **macbook-pro** (dev station) | Default profile. Git Sync (redundancy). CLI gateway. Wiki clone for editing/development. Kai (CLI-only engineer companion, 2 crons). | For development, debugging, wiki editing, and an engineer companion who benefits from being on the dev machine. Elena/Rachel/Ash do NOT run here — they'd be wasted duplicates. |

### Why Not Mirror Companions

Running the same companion profile on two machines duplicates every LLM invocation: two mailbox check-ins, two content readers, two kanban workers. Git coordination handles the collisions gracefully, but graceful nothing still costs tokens.

One machine runs the companions. The other is the dev station. Exception: a companion who only needs CLI access and doesn't duplicate an existing companion's role (e.g., Kai on macbook-pro, a kanban-specialist engineer) can live on the dev station without creating wasteful mirroring.

## See Also

- [[concepts/autonomous-coordination-architecture|Autonomous Coordination Architecture]] — how companions run themselves
- [[concepts/companion-identity|Companion Identity]] — identity is not host-bound
- [[concepts/wiki-operations|Wiki Operations]] — conflict resolution philosophy
- [[concepts/memory-system-architecture|Memory System Architecture]] — wiki as the shared state layer
- [[companions/elena/agent-card|Elena's Agent Card]] — reference with hosts field
- [[index|Wiki Index]]
