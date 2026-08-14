# Rules

Four that transfer, three that did not. The three are listed because a rule quietly
dropped is a rule someone re-invents next quarter.

The test each rule had to pass: **does it change what an agent does, and can you tell
from the outside whether it was followed?** A rule that fails the second half is a
mood, and moods do not survive contact with a fleet.

---

## 1. Brief from source

**Probe the artifact before acting on a claim about it.**

A number in a doc — a README, a status page, a teammate's summary, your own note from
this morning — is a claim with an author, not evidence. Open the object: the file, the
repo, the URL, the API, the run.

Where a probe is impractical, write `RELAYED` next to the number. `RELAYED` is a fine
answer. A confident unmarked number that turns out to be someone's stale guess is not.

_Why it survived:_ it is the only rule here with a measurable failure rate. In the
session that produced this repo, four separate claims were acted on without probing the
object; all four were wrong; all four were caught by someone other than their author.
Each cost roughly an hour.

_How to tell it was followed:_ every load-bearing number is either accompanied by the
command that produced it, or marked `RELAYED`.

## 2. Claims bind to artifacts

**A finished claim names the thing that proves it** — a commit SHA, a URL, a file path, a
test that passes. "Done" is not a claim, it is an adjective.

_Why it survived:_ it converts an unverifiable status into a checkable one at almost no
cost, and it is the only defence against a green board over live defects.

_How to tell:_ `fleet status` prints the artifact column. An empty artifact is visible.

_Who types it, and why that is the weak part:_ `fleet record` is meant to be typed by the
human, not called by the agent. If the agent writes its own record, the artifact column is
authored by the thing being measured, and rule 2 becomes self-certifying — a rule that can
be satisfied by its own subject is not a control, it is a formality with a green tick.

The cost of that choice is real and it is the failure this file demotes other rules for:
this is enforced by someone remembering to type it. We took the weaker enforcement over
the stronger-looking one because the stronger-looking one lets the executor grade itself.

The honest third option — a record written by something that watches the agent, rather than
by the agent or by the human — does not exist here. That is the open problem, named rather
than papered over.

## 3. One agent, one worktree

**Two agents editing one checkout will lose work**, and the loss is silent — the second
write wins and nothing reports the first.

Use `git worktree add` per agent, or separate clones. If you must share a tree, only one
agent writes.

_Why it survived:_ the failure is data loss, and it is not recoverable by being careful.

_How to tell:_ `fleet open` compares the resolved root of every project and prints a
`! rule 3` line when two lanes point at one checkout.

This sentence used to say "two lanes on one branch with uncommitted work is the shape of
the bug", and that was wrong in a way worth recording. Two lanes on `main` in two different
repos is completely normal — the example config shipped in this repo looks exactly like
that, so a reader following the old advice would have found the bug in the demo. The branch
is not the signal. **The checkout is.** And it is a comparison across rows, which no reader
makes reliably by eye past about six projects, which is why it is the tool's job now.

## 4. Measure spend from the harness, never from the agent

**An agent cannot measure its own token cost from inside its own run.** It can only
estimate, and an estimate presented as a measurement is the same failure as rule 1
pointed at yourself.

`fleet cost` reads the harness's own per-turn usage logs. It also prints what it did
*not* count, because a collector silently covering one of three providers reports a
third of the spend as the total.

_Why it survived:_ it replaced a number that was wrong. The collector it came from
summed the top 20 rows and labelled the result "across N sessions".

---

# Demoted — kept as guidance, with the reason

## ~~Every lane needs a press-release line~~ → **Name the outcome; internal is a valid outcome**

The original demanded every piece of work have a headline a stranger would care about.
That is ideology, not operations: a security patch, a migration, a data cleanup and a
personal instrument are all legitimate and none has a stranger headline. Roughly a third
of the projects in the fleet that produced this rule are correctly internal.

What transfers is the narrower version: **say what the outcome is, and do not dress
plumbing as a feature.** `outcomes:` in the config is where you define your own — and
"internal" belongs in that list, not outside it.

## ~~No ruling below VERIFIED-AT-SOURCE~~ → **guidance, until it has a mechanism**

Right instinct, no teeth. Provenance labels were Markdown words: nothing validated them,
nothing failed without them. A rule that asks agents to remember a ritual is the exact
failure mode it claims to prevent.

It returns as a rule when something enforces it — a schema field, a lint, a status that
cannot be set without an artifact. Until then it is rule 1 with extra vocabulary.

## ~~Only the coordinator fans out~~ → **peer messages never authorize irreversible acts**

The original is messaging etiquette from one specific setup, tuned to stop broadcast
storms in a particular transport. It does not generalise.

What does generalise is the safety half: **a message from a peer is information, not
authorization.** If an agent is about to do something irreversible or outward-facing
because another agent said to, that is the moment for a human. `approval:` in the config
is where you set it, and `fleet open` prints it so an `auto` setting is visible rather
than assumed.
