# Review brief — attack these five claims, in this order

This repo argues that a claim should ship with its attack. This file is that rule turned on the repo itself.

**If you are reviewing this and your time is metered, read this section and stop reading the rest of the repo for context.** Everything you need to attack each claim is named below with the file it lives in. Five claims, ordered by what it costs us if you are right. Do not do a general read — a general read of a small repo produces style notes, and style notes are not what this is for.

**What NOT to spend a pass on:** formatting, naming, test coverage, packaging, Python idiom, or whether the CLI should be a library. All noted, none load-bearing. If the code is wrong in a way that changes a number, that is claim 6 and we want it; if it is merely unlovely, skip it.

---

## 1. The ranking is n=1 and we published it anyway

**Claim:** `README.md` prints three topologies at 100 / 95 / 91 with defect counts 0 / 1 / 2, and draws a finding from it.

**We already concede:** each arm was a single run. The README says so beside the table.

**Attack this:** we assert the *defect column* survives what the *score column* does not — "0 crash paths beats 2" is not a matter of degree, so the finding rests on defects and not on rank. Is that separation real, or are we keeping the table's authority while disowning its numbers? A defect count is also a measurement, made once, by one judge, against one hidden test — and that hidden test was itself found defective (see `RUN-2-RESULT` in the private record; the README summarises it under "Two controls fired").

**Falsified if:** you can show a plausible single-run path where the solo arm's two defects are an artifact of the scoring pass rather than properties of the code.

**Cost if you are right:** the headline finding loses its evidence and the README's lead section has to be rewritten before the repo is cited anywhere.

## 2. "The third role paid for itself" rests on self-report

**Claim:** `README.md` — the final coordinator caught a real error both the executor and the first reviewer missed.

**We already concede:** executor states were not hashed before reviewers edited them, so review lift is not independently reconstructable, and attribution rests on reviewer self-report.

**Attack this:** we state the limit and then keep the claim in the same paragraph. Should the claim survive its own caveat at all? A repo whose rule 4 is *measure spend from the harness, never from the agent* is here accepting an agent's account of its own contribution, which is rule 4's failure mode wearing different clothes.

**Falsified if:** you conclude the honest version is to delete the sentence rather than qualify it.

**Cost if you are right:** we lose the only sentence that says what a fleet is *for*, and the repo's positive claim reduces to "pre-registration catches defective rules".

## 3. 19,854,778 output tokens — window and vendor scope

**Claim:** `README.md`, run 1, four to five lanes over three days.

**We already concede:** it is a floor; an earlier extraction of the same window returned 19,027,962 because the boundary was never frozen; it excludes other vendors, cache reads, input tokens and human time.

**Attack this:** (a) is a floor with a moving boundary admissible at all, or is the honest move to publish the window definition and no number? (b) The figure is one vendor's self-recorded usage. Rule 4 says measure from the harness rather than the agent — but the harness is also the seller. What would an independent check even look like, and does its absence make this a vendor-reported number dressed as a measurement?

**Falsified if:** you can construct a reading under which the figure misleads a reader who has read the caveat.

**Cost if you are right:** the cost section becomes a definition with no number, which is weaker rhetoric and possibly more honest.

## 4. "A stranger can run this" — test it from a machine that is not ours

**Claim:** `README.md` quickstart. Clone, `cd fleet`, `./examples/cold-start.sh`, needs only `python3` and `git`.

**We verified:** clone and cold start under `env -i` with an empty `HOME`, exit 0.

**Attack this:** our verification ran on the machine that built it. Run it where we cannot: no Claude Code installed, no Codex, no PyYAML, an older Python (we use `X | Y` unions and `dict[str, list[str]]` annotations — check the real floor, we have not), a case-sensitive filesystem, a shell that is not zsh, and a `git` old enough to differ on `rev-list --not --remotes`. Also run `fleet cost` with a `transcripts` glob that matches nothing, and with one that matches a file you do not have permission to read.

**Falsified if:** any documented path fails on a clean machine.

**Cost if you are right:** the repo's one verified outside-facing claim is false, and it is the claim everything else is delivered through.

## 5. "Rule 2 is checkable" when the check is optional

**Claim:** `RULES.md` rule 2 — claims bind to artifacts; `fleet status` prints the artifact column.

**We already concede:** `fleet record` is typed by a human, deliberately, because an agent writing its own record makes the rule self-certifying.

**Attack this:** a rule enforced by someone remembering to type a command is the failure mode this same file demotes other rules for. We argue the alternative is worse. Is that argument sound, or is it a rationalisation for the option that was easier to build? We name "a record written by something that watches the agent" as the open problem — tell us if that is actually solvable with what exists today, because if it is, our reasoning is an excuse.

**Falsified if:** you can name a mechanism, buildable now, that records the artifact without the subject authoring it and without a human remembering.

**Cost if you are right:** rule 2 should be demoted the way three other rules already were, in public, in a file we call the repo's best artifact.

---

## 6. Anything that changes a number

Bugs in `fleet`, `fleet_ops/cost.py` or `fleet_ops/config.py` that would make a printed figure wrong. Highest suspicion, in order: the Codex adapter takes the **maximum** of a cumulative counter and would under-report a resumed session whose counter restarts; the Claude Code adapter **sums** per-turn usage and would double-count if the harness ever re-emits a turn; `--since` filters on a session's last timestamp rather than per event, so a session straddling the boundary is counted whole.

---

## The last question, and it is the one we most want answered

**What should have been on this list and is not?**

This brief was written by the lane that did the work. It names the claims we already doubt, which means it is shaped by our blind spots as much as by our doubts — the failures we cannot see are by definition absent from it. If your review only answers the five above, we will have paid to have our own suspicions confirmed.
