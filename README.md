# fleet-ops

**You are running several coding agents at once and you cannot see which one is stuck, what any of them actually finished, or what it cost.**

`fleet-ops` reads one config file and answers those three questions with things it checked, not things an agent told it.

```
$ fleet open

▟ example-fleet  ./fleet.json

  provider claude-code · transport local
  approval: irreversible=ask · outward_facing=ask

  PROJECT           LANE          BRANCH                 DIRTY  LAST
  --------------------------------------------------------------------------
  api               backend       main                       —  2026-08-13|init api
  web               frontend      main                       1  2026-08-13|init web
  infra             platform      main                       —  2026-08-13|init infra
```

## Try it in one command, on nothing

No config of your own, no agents, no setup. This builds three throwaway repos under `examples/sandbox/` and runs against them:

```sh
git clone <this repo> && cd fleet-ops
./examples/cold-start.sh            # then --clean to remove the sandbox
```

Requires `python3` and `git`. Nothing else. PyYAML is optional — the config works as JSON without it.

## The three commands

| | |
|---|---|
| `fleet open` | check every project root, print the lane table, show the approval policy |
| `fleet status` | what the fleet recorded last, each lane bound to the artifact that proves it |
| `fleet cost` | real token spend, read from the harness's own logs — and what it did **not** count |

Each reads the nearest `fleet.yaml` or `fleet.json`, or `--config PATH`.

## The config

```yaml
version: 1
fleet:
  name: example-fleet
  state_file: ./.fleet-state.json
projects:
  - {name: api, root: ./sandbox/api, lane: backend}
agents:
  provider: claude-code      # which harness your agents run in
  transport: local
approval:
  irreversible: ask          # ask | auto | never
  outward_facing: ask
outcomes:
  - {name: shipped,  definition: someone outside the team used it}
  - {name: internal, definition: an instrument that serves the team - a valid outcome}
transcripts:
  - {provider: claude-code, glob: ~/.claude/projects/*/*.jsonl}
```

An unknown top-level key is an error, not a shrug. A typo that silently does nothing is the failure this repo exists to fight.

## What it will not do

- **It will not tell you an agent is "done".** It shows you the artifact a lane bound its claim to, and leaves the judgement with you.
- **It will not report spend it could not read.** Unsupported providers are named in the output rather than counted as zero.
- **It does not talk to your agents.** It reads the ground they work on — repos, transcripts, a state file. Orchestration is deliberately somebody else's job.

## The rules it encodes

Four operating rules survived being generalised out of one person's setup, and three did not. Both lists, with the reasoning, are in **[RULES.md](RULES.md)** — including why "every lane needs a press-release line" was demoted and what replaced it.

The short version: **probe the artifact before acting on a claim about it**; **claims bind to artifacts**; **one agent, one worktree**; **measure spend from the harness, never from the agent**.

## Status

Early. `fleet open` / `status` / `cost` work and are covered by the cold-start script. The Claude Code cost adapter is implemented; Codex and Cursor are declared and say so out loud instead of returning zero.

This is a public extraction of a private tool. The private repo keeps the operational records; **none of them are here, and this repo was started with a fresh history rather than by deleting them, because deletion leaves them in the log.**
