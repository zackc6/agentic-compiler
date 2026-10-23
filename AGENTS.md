# Instructions for coding agents (ChatGPT/Codex, Claude, Cursor)

This file is the briefing for any agent working in this repository. Read it fully before editing. It is one of four repositories maintained together. The ownership rules below are shared by all four; Lintel and Choreo work by the IR-increment loop (their `AGENTS.md`), this bench by the rules below, the survey by its own.

## What this repository is

**agentic-compiler** is where Lintel and Choreo run together: the application-search walk (propose → gate → measure → freeze/fallback → serve), the test-case corpus, setup, and — once a device clock exists — the performance table. Lintel and Choreo are submodules pinned by commit.

**This repo owns:** the walk, the case corpus, the drift report between the two pins, and the performance method and table.

**This repo does not own:** schema field names (Lintel); Kernel encoding and artifact kinds (Choreo); the thesis and forecasts (the survey). A contract change starts in the owner repo and reaches here as a submodule bump.

## Validation gate (must pass on the branch before a batch is argued)

```bash
./scripts/setup.sh && agentic-compiler run-all -o /tmp/walks
```

`agentic-compiler run-all` reports every case `ok` (pytest suite removed 2026-10-23; cases are illustrative walks while the IRs are being designed). A submodule bump is a batch of its own: it must re-read `docs/DRIFT.md` and say what changed in the contract.

## What a batch must say (the verdict comes first)

Every batch entry in the Review thread leads with: which survey section in `docs/SURVEY_BASIS.md` the change serves; whether any measurement is still a labelled proxy (`measured: false`) — a number may be called performance only when `docs/PERFORMANCE.md` rules are met; whether a submodule bump changes `%k`. A list of files changed without these is not a batch.

## The four repositories, and who owns what

| Repo | Role | Owns |
|---|---|---|
| [ai-compiler-survey](https://github.com/zackc6/ai-compiler-survey) | Referee. The thesis, evidence, and dated forecasts. | Whether the thesis still holds; what the evidence means. |
| [lintel](https://github.com/zackc6/lintel) | Control plane: written contract + design. | Schema field names, the three loops, kill switches. |
| [choreo](https://github.com/zackc6/choreo) | Data plane: kernel-schedule compiler. | Kernel encoding, admit findings, sinks, `compiler_ver`. |
| [agentic-compiler](https://github.com/zackc6/agentic-compiler) | Where the two run together. | The walk, the case corpus, drift report, performance table. |

The same two agents (Claude and ChatGPT/Codex) maintain all four. In every repository the maintainer (Zack) approves every merge and decides ties. Each agent's daily check covers all four `STATUS.md` files, not just the one it last edited.

Cross-repo rules:

1. **The survey is the referee, not an advocate.** Thesis and forecast changes happen only in the survey repo. A batch here that rests on a survey claim names the section. If work here produces evidence that bears on the thesis (a falsifier fired, a measured number), open a row in the **survey's** `STATUS.md` rather than arguing it here.
2. **A contract change starts in the owner repo.** Field names → Lintel. Kernel encoding, artifact kinds, `compiler_ver` → Choreo. It lands there by this protocol, then reaches agentic-compiler as a submodule-bump batch that updates `docs/DRIFT.md` in the same commit. Nobody edits a submodule's files from agentic-compiler.
3. **Three loops stay apart.** Application search (the walk) never edits the compiler; a compiler change is an IR-evolution commit on Choreo `main` with a `compiler_ver` bump; a controller change is a `policy_id` promotion with its own holdout. Say which loop a batch belongs to.
4. **Numbers keep their denominators.** A correctness-only result is not a speedup; a kernel speedup is not an application gain; a proxy labelled `measured: false` is not performance. Same evidence discipline as the survey.

## How the two agents work together here (the bench side of the IR-increment loop)

Lintel and Choreo are IR-design repositories and work by the **IR-increment loop** (their `AGENTS.md`: gap → IR change → carrier → falsifier, from a `gaps/` backlog). This repository is the **bench**: it has no IR of its own, it runs the two IRs together, and it feeds the loop one way. Maintainer's rules, 23 October 2026.

1. **The bench files gaps; it never designs.** When a walk hits a representation limit — a reject that cannot name a program point, a kernel the schedule cannot express, a decision the admit record cannot carry, a cache key that collides — the agent files a gap in the **owner** repo's `gaps/` (control-plane limits → `lintel/gaps/L-nnn`, data-plane limits → `choreo/gaps/C-nnn`), citing the case and the walk output. Filing a gap is a backlog operation and may go to the owner repo's `main` directly. The design happens there, not here.
2. **Units of work here** are three, and each is one batch on its own branch: (a) a **submodule bump** (re-read `docs/DRIFT.md`, say what changed in the contract, re-run every walk; bumps happen on a cadence — weekly, or when a versioned contract lands — not per upstream commit); (b) a **case addition** (one `*.case.json`, kernels referenced from the submodules, never copied); (c) a **measurement row** (`perf/results/*.json` written by the measurement job; an agent may not type a number — `docs/PERFORMANCE.md`).
3. **IR-design stage.** Cases are **illustrative walks**, not a correctness contract: the gate is `./scripts/setup.sh && agentic-compiler run-all -o out` with every case `ok`. The pytest suite was removed on 2026-10-23; drift between the pins is recorded in `docs/DRIFT.md` as prose and checked by the walks. Do not add test suites or generators until both IRs are decided.
4. **Parallel batches, one owner each.** The **Open batches** table at the top of `STATUS.md` holds up to three batches in flight, one row each: `batch, agent, branch, started, status`. Claim a row before editing; the other agent reviews. Branch names: `claude/<topic>-<date>` / `chatgpt/<topic>-<date>`.
5. **Thread.** Review-thread entries in `STATUS.md`, newest first, headed `**<YYYY-MM-DD HH:MM UTC> — <Agent> [<batch>]**` (ChatGPT headings must contain "ChatGPT" so the push detector fires). An entry says: which survey section in `docs/SURVEY_BASIS.md`; whether any number is still a labelled proxy; whether a bump changes `%k`; agree / object per point naming file and line; what next. **At most two rounds per side per batch.** Do not argue validation evidence: the gate run is on the branch and the maintainer sees it on the PR. At the cap, stop and hand the batch to the maintainer.
6. **The maintainer approves every merge.** On full "agree" or at the round cap, the author opens a **pull request** to `main` (title = batch summary; body = what changed, the gate run on the head SHA, the thread entries, the agreement record or the open points) and requests the maintainer's review. No auto-land, no tie-break, no deadline that merges on its own. After approval: squash to one commit; **MERGE SUMMARY** at the top of the thread (alignment with the owner contracts and the survey first, then changes, agreement record, commit hash; email recorded as pending, never sent); clear the Open-batches row; delete the branch and verify with `git ls-remote --heads origin`.
7. **Direct to `main`:** thread entries, Open-batches rows, and pure fact fixes (a wrong number, a broken link, a failing build fixed). Nothing else.
8. **Sign commits** with your agent name (`Co-Authored-By: Claude` / `Co-Authored-By: ChatGPT`).
9. **Event-driven debate.** `.github/workflows/claude-reply.yml` runs Claude (`anthropics/claude-code-action/base-action@v1`, secret `ANTHROPIC_API_KEY`) when a push to `main` adds a ChatGPT-headed Review-thread entry or on a `chatgpt_replied` dispatch. `.github/workflows/codex-review.yml` runs a read-only Codex review (`openai/codex-action@v1`, secret `OPENAI_API_KEY`) when a `claude/*` branch is created or pushed, on manual dispatch, or on a `claude_replied` dispatch; it posts to `STATUS.md` and dispatches Claude. Round cap **two** per side per batch. A workflow run is never approval.
10. **PRs are for the maintainer, not for the debate.** `main` is the only long-lived ref.
11. **Evidence flows outward.** A measured number with its denominator, or a falsifier that fired, becomes a source row in the survey's `STATUS.md` (the survey is the referee). Gaps closed or falsified upstream are confirmed here by the next bump's walks.

## What not to do

- Do not edit the other agent's stylistic choices; object in the thread, fix only facts, broken links, or failing builds.
- Do not change a contract field, a Kernel encoding, or `compiler_ver` outside the owner repo.
- Do not call a proxy a measurement, or a correctness result a speedup.
- Do not merge because a workflow passed. Green CI is a precondition, not agreement.
- Do not argue validation evidence in the thread; the gate run is on the branch and the maintainer sees it on the PR.
- Do not design an IR change here: file a gap in the owner repo's `gaps/`.
- Do not add test suites or carrier generators before both IRs are decided.
