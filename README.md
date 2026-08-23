# ShiftLeft.ai

An LLM-powered Quality Engineering assistant. **The goal is a full Requirements → BDD pipeline**: feed it a raw requirement (user story, BRD, Jira ticket) and get back acceptance criteria, traceable Gherkin scenarios, and runnable step-definition scaffolding for your test framework. **The project is not there yet** — it currently covers the requirements → scenarios half of that pipeline; the scenarios → runnable test code half hasn't been built.

## The problem this is meant to solve

QA teams routinely receive vague BRDs, Jira stories, or nothing but a screenshot, and are expected to produce test scenarios, test cases, and regression suites from them. In practice:

| Step | What actually happens |
| --- | --- |
| Requirements | Ambiguous, late, changing |
| Test Design | Copy-paste, human bias |
| Edge Cases | Missed |
| Traceability | Manual and painful |
| Maintenance | Extremely costly |
| Feedback Loop | Weak / delayed |

See [docs/about.md](docs/about.md) for the fuller picture.

## Where it is today

Built so far: a Streamlit app that runs a two-stage LLM pipeline with a human checkpoint in between.

1. **Story → Acceptance Criteria.** You provide a user story (typed, or extracted from an uploaded PDF/DOCX/TXT). The LLM enumerates every distinct, testable rule the story implies (happy paths, boundaries, error conditions) as `AC1, AC2, ...` items.
2. **Review.** You edit, add, or delete acceptance criteria in an editable table before the second (more expensive) LLM call runs.
3. **Acceptance Criteria → Scenarios.** The LLM converts the approved criteria into BDD scenarios — including Scenario Outlines with Examples tables for data-driven cases — returned as JSON validated against a Pydantic schema. Each scenario declares which AC id(s) it `verifies`.
4. **Coverage check + export.** The app flags any acceptance criterion left uncovered by a scenario, then renders the result as a downloadable `.feature` file (Gherkin) and a CSV of test cases.

What it does **not** do yet: generate step-definition code, validate its own Gherkin output beyond schema shape, retrieve context from existing specs/tests (RAG), or run as anything other than a local Streamlit app.

## Architecture

```
core/
  app.py             Streamlit UI and the 3-stage session-state workflow
  ingestion.py       PDF / DOCX / TXT -> plain text extraction
  llm_handler.py     Groq client wrapper; JSON-mode calls with schema-validation retries
  prompt_template.py Prompt construction for the AC stage and the scenario stage
  render.py          Feature model -> .feature (Gherkin) and -> CSV
schemas/
  gherkin.py         Pydantic models: Feature, Scenario, Step, Examples, AcceptanceCriteria
docs/
  about.md           The QA workflow problem this project addresses
  phases.txt         Phased build roadmap
```

**Stack:** Streamlit (UI) · Groq `llama-3.3-70b-versatile` (LLM, JSON mode) · Pydantic (schema validation) · PyMuPDF / python-docx (file ingestion) · uv (package management). FastAPI and Uvicorn are already dependencies but not wired up yet — reserved for the productionization phase below.

## Setup

Requires Python 3.13+.

```bash
uv sync
# or: pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

## Usage

```bash
cd core
streamlit run app.py
```

Enter a user story (or upload a PDF/DOCX/TXT), generate acceptance criteria, review/edit them, then generate scenarios. Download the result as a `.feature` file or a CSV of test cases.

## Roadmap toward the Requirements → BDD pipeline

The project is deliberately built in phases, each adding a distinct engineering capability rather than just more LLM wrapping. Branch names track phases directly; full detail in [docs/phases.txt](docs/phases.txt).

- [x] **Phase 0 — Working demo** (`core/initial-setup`). Streamlit UI, file ingestion, story → Gherkin, end-to-end demoable.
- [x] **Phase 1 — Structured output** (`phase1/schema-validated-gherkin`). LLM output validated against Pydantic schemas instead of string-matching; reliable `.feature` / CSV export.
- **Phase 2 — Pipeline + step definitions.** Requirement → feature → generated step-definition stubs for a chosen framework (pytest-bdd / behave / cucumber-js) — the piece that actually closes the "Requirements → BDD" loop, since everything before it stops at human-readable Gherkin.
  - [x] `phase2/step-def-convert`: combined the Story → AC → Scenario flow into one pipeline with a human review checkpoint and AC-to-scenario traceability (the `verifies` field).
  - [ ] `phase3/Basic-StepDef-convert` *(current branch, in progress)*: generate step-definition stubs from the approved scenarios.
- [ ] **Phase 3 — Quality / evaluation layer** *(not yet started)*. Gherkin syntax validation (actually parse output, don't just trust the schema), coverage analysis (functional / negative / edge / boundary, not just happy paths), and an eval harness (LLM-as-judge scoring of scenario completeness).
- [ ] **Phase 4 — RAG / real context** *(not yet started)*. Ingest PRDs, OpenAPI specs, or an existing test suite; retrieve relevant context so generated scenarios don't duplicate what already exists and stay consistent with real API contracts.

A prior "productionize" phase (FastAPI backend, auth, deployment) was dropped from scope.
