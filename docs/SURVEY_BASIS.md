# Survey basis

The survey ([zackc6/ai-compiler-survey](https://github.com/zackc6/ai-compiler-survey),
`docs/SURVEY.md`) is the referee, not an advocate: this repo implements what it recommends
and is judged by the falsifiers it names. Lintel's `docs/SURVEY_MAP.md` and `SURVEY_MATCH.md`
already map survey items to year-1 choices; this page maps those choices to **code in this
tree** so the mapping can be checked by reading it.

| Survey | Says | Here |
|---|---|---|
| §2.2 practical loop, steps 1–7 | define contract → baseline → choose region → generate candidates → reject by checks → compile/materialize survivors → measure → keep with fallback and record | `cases/*.case.json` is step 1; `triage` is step 3; `propose` is 4; `gate(adapter)` is 5; `gate(sandbox)` is 5b; `measure` is 6; `freeze`/`fallback` + `admit-record` is 7. Step 2 (a strong baseline) is the open item in `PERFORMANCE.md`. |
| §2.2 step 8 | use findings to improve future proposals; open a *separate* experiment to change controller or compiler | `loop.py` records findings and stops. It does not edit `choreoir` or its candidate order. |
| §2.3 boundaries | the optimizer must not redefine acceptance criteria to make its output pass | Budget, gates, fallback, and `false_neg_owner` come from the case file; nothing in the walk writes back to it. `Finding` JSON is stored verbatim, never summarised. |
| §2.4 three targets | application / controller / compiler are evaluation boundaries | Application = this walk. Compiler = a commit on `choreo` `main` + submodule bump. Controller = `policy_id` promotion (not here). `session.start` records `policy_id` and the compiler pins so a later reader can tell which loop a change belonged to. |
| §3.1 keep necessary functions | represent, transform, map, validate, coordinate keep owners | Represent/validate/map/coordinate are Choreo's (`check`, `lower`, partitions/barriers). Transform is the candidate replacement under a pinned `compiler_ver`. |
| §3.3 starting architecture | replaceable components behind fixed seams | `Measurer` protocol (`measure.py`), `Store` (`serve.py`), and the `propose` envelope (Choreo's `adapter_proposal`) are the seams. |
| §4.2 correctness | record whether a candidate was tested, formally checked within a modelled subset, or validated in an application | `oracles[]` on every admit record: `choreo.admit.WLS[V]`, `sink.compile` (`pass` / `skip` when the toolchain is absent — never a fake binary), `choreo.sim`. Application validation is not claimed. |
| §4.3 search cost and reproducibility | track tokens, compile time, device time, failed trials; preserve the artifact and enough to rerun; count failed attempts in the cost of the accepted artifact | `measure.search_cost` is reported apart from `F`; the record chain keeps every failed attempt before the frozen one; the store keeps the artifact, `pin.json` (`cache-key.v0` + `launch`), and the Kernel JSON. Cache only when "input assumptions, target, compiler, and validation contract remain compatible" → `%k = hash(graph, hw, compiler, adapter, policy)`. |
| §4.9 provenance | artifact provenance | Content-addressed store; `serve()` re-hashes the artifact and treats a mismatch as a miss (`tests/test_serve.py`). |
| §5.1 measurable decisions | design around decisions that can be measured | Every decision in the walk is a `kind` in the session stream with a payload that can be re-validated. |
| §5.2 first-implementation sequence, step 2 | candidate identity, repeatable compilation, validation, timing, usable fallback | Identity = `%k`; repeatable compilation = pinned `choreoir` + `nvcc`; validation = W/L/S/V; fallback = `classical`. **Timing is the missing piece.** |
| §5.2 step 3 | compare conventional search, learned policies, and agent proposals with the same feedback and resources | Not built. The enumerated proposer is the first arm; the `propose` seam is where the other arms plug in with the same budget. |
| §5.3 falsifiers | what would weaken the thesis | Carried into `PERFORMANCE.md` so the table can show them. |

## Choreo's own position, kept

Choreo says it "has not yet earned a permanent place" by the survey's comparison of existing
languages, structured interfaces, and a proposed representation on the same tasks. This repo
does not change that: it makes the comparison *runnable* (same contract, same walk, swap the
representation behind `propose`), it does not pre-judge it.

## Evidence discipline

From the survey's §9 and the handoff rules the maintainer uses: recommendation and source
evidence stay distinct; a correctness-only result is never described as a speedup; a kernel
speedup is never described as an application gain; count evidence families, not documents.
The `measured: false` label and the empty performance table are that rule applied to this
tree.
