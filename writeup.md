# Week 7 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## Instructions

Fill out all of the `TODO`s in this file.

## Submission Details

Name: **TODO** \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do.


## Task 1: Add more endpoints and validations
a. Links to relevant commits/issues
> Branch: `task-1-add-endpoints-and-validations`
> Commit: `dab8e2a` — Add DELETE endpoints, GET single action item, and input validation
> PR: **TODO** (create via Graphite after pushing)

b. PR Description
> **Problem**: The API was missing DELETE endpoints for notes and action items, a GET single action item endpoint, and input validation allowed empty strings.
>
> **Approach**: Added `DELETE /notes/{id}` and `DELETE /action-items/{id}` (both return 204 with 404 for missing resources). Added `GET /action-items/{id}` which was entirely missing. Added `Field(min_length=1)` validation to all Pydantic Create/Patch schemas, and `max_length=200` on `Note.title` matching the DB column.
>
> **Testing**: Ran `pytest -q backend/tests` — 10 tests passed. New tests cover: DELETE success (204) → GET returns 404, POST with empty strings → 422, PATCH with empty strings → 422, GET nonexistent resource → 404. Also fixed Windows `PermissionError` in conftest.py teardown.
>
> **Tradeoffs/Limitations**: No PUT (full replace) endpoints — PATCH is sufficient for partial updates and the frontend doesn't need full replace semantics. The `conftest.py` fix catches all `PermissionError` on cleanup which is coarse but pragmatic for Windows temp files.

c. Graphite Diamond generated code review
> **TODO** — Create PR on Graphite and run Diamond review

**Manual review notes**:
- Verified all new endpoints follow existing patterns (same error handling, same response shapes)
- Confirmed `Field(min_length=1)` catches empty strings at the Pydantic layer before hitting the DB
- Frontend delete buttons added consistently for both notes and action items
- One issue: `skip=-1` passes validation silently (no `ge=0` on Query) — deferred to Task 4


## Task 2: Extend extraction logic
a. Links to relevant commits/issues
> Branch: `task-2-extend-extraction-logic`
> Commit: `967d020` — Enhance action item extraction with structured output and more patterns
> PR: **TODO** (create via Graphite after pushing)

b. PR Description
> **Problem**: The extraction service only recognized `TODO:` and `ACTION:` prefixes, returned plain strings, and had no API endpoint.
>
> **Approach**: Rewrote `extract_action_items()` to return structured dicts `{text, category, priority}`. Added 7 category regex patterns (TODO, ACTION, FIXME, HACK, BUG, NOTE, IMPORTANT). Added markdown checkbox detection (`- [ ]`, `- [x]`). Added priority detection: lines ending with `!` or containing URGENT/CRITICAL/P0 are `high` priority. Added `POST /extract/` API endpoint. Strips bullet prefixes (`- * +`) from display text while preserving checkbox syntax.
>
> **Testing**: 6 tests covering: original patterns still work with new return format, new prefixes (FIXME, NOTE, BUG), markdown checkboxes (including checked `[x]`), priority classification, empty input, and plain text returning no items.
>
> **Tradeoffs/Limitations**: The bullet-prefix stripping uses `re.sub(r"^[-*+]\s+", "", line)` which handles `- item`, `* item`, `+ item` but not nested bullets like `  - item`. Priority detection is keyword-based and doesn't handle semantic urgency.

c. Graphite Diamond generated code review
> **TODO** — Create PR on Graphite and run Diamond review

**Manual review notes**:
- Changed return type from `list[str]` to `list[dict]` — verified no callers outside tests were broken
- Checkbox regex needed iteration to handle the interplay with bullet-prefix stripping
- The `_classify_line` helper keeps the classification logic testable in isolation
- Priority markers `!!` and `P0` are standard conventions, appropriately chosen


## Task 3: Try adding a new model and relationships
a. Links to relevant commits/issues
> Branch: `task-3-add-model-and-relationships`
> Commit: `0cd1b59` — Add Project model with one-to-many relationships to Notes and ActionItems
> PR: **TODO** (create via Graphite after pushing)

b. PR Description
> **Problem**: Notes and ActionItems existed in isolation with no grouping or organizational structure. No way to scope related items together.
>
> **Approach**: Added a `Project` model (id, name, description, timestamps) with one-to-many relationships to Note and ActionItem via nullable `project_id` foreign keys. Used `cascade="all, delete-orphan"` so deleting a project cleans up its children. Added full CRUD at `/projects/`, nested routes `/projects/{id}/notes` and `/projects/{id}/action-items`. Updated existing Note and ActionItem list/create/patch endpoints to accept optional `project_id`. Added Projects section to frontend.
>
> **Testing**: 5 tests: full CRUD lifecycle, relationship creation/retrieval, filtering by project_id, cascade delete (project deletion removes children), and validation (empty name → 422, nonexistent project → 404). Full suite at 20 tests.
>
> **Tradeoffs/Limitations**: FK is nullable for backward compatibility. Nested routes don't support sorting — could be added later. Frontend project selection for notes/action items is minimal (no dropdown to pick a project when creating items).

c. Graphite Diamond generated code review
> **TODO** — Create PR on Graphite and run Diamond review

**Manual review notes**:
- Cascade delete is correctly configured with `delete-orphan`
- Verified FK column uses `nullable=True` (backward compatible with existing seed data)
- `Project.description` defaults to `""` in both model and schema — consistent
- Frontend shows `[project #N]` label on associated items but doesn't let you set project on creation — minor UX gap


## Task 4: Improve tests for pagination and sorting
a. Links to relevant commits/issues
> Branch: `task-4-improve-pagination-sorting-tests`
> Commit: `8d693d9` — Add comprehensive pagination and sorting tests across all endpoints
> PR: **TODO** (create via Graphite after pushing)

b. PR Description
> **Problem**: Pagination and sorting had minimal test coverage — basic skip/limit params were tested incidentally in CRUD tests but edge cases (zero limit, negative skip, invalid sort fields, boundary values) were untested.
>
> **Approach**: Added 14 dedicated tests in `test_pagination_sorting.py` covering: (1) Pagination: skip/limit across pages, out-of-range skip returns empty, limit=0 returns empty, limit=201 returns 422, skip=-1 returns 422. (2) Sorting: ascending by title/name, descending with `-` prefix, invalid field falls back to `-created_at`, default sort is `-created_at`. (3) Nested route pagination: `/projects/{id}/notes` and `/projects/{id}/action-items`. Also added `ge=0` validation to skip/limit Query params in all three routers, fixing a gap where negative values were silently accepted.
>
> **Testing**: 14 new tests + 20 existing = 34 total. Verified with `pytest -q backend/tests` — all pass.
>
> **Tradeoffs/Limitations**: The `ge=0` fix changes API behavior for negative skip/limit (now 422 instead of silently succeeding), which is technically a breaking change but practically correct.

c. Graphite Diamond generated code review
> **TODO** — Create PR on Graphite and run Diamond review

**Manual review notes**:
- The `_seed_items` helper had a bug where `.format(i=i)` was called on int values (project_id) — fixed with `isinstance(v, str)` guard
- Verifying `limit=0` returns empty is important for frontend edge cases
- The invalid sort field fallback to `-created_at` is tested explicitly across all three resource types
- `ge=0` validation was applied consistently across all 6 list endpoints in 3 routers


## Brief Reflection
a. The types of comments you typically made in your manual reviews (e.g., correctness, performance, security, naming, test gaps, API shape, UX, docs).
> My manual reviews focused on:
> - **Correctness**: Verifying cascade delete behavior, nullability of foreign keys, validation edge cases (empty strings, out-of-range pagination)
> - **API Shape**: Consistency of response codes (204 for delete, 422 for validation), whether endpoints follow REST conventions (PATCH vs PUT), missing endpoints (GET single action item in Task 1)
> - **Naming**: Consistent use of `{resource}_id` for path params, `project_id` for FK fields
> - **Test gaps**: Identifying untested scenarios (Task 4 pagination boundaries), missing validation constraints (`ge=0` on skip/limit)
> - **UX**: Frontend missing project selector when creating items (Task 3), delete buttons for both resources (Task 1)
> - **Backward compatibility**: Whether schema changes (nullable FKs) and return type changes (list[str] → list[dict]) break existing consumers

b. A comparison of **your** comments vs. **Graphite's** AI-generated comments for each PR.
> **TODO** — After running Graphite Diamond on each PR, fill in this comparison.
> For each PR, note:
> - Types of issues Graphite found that you missed
> - Types of issues you found that Graphite missed
> - Whether the AI reviews were actionable and specific

c. When the AI reviews were better/worse than yours (cite specific examples)
> **TODO** — Provide specific examples from the Graphite Diamond reviews.
> Examples of where AI may excel: catching missing validation constraints, suggesting edge case tests, flagging inconsistent error message formats.
> Examples of where AI may fall short: understanding domain intent (why Project is the right abstraction vs Tag), judging UX tradeoffs, recognizing deliberate simplifications.

d. Your comfort level trusting AI reviews going forward and any heuristics for when to rely on them.
> **TODO** — Reflect on:
> - What types of feedback you'd trust from AI without verification (syntax, missing null checks, type inconsistencies)
> - What types you'd always double-check (architecture decisions, security, business logic)
> - A heuristic: "trust AI reviews for ______, but always manually verify ______"
