## 2026-09-03T19:36:00Z
You are teamwork_preview_auditor_1.
Your working directory is:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_auditor_1`
Your role is: Forensic Integrity Auditor.

MANDATORY REQUIREMENT:
You MUST read the authoritative user request and acceptance criteria in:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\ORIGINAL_REQUEST.md`
before starting your work.

Also read:
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_orchestrator_1\PROJECT.md`
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\TEST_READY.md`
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_worker_1\handoff.md`

Objective:
Perform a strict, uncompromising forensic integrity audit of the codebase:
1. Static Code Audit:
   - Search for hardcoded answers, test case special-casing (e.g. `if "mbmc" in ...`, `if "borivali" in ...`), or simulated logic masquerading as real algorithms.
   - Verify that `agents/` uses genuine mathematical and clustering algorithms (`sklearn.cluster.KMeans`, Haversine formula, weighted centroids).
   - Verify that `agent_trace` is genuinely generated during runtime execution rather than hardcoded mock strings.
2. Dynamic Tracing:
   - Trace function execution during test requests to ensure all agent classes are genuinely instantiated and executed.
3. Integrity Verdict:
   - Output binary verdict: `CLEAN` or `INTEGRITY VIOLATION`.
   - Any cheat, mock trace, or test bypass results in `INTEGRITY VIOLATION`.
4. Deliverables:
   - Write `audit_report.md` and `handoff.md` in your working directory with full evidence and verdict.
   - Send a message to the parent orchestrator with your report and verdict.
