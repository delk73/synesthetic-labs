---
version: v0.1.0
lastReviewed: 2025-10-01
owner: delk73
---

# Synesthetic Canon Process

This document defines the canonical workflow for evolving Synesthetic components.  
All work follows the **Spec → Audit → Patch → Repeat** loop.

---

## 1. Spec

* A **Spec** introduces or modifies functionality.  
* Must include:
  * **Purpose** — why the change exists.  
  * **Scope** — explicit features and exclusions.  
  * **Baseline / Canonical Example** — the minimal working case.  
  * **Validation & Exit Criteria** — what makes the spec “done.”  
* Specs accumulate history inline. If a document grows too long, older scopes are moved to `docs/spec_archive/` with a link back.

---

## 2. Audit

* Every Spec must be followed by an **Audit prompt** pinned to its version.  
* The audit compares **implementation, tests, and docs** against the spec.  
* Output files:
  * `meta/output/<component>_state.md` — structured audit findings.  
  * `<component>/AGENTS.md` — updated agent snapshot.  
* Audit rules:
  * **Present** = implemented + covered.  
  * **Missing** = not implemented.  
  * **Divergent** = implemented but differs in naming/behavior.  
* Audit is incomplete unless both outputs are non-empty.

---

## 3. Patch

* Patches flow **only from audit gaps.**  
* Format:
  * `"task"`, `"objective"`, `"changes"`, `"constraints"`, `"exit_criteria"`.  
* Patches must be **atomic** — touch only the files and concerns listed in the audit.  
* Exit criteria ensure:
  * Gaps are closed.  
  * Tests remain green.  
  * Docs/spec stay aligned.

---

## 4. Rolling History

* **Spec documents are living records.**  
* Each new scope increments the version (`vX.Y`).  
* Old scopes are kept inline until the file grows too long, then pruned into `docs/spec_archive/` with references.  

---

## 5. Canon Rule

Everything must flow from the Spec.  
No changes to code, tests, or docs are valid unless:  
1. A Spec defines them.  
2. An Audit identifies gaps.  
3. A Patch closes them.

---
