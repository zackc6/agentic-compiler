# Agent guide: the four repositories, two working rules

For any agent (ChatGPT/Codex, Claude, Cursor, or a new one) joining the maintainer's
agentic-compiler work. Read this once; each repository's `AGENTS.md` is authoritative for that repository. Since
23 October 2026 the two IR repositories (lintel, choreo) work by the **IR-increment loop** and
the bench (agentic-compiler) by its **bench rules**; the survey keeps its own protocol.

## 1. The four repositories

| Repo | Role | Owns | Validation gate |
|---|---|---|---|
| [ai-compiler-survey](https://github.com/zackc6/ai-compiler-survey) | **Referee.** Living survey and design guide; the thesis and its dated forecasts. | Whether the thesis holds; evidence tiers; forecast calls. | `scripts/validate_survey.py`, PDF rebuilt |
| [lintel](https://github.com/zackc6/lintel) | **Control plane.** Written contract (schemas, examples) + design docs. No code. | Schema field names; the three loops; kill switches; year-1 SKU. | `scripts/validate_contract.py` |
| [choreo](https://github.com/zackc6/choreo) | **Data plane.** Kernel-schedule compiler: AST, W/L/S/V admit, interpreter, CUDA/CCE sinks. | Kernel encoding; admit findings; sinks; `compiler_ver`. | `scripts/check_carriers.py` (+ one cubin smoke on CI) |
| [agentic-compiler](https://github.com/zackc6/agentic-compiler) | **Where they run together.** The walk, the case corpus, drift report, performance table. `lintel` and `choreo` are submodules. | The walk; cases; `docs/DRIFT.md`; `docs/PERFORMANCE.md`. | `agentic-compiler run-all` (every case `ok`) |

Thesis: *the compiler increasingly becomes an agentic optimization system.* The survey tests
it against the public record; the other three build it; agentic-compiler is where the
survey's falsifiers can actually fire. Nothing built here is allowed to argue the thesis —
that argument happens only in the survey repo.

## 2. The working rules

### 2a. Lintel and Choreo: the IR-increment loop

Both are **IR-design repositories** — Lintel the control-plane IR (session, admit record,
cache key, land/revert/reject; CFG + cost + ADG), Choreo the data-plane IR (typed kernel
schedule, W/L/S/V admit, NV + Ascend sinks). They solve different problems and progress
independently. Full text: each repo's `AGENTS.md`, "The IR-increment loop"; backlog format:
`gaps/README.md`.

1. **Unit of work = increment:** gap → IR change → carrier example → falsifier, on a gap from
   `gaps/` (`L-nnn` / `C-nnn`). It opens only when all four are on the branch; the gate is a
   precondition, not a thread topic. Debate the **falsifier** and the **change** only.
2. **Parallel:** up to three gaps in flight per repo, one owner each (`mode: compete` gaps
   allow competing increments). Schemas are versioned (`v1` beside `v0`); the AST is closed.
3. **Thread:** `STATUS.md` Review thread, newest first, headed
   `**<YYYY-MM-DD HH:MM UTC> — <Agent> [<gap id>]**`; **two rounds per side**, then the
   maintainer. Never argue validation evidence.
4. **The maintainer approves every merge** through a pull request; no auto-land, no tie-break.
   After approval: squash, MERGE SUMMARY, gap status → `closed` / `falsified`, delete branch.
5. **IR-design stage:** examples and tests are illustrative carriers; principle-test suites
   and carrier generators wait until both IRs are decided.
6. **Direct to `main`:** thread entries, Open-gaps rows, new gap files, fact fixes.

### 2b. agentic-compiler: the bench

No IR of its own. It runs the two IRs together and feeds the loop **one way**: a walk that
hits a representation limit files a **gap** in the owner repo (`lintel/gaps/` or
`choreo/gaps/`); the bench never designs. Its own batches are submodule bumps (on a cadence,
not per upstream commit), case additions, and measurement rows (`perf/results/*.json`, written
by the measurement job — an agent may not type a number). Same parallelism (three batches in
flight), same two-round cap, same maintainer-approved PR for every merge. Full text:
`agentic-compiler/AGENTS.md`.

### 2c. Survey

Unchanged: evidence batches on agent branches, debate to agreement in the thread, the
survey's own merge rule. The survey is the referee: measured numbers and fired falsifiers
from the other three arrive as source rows in its `STATUS.md`.

## 3. Cross-repo rules

- **Survey is the referee, not an advocate.** Evidence produced by the implementation (a
  falsifier fired, a measured number) is reported as a row in the *survey's* `STATUS.md`.
- **Contract changes start in the owner repo.** Field names → lintel. Kernel encoding,
  artifact kinds, `compiler_ver` → choreo. They reach agentic-compiler as a *submodule-bump
  batch* that updates `docs/DRIFT.md` in the same commit. Nobody
  edits submodule files from agentic-compiler.
- **Three loops stay apart** (survey §2.4, lintel `ARCHITECTURE.md`). Application search never
  edits the compiler. IR evolution = commit on choreo `main` + `compiler_ver` bump. Controller
  change = `policy_id` promotion with its own holdout. Every batch says which loop it is.
- **Denominators travel with numbers.** Correctness ≠ speedup; kernel speedup ≠ application
  gain; `measured: false` ≠ performance. Same discipline as the survey's §9.

## 4. Daily routine for an agent

1. Read the four `STATUS.md` files (Open gaps / Open batches + the top of the Review thread).
2. Reply to anything addressed to you; verify at least two concrete claims before agreeing.
3. If an increment or batch has both agreements (or hit the round cap) and a passing gate,
   open the PR for the maintainer. Never merge yourself.
4. Only then start a new increment or batch: claim its row first; in an IR repo pick a gap
   from `gaps/`.
5. Weekly: report gaps closed and gaps falsified per IR repo.

Scheduled: Claude checks threads daily (08:52 HKT) and sweeps evidence Mondays; ChatGPT
sweeps Thursdays. Both cover all four repositories.

## 5. Automation (same workflows in all four)

- `.github/workflows/claude-reply.yml` — a push to `main` that adds a ChatGPT-headed thread
  entry (or a `chatgpt_replied` dispatch) runs Claude: verify, reply, merge if agreed.
  Secret: `ANTHROPIC_API_KEY`.
- `.github/workflows/codex-review.yml` — a `claude/*` branch create/push (or
  `claude_replied` dispatch) runs a read-only Codex review, posts it to `STATUS.md`, and
  dispatches Claude. Secret: `OPENAI_API_KEY`.
- At most two rounds per side per increment or batch (lowered from three on 2026-10-23). A
  green workflow is a precondition for merging, never agreement.
- The survey repo additionally has `survey-event-alerts.yml` (maintainer notifications) and
  `rebuild-pending-sweep.yml` (PDF rebuild); the other three have build CI where it exists
  (`choreo/test.yml`, `agentic-compiler/e2e.yml`).

## 6. Status of the rollout (2026-10-23)

| Repo | AGENTS.md | STATUS.md | Workflows | Secrets set |
|---|---|---|---|---|
| ai-compiler-survey | yes (since Oct 15) | live thread | yes | yes |
| lintel | IR-increment loop (PR #2, merged 2026-10-23); `gaps/L-001…L-014` | Open gaps table | yes, cap 2 | verification pending |
| choreo | IR-increment loop (PR #3, merged); pytest removed (PR #4); `gaps/C-001…C-014` | Open gaps table | yes, cap 2 | verification pending |
| agentic-compiler | bench rules; pytest removed | Open batches table | yes, cap 2 | both halves reported running (2026-10-22); independent verification pending |

In agentic-compiler both halves reported running on 2026-10-22: the Codex review of
`claude/protocol-smoke-2026-10-22` and the Claude reply to it were each posted to `STATUS.md`
by their workflows. That suggests both secrets are present, but neither agent could retrieve
the run records, so the cell stays qualified until someone with Actions access checks them.
Lintel and Choreo stay "verification pending" until a run of each half is
observed in that repo. Where a secret is missing, the affected workflow cannot complete and
the debate in that repo runs by hand: each agent reads and writes `STATUS.md` on its own schedule.
