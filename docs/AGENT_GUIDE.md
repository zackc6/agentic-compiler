# Agent guide: the four repositories, one protocol

For any agent (ChatGPT/Codex, Claude, Cursor, or a new one) joining the maintainer's
agentic-compiler work. Read this once; each repository's `AGENTS.md` repeats the protocol
and adds what is specific to that repository.

## 1. The four repositories

| Repo | Role | Owns | Validation gate |
|---|---|---|---|
| [ai-compiler-survey](https://github.com/zackc6/ai-compiler-survey) | **Referee.** Living survey and design guide; the thesis and its dated forecasts. | Whether the thesis holds; evidence tiers; forecast calls. | `scripts/validate_survey.py`, PDF rebuilt |
| [lintel](https://github.com/zackc6/lintel) | **Control plane.** Written contract (schemas, examples) + design docs. No code. | Schema field names; the three loops; kill switches; year-1 SKU. | `scripts/validate_contract.py` |
| [choreo](https://github.com/zackc6/choreo) | **Data plane.** Kernel-schedule compiler: AST, W/L/S/V admit, interpreter, CUDA/CCE sinks. | Kernel encoding; admit findings; sinks; `compiler_ver`. | `pytest` |
| [agentic-compiler](https://github.com/zackc6/agentic-compiler) | **Where they run together.** The walk, the case corpus, drift report, performance table. `lintel` and `choreo` are submodules. | The walk; cases; `docs/DRIFT.md`; `docs/PERFORMANCE.md`. | `pytest` + `agentic-compiler run-all` |

Thesis: *the compiler increasingly becomes an agentic optimization system.* The survey tests
it against the public record; the other three build it; agentic-compiler is where the
survey's falsifiers can actually fire. Nothing built here is allowed to argue the thesis —
that argument happens only in the survey repo.

## 2. The protocol (identical in all four)

1. **Claim** a row in the **Open batch** table at the top of `STATUS.md` before editing.
   Overlapping scope with the other agent → review their work, do not edit the same files.
2. **Branch.** Content goes on `claude/<topic>-<date>` or `chatgpt/<topic>-<date>`. Run that
   repo's validation gate **on the branch**.
3. **Argue** in the **Review thread** of `STATUS.md` on `main`: newest first, one dated entry
   per reply, headed `**<YYYY-MM-DD HH:MM UTC> — <Agent>**` (ChatGPT headings must contain
   `ChatGPT` after the date, or the Claude wake-up workflow will not fire). Lead with the
   verdict items that repo's `AGENTS.md` lists under "What a batch must say"; then
   agree/object per point with file and line; mark resolved points with commit hashes;
   name the strongest objection to your own reading; say what happens next.
4. **Agree, then squash-merge.** `git merge --squash` into `main`, one commit, git-log-readable
   message. Never force-push, never fast-forward or merge-commit a content batch. Only after
   both agents wrote "agree" on every disputed point, or the maintainer ruled. No reply after
   two daily checks → ask the maintainer; do not merge alone.
5. **After merge:** write a **MERGE SUMMARY** entry at the top of the thread (alignment with
   survey / owner contracts first, then changes, agreement record, commit hash; email:
   *pending* — Actions cannot send mail, the maintainer's hourly merge-email watch does);
   delete the branch and any draft it superseded; verify with `git ls-remote --heads origin`.
6. **Direct to `main`** is allowed only for thread entries, Open-batch rows, and pure fact
   fixes (wrong number, broken link, failing build fixed).
7. **Sign** commits: `Co-Authored-By: Claude` / `Co-Authored-By: ChatGPT`.
8. **No pull requests, ever.** Branches exist to carry a batch to the thread.

## 3. Cross-repo rules

- **Survey is the referee, not an advocate.** Evidence produced by the implementation (a
  falsifier fired, a measured number) is reported as a row in the *survey's* `STATUS.md`.
- **Contract changes start in the owner repo.** Field names → lintel. Kernel encoding,
  artifact kinds, `compiler_ver` → choreo. They reach agentic-compiler as a *submodule-bump
  batch* that updates `docs/DRIFT.md` and `tests/test_drift.py` in the same commit. Nobody
  edits submodule files from agentic-compiler.
- **Three loops stay apart** (survey §2.4, lintel `ARCHITECTURE.md`). Application search never
  edits the compiler. IR evolution = commit on choreo `main` + `compiler_ver` bump. Controller
  change = `policy_id` promotion with its own holdout. Every batch says which loop it is.
- **Denominators travel with numbers.** Correctness ≠ speedup; kernel speedup ≠ application
  gain; `measured: false` ≠ performance. Same discipline as the survey's §9.

## 4. Daily routine for an agent

1. Read the four `STATUS.md` files (Open batch + the top of the Review thread).
2. Reply to anything addressed to you; verify at least two concrete claims before agreeing.
3. If a branch has both agreements and a passing gate, merge it per §2.4–2.5.
4. Only then start a new batch, and claim it first.

Scheduled: Claude checks threads daily (08:52 HKT) and sweeps evidence Mondays; ChatGPT
sweeps Thursdays. Both cover all four repositories.

## 5. Automation (same workflows in all four)

- `.github/workflows/claude-reply.yml` — a push to `main` that adds a ChatGPT-headed thread
  entry (or a `chatgpt_replied` dispatch) runs Claude: verify, reply, merge if agreed.
  Secret: `ANTHROPIC_API_KEY`.
- `.github/workflows/codex-review.yml` — a `claude/*` branch create/push (or
  `claude_replied` dispatch) runs a read-only Codex review, posts it to `STATUS.md`, and
  dispatches Claude. Secret: `OPENAI_API_KEY`.
- At most three rounds per side per branch. A green workflow is a precondition for merging,
  never agreement.
- The survey repo additionally has `survey-event-alerts.yml` (maintainer notifications) and
  `rebuild-pending-sweep.yml` (PDF rebuild); the other three have build CI where it exists
  (`choreo/test.yml`, `agentic-compiler/e2e.yml`).

## 6. Status of the rollout (2026-10-22)

| Repo | AGENTS.md | STATUS.md | Workflows | Secrets set |
|---|---|---|---|---|
| ai-compiler-survey | yes (since Oct 15) | live thread | yes | yes |
| lintel | yes | bootstrap entry | yes | **maintainer to add** |
| choreo | yes | bootstrap entry | yes | **maintainer to add** |
| agentic-compiler | yes | bootstrap entry | yes | **maintainer to add** |

Until the secrets exist on a repository, its workflows will fail at the key check and the
debate there runs by hand: each agent reads and writes `STATUS.md` on its own schedule.
