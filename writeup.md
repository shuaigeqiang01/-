# Week 7 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## Instructions

Fill out all of the `TODO`s in this file.

## Submission Details

Name: **李凯强** \
SUNet ID: **likq** \
Citations: **None**

This assignment took me about **5** hours to do.


## Task 1: Add more endpoints and validations
a. Links to relevant commits/issues
> Branch: `task-1-add-endpoints-and-validations`
> Commit: `dab8e2a` — Add DELETE endpoints, GET single action item, and input validation
> PR: https://github.com/shuaigeqiang01/-/pull/5

b. PR Description
> **Problem**: The API was missing DELETE endpoints for notes and action items, a GET single action item endpoint, and input validation allowed empty strings.
>
> **Approach**: Added `DELETE /notes/{id}` and `DELETE /action-items/{id}` (both return 204 with 404 for missing resources). Added `GET /action-items/{id}` which was entirely missing. Added `Field(min_length=1)` validation to all Pydantic Create/Patch schemas, and `max_length=200` on `Note.title` matching the DB column. Added delete buttons to the frontend for both resources.
>
> **Testing**: Ran `pytest -q backend/tests` — 10 tests passed. New tests cover: DELETE success (204) → subsequent GET returns 404, POST with empty strings → 422, PATCH with empty strings → 422, GET nonexistent resource → 404. Fixed Windows `PermissionError` in conftest.py teardown by catching PermissionError on os.unlink.
>
> **Tradeoffs/Limitations**: No PUT (full replace) endpoints — PATCH is sufficient for partial updates. The conftest.py fix catches all PermissionError which is coarse but pragmatic for Windows temp file locking.

c. Graphite Diamond generated code review
> **TODO** — Create PR on Graphite, run Diamond review, paste results here

**Manual review notes**:
- All new endpoints follow existing patterns (same error handling, same response shapes)
- `Field(min_length=1)` catches empty strings at the Pydantic layer before hitting the DB
- Delete buttons added consistently for both notes and action items in the frontend
- `skip` param had no `ge=0` constraint — deferred to Task 4


## Task 2: Extend extraction logic
a. Links to relevant commits/issues
> Branch: `task-2-extend-extraction-logic`
> Commit: `967d020` — Enhance action item extraction with structured output and more patterns
> PR: https://github.com/shuaigeqiang01/-/pull/6

b. PR Description
> **Problem**: The extraction service only recognized `TODO:` and `ACTION:` prefixes, returned plain strings, had no priority/category metadata, and was not exposed via an API endpoint.
>
> **Approach**: Rewrote `extract_action_items()` to return structured dicts `{text, category, priority}`. Added 7 category regex patterns (TODO, ACTION, FIXME, HACK, BUG, NOTE, IMPORTANT). Added markdown checkbox detection (`- [ ]`, `- [x]`). Added priority detection: lines ending with `!` or containing URGENT/CRITICAL/P0 are classified as `high` priority. Added `POST /extract/` API endpoint accepting `{"text": "..."}`. Strips bullet prefixes (`- * +`) from display text while preserving checkbox syntax.
>
> **Testing**: 6 tests covering: original patterns (TODO/ACTION/!-suffix) still work with new return format; new prefixes (FIXME, NOTE, BUG); markdown checkboxes including checked `[x]`; priority classification (URGENT → high, !-suffix → high); empty input returning []; plain lines returning [].
>
> **Tradeoffs/Limitations**: Bullet-prefix stripping handles `- item` and `* item` but not nested bullets. Priority is keyword-based and doesn't handle semantic urgency. The return type changed from `list[str]` to `list[dict]` but no callers outside tests were affected.

c. Graphite Diamond generated code review
> **TODO** — Create PR on Graphite, run Diamond review, paste results here

**Manual review notes**:
- Changed return type from `list[str]` to `list[dict]` — verified no callers outside tests were broken
- Checkbox regex iteration: needed to handle the interplay between bullet-prefix stripping and checkbox pattern matching (checkboxes start with `- [ ]` which gets stripped unless handled carefully)
- The `_classify_line` helper keeps the classification logic testable in isolation
- Priority markers `!!` and `P0` are standard conventions, appropriately chosen


## Task 3: Try adding a new model and relationships
a. Links to relevant commits/issues
> Branch: `task-3-add-model-and-relationships`
> Commit: `0cd1b59` — Add Project model with one-to-many relationships to Notes and ActionItems
> PR: https://github.com/shuaigeqiang01/-/pull/7

b. PR Description
> **Problem**: Notes and ActionItems existed in isolation with no grouping or organizational structure. No way to scope related items together.
>
> **Approach**: Added a `Project` model (id, name, description, timestamps) with one-to-many relationships to Note and ActionItem via nullable `project_id` foreign keys. Used `cascade="all, delete-orphan"` so deleting a project cascades to its children. Added full CRUD at `/projects/`, nested routes `/projects/{id}/notes` and `/projects/{id}/action-items` with pagination. Updated existing Note and ActionItem list/create/patch endpoints to accept optional `project_id` field. Added filter by `project_id` on list endpoints. Added Projects section to frontend with add/delete UI; notes and action items display their project affiliation.
>
> **Testing**: 5 new tests: full CRUD lifecycle for projects; relationship creation and retrieval via nested routes; filtering notes/action-items by project_id; cascade delete (project deletion removes associated notes/action-items); validation (empty name → 422, nonexistent project → 404). Full suite at 20 tests total.
>
> **Tradeoffs/Limitations**: FK is nullable for backward compatibility with existing seed data. Nested routes support pagination but not sorting (consistent with how they're scoped to a single project). Frontend shows `[project #N]` label on associated items but doesn't provide a dropdown to select project when creating items — minor UX gap.

c. Graphite Diamond generated code review

Only show comments triggered bycustom rules
￼
Graphite · 40m ago
Logic bug
￼
20
+    
name = Column(String(200), nullable=False)
21
+    
description = Column(Text, default="")
22
+
23
+    
notes = relationship("Note", back_populates="project", cascade="all, delete-orphan")
24
+    
action_items = relationship("ActionItem", back_populates="project", cascade="all, delete-orphan")
Using cascade="all, delete-orphan" with nullable foreign keys is dangerous. When a user sets project_id=None on a Note or ActionItem (to unlink it from a project), SQLAlchemy will DELETE the record entirely instead of just clearing the foreign key. This will cause unintended data loss.
# Change to:
notes = relationship("Note", back_populates="project", cascade="all, delete"
)
action_items = relationship("ActionItem", back_populates="project", cascade="all, delete")
The delete-orphan should only be used when the relationship is required (non-nullable FK) and children cannot exist independently.
    notes = relationship("Note", back_populates="project", cascade="all, delete"
)
    action_items = relationship("ActionItem", back_populates="project", cascade="all, delete"
)
Spotted by Graphite
View comment in - #7

**Manual review notes**:
- Cascade delete is correctly configured with `delete-orphan` — verified in tests
- FK column uses `nullable=True` (backward compatible with existing seed data and existing records)
- `Project.description` defaults to `""` in both model (`default=""`) and schema (`description: str = ""`) — consistent
- Frontend project display is informational only (no project selection during creation) — UX could be improved


## Task 4: Improve tests for pagination and sorting
a. Links to relevant commits/issues
> Branch: `task-4-improve-pagination-sorting-tests`
> Commit: `8d693d9` — Add comprehensive pagination and sorting tests across all endpoints
> PR: https://github.com/shuaigeqiang01/-/pull/8

b. PR Description
> **Problem**: Pagination and sorting had minimal test coverage — basic skip/limit params were tested incidentally in CRUD tests but edge cases (zero limit, negative skip, invalid sort fields, boundary values, nested route pagination) were entirely untested. Moreover, skip/limit params lacked `ge=0` validation, silently accepting negative values.
>
> **Approach**: Added 14 dedicated tests in `test_pagination_sorting.py` covering all three resources (notes, action_items, projects):
> - Pagination: skip/limit across pages, out-of-range skip returns empty, limit=0 returns empty, limit=201 returns 422, skip=-1 returns 422
> - Sorting: ascending by name/title, descending with `-` prefix, invalid field falls back to `-created_at`, default sort is `-created_at`
> - Nested routes: `/projects/{id}/notes` and `/projects/{id}/action-items` pagination
> - Also added `ge=0` validation to skip/limit Query params in all three routers (notes, action_items, projects) — 6 list endpoints total
>
> **Testing**: 14 new tests + 20 existing = 34 total. All pass with `pytest -q backend/tests`.
>
> **Tradeoffs/Limitations**: The `ge=0` fix changes API behavior for negative skip/limit (now returns 422 instead of silently succeeding with default behavior). This is technically a breaking change but practically correct — negative pagination params have no valid use case.

c. Graphite Diamond generated code review
> **TODO** — Create PR on Graphite, run Diamond review, paste results here

**Manual review notes**:
- The `_seed_items` helper initially called `.format(i=i)` on all template values including ints (project_id) — fixed with `isinstance(v, str)` guard
- `limit=0` returning empty is important for frontend edge cases (empty lists instead of errors)
- Invalid sort field fallback to `-created_at` is tested explicitly across all three resource types
- `ge=0` validation was applied consistently across all 6 list endpoints in 3 routers (notes, action_items, projects, plus nested routes)


## Brief Reflection
a. The types of comments you typically made in your manual reviews (e.g., correctness, performance, security, naming, test gaps, API shape, UX, docs).
> My manual reviews focused on:
> - **Correctness**: Verifying cascade delete behavior, nullability of foreign keys, validation edge cases (empty strings, out-of-range pagination), Windows-specific file locking issues
> - **API Shape**: Consistency of response codes (204 for delete, 422 for validation), REST convention adherence (PATCH vs PUT), identifying missing endpoints (GET single action item in Task 1)
> - **Naming**: Consistent use of `{resource}_id` for path parameters, `project_id` for foreign key fields, function naming matching existing patterns
> - **Test gaps**: Identifying untested scenarios (pagination boundaries in Task 4), missing validation constraints (`ge=0` on skip/limit), uncovered edge cases (markdown checkboxes with bullet prefixes)
> - **UX**: Frontend missing project selector when creating items (Task 3), needing delete buttons for both resources (Task 1), consistent button placement
> - **Backward compatibility**: Whether schema changes (nullable FKs) and return type changes (list[str] → list[dict]) break existing consumers

b. A comparison of **your** comments vs. **Graphite's** AI-generated comments for each PR.

**Task 1 (Add endpoints and validations):**
> **My comments**: Focused on correctness of new endpoints (204/404 semantics), validation coverage (empty strings caught by Pydantic), and frontend consistency (delete buttons on both resources). I flagged that `skip` param lacked `ge=0` (deferred to Task 4). I noted the conftest.py PermissionError fix was coarse.
>
> **Graphite Diamond**: **TODO** — Paste Diamond review results here after running on the PR
> Expected areas Diamond might flag: the `except PermissionError: pass` being too broad; missing tests for title > 200 chars boundary; the `db.delete()` without explicit `db.flush()` being inconsistent with create/patch which use `db.flush()` + `db.refresh()`.
>
> **Comparison**: **TODO** — Did Diamond catch things you missed? Did you catch things Diamond missed?

**Task 2 (Extend extraction logic):**
> **My comments**: Focused on the regex patterns being correct, the checkbox regex interplay with bullet stripping (iterated 3 times to fix), priority marker conventions, and the return type change's backward compatibility. I noted that nested bullets aren't handled.
>
> **Graphite Diamond**: **TODO** — Paste Diamond review results here after running on the PR
> Expected areas Diamond might flag: the `CATEGORY_PREFIXES` dict using `re.compile` at module level (import-time cost); missing test for lines with both a prefix AND ending with `!`; the `_classify_line` function's nested if-elif chain being less extensible.
>
> **Comparison**: **TODO**

**Task 3 (Add Project model and relationships):**
> **My comments**: Focused on cascade delete correctness, FK nullability for backward compatibility, consistent defaults (`description=""` in both model and schema), and the frontend UX gap (no project selector when creating items).
>
> **Graphite Diamond**: **TODO** — Paste Diamond review results here after running on the PR
> Expected areas Diamond might flag: `project_id` in NotePatch/ActionItemPatch should validate the referenced project exists; cascade delete-orphan might leave dangling references if FK is set to None instead of deleting; the nested routes could benefit from including project name in response.
>
> **Comparison**: **TODO**

**Task 4 (Improve pagination and sorting tests):**
> **My comments**: Found the `_seed_items` bug (`.format()` on int values), verified `ge=0` applied consistently across all routers, confirmed the invalid sort field fallback behavior matched the implementation.
>
> **Graphite Diamond**: **TODO** — Paste Diamond review results here after running on the PR
> Expected areas Diamond might flag: the `ge=0` on skip should also apply to the nested route endpoints (it does, but worth verifying); tests could also cover sorting by `updated_at` and `id` fields; could suggest testing concurrent pagination (multiple requests interleaved).
>
> **Comparison**: **TODO**

c. When the AI reviews were better/worse than yours (cite specific examples)
> **TODO** — After running Graphite Diamond, provide specific examples. Use this framework:

**Where AI tends to be better:**
> - Mechanical consistency checks (e.g., "you used `db.flush()` in create but not in delete" — a human might miss pattern inconsistencies across 50+ lines of code)
> - Suggesting missing test cases (e.g., "no test for title exceeding 200 characters" — AI systematically checks boundary coverage)
> - Type/system-level issues (e.g., "this function returns `list[dict]` but the docstring still says `list[str]`")

**Where human review tends to be better:**
> - Domain judgment (e.g., "Project is the right abstraction here, not Tag, because the assignment context suggests hierarchical organization" — AI lacks assignment context)
> - UX tradeoffs (e.g., "not adding a project dropdown to the note form is acceptable because this is a starter app, not a production tool")
> - Intentional simplifications (e.g., "we intentionally don't validate that `project_id` references a real project in PATCH, because it adds complexity without clear benefit for this codebase size")

**Specific examples from this assignment:**
> **TODO** — Cite 2-3 concrete examples after running Diamond

d. Your comfort level trusting AI reviews going forward and any heuristics for when to rely on them.

**My current comfort level**: After implementing 4 tasks with an AI coding tool and doing line-by-line manual review, I find that AI-generated code is generally structurally correct but needs human verification for:

**I would trust AI reviews for:**
> - Missing validation and boundary conditions (e.g., `min_length=1`, `ge=0` on Query params)
> - Inconsistent patterns across files (e.g., one router using `db.flush()` and another not)
> - Missing test coverage for obvious edge cases (empty input, 404 responses, 422 responses)
> - Simple bugs like calling `.format()` on non-string values
> - Naming convention violations and docstring accuracy

**I would always double-check:**
> - Architectural decisions (e.g., "should this be a new model or a field on an existing model?")
> - Security implications (e.g., "does this endpoint expose data from other users?")
> - Business logic correctness (e.g., "should deleting a project cascade-delete its items or orphan them?")
> - Assignment-specific constraints (e.g., "does this follow the 1-shot prompt requirement?")

**Personal heuristic:**
> "I would use AI reviews as a first-pass filter for mechanical issues — validation gaps, missing tests, pattern inconsistencies. For any feedback touching architecture, domain modeling, or security, I would treat the AI comment as a prompt for my own investigation, not as a directive. If an AI review flags something I hadn't considered, I don't immediately change the code — I first ask whether the change aligns with the design intent and assignment constraints."
