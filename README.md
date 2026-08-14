# fleet

**You are running several coding agents at once and you cannot see which one is stuck, what any of them actually finished, or what it cost.**

`fleet` reads one config file and answers those three questions with things it checked, not things an agent told it.

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

## The finding this came out of

Three topologies, one task, and the decision rule written down before the run: *prefer the solo agent if it reaches 90% of the best score.*

| Topology | Agent turns | Score | Known defects |
|---|---|---|---|
| Small fleet | 3 | 100 | 0 |
| Executor + blocker | 2 | 95 | 1 |
| Solo executor | 1 | 91 | 2 |

All three fixed the primary bug. The difference appeared only on adversarial inputs. Solo scored 91, so **under the registered rule, solo wins** — and solo ships two crash paths.

The rule was not changed after the scores came in. It is defective: economy must never override a known correctness defect. The corrected version is below.

The point is not that the rule was wrong. **A written-down rule can be caught choosing wrong. An unwritten one cannot.** Tune the rule after seeing the scores and you never find out it was defective, because it never disagrees with you.

### What this is not

Whether more agents beat one agent is already settled and is not our claim. [arXiv 2606.05670](https://arxiv.org/abs/2606.05670) ran six multi-agent systems against matched single-agent baselines: at most one beat it, the other five trailed by 2.56 to 11.29 points. Nothing here overturns that.

What this run adds is the condition their averages hide. **The third role paid for itself only because adversarial inputs could change the outcome** — the final coordinator caught a real error both the executor and the first reviewer missed. Read that claim with its limit attached: executor states were not hashed before reviewers edited them, so the exact review lift is **not independently reconstructable**. Final quality is verified; who fixed what rests on reviewer self-report. One task, one model family.

That gap is itself a recurrence of the rule this experiment was built to test — hash at handoff, not at scoring time. It is in the protocol now because it failed here, not because we thought of it first.

### Two controls fired

Both reviewed arms had tests that passed but were not discoverable under plain `unittest discover`; a suite that only passes under its author's chosen command is not yet a control. And the hidden test was itself wrong — overfit to exact wording, rejecting correct implementations — which the blind judge ruled a test defect. A test of independent review was saved by independent review.

### The corrected rule

1. A candidate with a known correctness defect cannot win.
2. If solo is clean and scores ≥90% of the best, use solo.
3. Otherwise use executor + blocker if it scores ≥95% of the small fleet.
4. Use the small fleet when the third role removes a real defect.
5. Freeze and hash every handoff before another agent edits it.

**Operating conclusion:** solo for bounded implementation, one blocker by default for measurement, security and release claims, the full fleet when malformed input or adversarial judgement can change the answer.

### Run it yourself, on your own data

This ships the instrument, not the readings. You point it at your own harness logs and your own repos and generate your own numbers; nothing from ours travels with it. Run 1 appears above only as aggregates.

And an honest note on where this started: run 1 was not a clean experiment. There was a structure, data was gathered, and a lot of it was vibes. Run 2 is the first one with a protocol written before the work. A bench that pretends its first run was clean is a bench nobody should trust.

## Try it in one command, on nothing

No config of your own, no agents, no setup. This builds three throwaway repos under `examples/sandbox/` and runs against them:

```sh
git clone https://github.com/Morkeeth/fleet.git
cd fleet
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

### What a fleet costs, and what this will not tell you

Run 1 was four lanes over three days, 11 to 13 August. The Claude Code harness recorded **19,854,778 output tokens** in that window, measured on 14 August.

Read it as a floor, not a total. An earlier extraction of the same window returned 19,027,962 — not because more work happened in between, but because the window had not been frozen when it was first measured. It also excludes every other vendor, all cache reads, all input tokens, and every minute of human time.

A number like this is only admissible with its window attached. Quoted bare it is the same figure and a much worse claim, which is why you will see it stated here and cut from anywhere that could not name the window.

No dollar figure here. We have no vendor-side total, and converting one would be inventing a number.

**Nothing in this repo caps or projects spend.** `fleet cost` is post-hoc — it tells you what a run cost after it has cost it. A ceiling has to come from your vendor's own controls, and if you are about to point four lanes at three days of work, set one first.

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
