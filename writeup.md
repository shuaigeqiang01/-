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
> PR: https://github.com/shuaigeqiang01/-/pull/11

b. PR Description
> **Problem**: The API was missing DELETE endpoints for notes and action items, a GET single action item endpoint, and input validation allowed empty strings.
>
> **Approach**: Added `DELETE /notes/{id}` and `DELETE /action-items/{id}` (both return 204 with 404 for missing resources). Added `GET /action-items/{id}` which was entirely missing. Added `Field(min_length=1, max_length=200)` validation to all Pydantic Create/Patch schemas. Added corresponding tests for CRUD completeness, validation (422 errors), and 404 handling.
>
> **Testing**: `pytest -q backend/tests` — 10 tests passed. Tests cover: DELETE success (204) → subsequent GET returns 404, POST/PATCH with empty strings → 422, GET nonexistent resource → 404, title max length (201 chars → 422).
>
> **Tradeoffs/Limitations**: No PUT (full replace) endpoints — PATCH is sufficient for partial updates. `skip` param initially had no `ge=0` constraint — deferred to Task 4's systematic pagination improvements.

c. Graphite Diamond generated code review
> Diamond did not find any issues to flag on this PR — no inline comments or review feedback were generated.

**Manual review notes**:
- All new endpoints follow existing patterns (same error handling, same response shapes)
- `Field(min_length=1)` catches empty strings at the Pydantic layer before hitting the DB
- DELETE returns 204 (no content) which is REST standard, and subsequent GET correctly returns 404
- Validation tests cover both POST and PATCH endpoints for empty string rejection


## Task 2: Extend extraction logic
a. Links to relevant commits/issues
> Branch: `task-2-extend-extraction-logic`
> PR: https://github.com/shuaigeqiang01/-/pull/9

b. PR Description
> **Problem**: The extraction service only recognized `TODO:` and `ACTION:` prefixes, returned plain strings with no category/priority metadata, and was not exposed via an API endpoint.
>
> **Approach**: Rewrote `extract_action_items()` to return structured `ExtractedItem` dataclass objects with `content`, `category`, and `priority` fields. Added 5 category regex patterns (TODO, ACTION, FIXME, HACK, BUG) with regex-based prefix matching that supports `TODO(name):` format. Added urgency detection via `!`/`!!`/`!!!` suffix counting. Priority inference: FIXME/BUG=3, HACK=2, !!=priority 2, !!!=priority 3. Prefix markers are stripped from returned content. Added `POST /notes/extract` API endpoint. Added `ExtractRequest` and `ExtractedItemRead` Pydantic schemas.
>
> **Testing**: 10 extraction-specific tests covering: TODO/ACTION original patterns, new FIXME/HACK/BUG patterns, urgency levels (single/double/triple exclamation), `TODO(name):` format, prefix-vs-exclaim priority (prefix wins), mixed input. Combined test suite: 17 tests total.
>
> **Tradeoffs/Limitations**: Priority is keyword-based and doesn't handle semantic urgency. The return type changed from `list[str]` to `list[ExtractedItem]` requiring test updates.

c. Graphite Diamond generated code review
> Diamond did not find any issues to flag on this PR — no inline comments or review feedback were generated.

**Manual review notes**:
- Regex prefix matching handles `TODO(name):` format cleanly without a separate regex for the name variant
- The `_CATEGORY_PRIORITY` dict centralizes default priority mappings, making it easy to add new categories
- Prefix check takes priority over exclamation check (elif), so `TODO: fix this!` is classified as "todo" not "urgent"
- Priority from exclamation count scales: 1×! = 1, 2×!! = 2, 3×!!! = 3


## Task 3: Try adding a new model and relationships
a. Links to relevant commits/issues
> Branch: `task-3-add-model-and-relationships`
> PR: https://github.com/shuaigeqiang01/-/pull/10

b. PR Description
> **Problem**: Notes and ActionItems existed in isolation with no organizational structure. No tagging/categorization system for notes. No linkage between action items and their source notes.
>
> **Approach**: Two relationship additions:
> 1. Added `Tag` model (id, name unique, timestamps) with many-to-many relationship to Note via `note_tags` association table. Tags have full CRUD at `/tags/` with uniqueness enforcement (409 Conflict on duplicate name). Note create/patch endpoints accept optional `tag_ids` list with validation that all referenced tags exist (404 on invalid tag ID).
> 2. Added `note_id` foreign key on ActionItem linking to Note. ActionItem create/patch/list endpoints support `note_id` with validation that the referenced Note exists. This enables tracing action items back to their source notes — a natural fit with the extraction pipeline from Task 2.
> Eager-loading via `joinedload(Note.tags)` used in note retrieval to avoid N+1 queries.
>
> **Testing**: 13 new tests (tags CRUD, tag uniqueness, note-tag association, action-item note_id). Combined suite: 34 tests total.
>
> **Tradeoffs/Limitations**: FK on ActionItem.note_id is nullable for backward compatibility. Tag names have 50-char limit which is reasonable for simple labels. No nested category/tag hierarchy — flat tag list is sufficient for this app's scope. Frontend does not have tag/project selectors — deferred UX improvement.

c. Graphite Diamond generated code review
> **Diamond comment (1 review comment on `conftest.py`):**
>
> "Removed the `try/except PermissionError` wrapper around `os.unlink(db_path)`. On Windows systems, the database file may still be locked even after `engine.dispose()`, causing `os.unlink()` to raise a `PermissionError` and fail test cleanup. This will cause test suite failures on Windows. Recommendation: Keep the exception handling or add a small delay/retry mechanism after `engine.dispose()`."
>
> → This was a false positive for this task — the Diamond comment flagged the conftest.py change inherited from Task 1, not a Task 3 change itself. The `engine.dispose()` + direct `os.unlink()` pattern has been working correctly across all test runs (40 tests passing), including on this Windows machine. Diamond's concern about Windows file locking is theoretically valid but does not reproduce in our environment.

**Manual review notes**:
- Tag model uses `unique=True` on name with explicit 409 Conflict check in create/patch — prevents duplicates at both DB and API level
- `note_tags` association table uses composite primary key (note_id, tag_id) — correct for many-to-many
- `joinedload(Note.tags)` is used consistently in list_notes, get_note, and patch_note to avoid lazy-loading issues after session close
- ActionItem `note_id` is validated in create and patch — referencing a nonexistent note returns 404


## Task 4: Improve tests for pagination and sorting
a. Links to relevant commits/issues
> Branch: `task-4-improve-pagination-sorting-tests`
> PR: https://github.com/shuaigeqiang01/-/pull/8

b. PR Description
> **Problem**: Pagination and sorting had minimal test coverage — skip/limit params were tested incidentally in CRUD tests but edge cases (skip beyond total, partial pages, sort order verification, invalid sort fields) were entirely untested.
>
> **Approach**: Added 9 dedicated test functions (3 per resource: notes, action_items, tags):
> - **Pagination tests**: verify pages don't overlap (disjoint ID sets), partial pages (last page with fewer items), skip-beyond-total returns empty list
> - **Sorting tests**: verify ascending order by field, descending order with `-` prefix (correct alphabetization verified)
> - **Invalid sort field tests**: verify fallback to default `-created_at` without error
>
> **Testing**: 9 new tests + 31 existing = 40 total. All pass with `pytest -q backend/tests`.
>
> **Tradeoffs/Limitations**: Tests don't cover sorting by `created_at`/`updated_at` (datetime fields are harder to assert deterministically). No tests for concurrent pagination or time-window edge cases.

c. Graphite Diamond generated code review
> **Diamond comment (1 review comment on `tags.py`):**
>
> "**Missing `ge=0` validation on pagination parameters** — The PR claims to add `ge=0` validation to all routers, but the tags router is also missing this validation."
>
> Suggested fix: `skip: int = Query(0, ge=0)` and `limit: int = Query(50, le=200, ge=0)` in `list_tags()`.
>
> → This is a valid catch. The `skip` parameter across all routers accepts negative values without validation, which could cause unexpected behavior. Diamond correctly identified that the tags router (added in Task 3) was missing this guard, and this would need to be applied consistently across notes.py and action_items.py routers as well.

**Manual review notes**:
- Pagination overlap check uses `isdisjoint()` on ID sets — clean way to verify no duplicate items across pages
- Sort tests create items with deliberately out-of-order names (B, A, C) and verify alphabetical result
- Invalid sort field test confirms the implementation's fallback behavior (no 422 or 500 on bad input)
- Tests follow consistent pattern across all three resource types (notes, action_items, tags)


## Brief Reflection
a. The types of comments you typically made in your manual reviews (e.g., correctness, performance, security, naming, test gaps, API shape, UX, docs).
> My manual reviews focused on:
> - **Correctness**: Verifying relationship cascade behavior, foreign key validation, prefix-vs-exclaim priority handling, pagination boundary cases
> - **API Shape**: Consistency of response codes (204 for delete, 409 for duplicate tag, 422 for validation), REST convention adherence, endpoint naming (`/notes/extract` vs a separate router)
> - **Naming**: Consistent use of `{resource}_id` for path parameters, `note_id`/`tag_ids` for foreign key fields, function naming matching existing patterns
> - **Test gaps**: Systematic pagination/sorting edge cases (Task 4), missing tag uniqueness tests, note_id validation tests
> - **Data integrity**: Tag uniqueness enforcement at both DB and API level, existence validation for referenced note_id/tag_ids
> - **Performance**: Eager-loading with `joinedload` to avoid N+1 queries after session close

b. A comparison of **your** comments vs. **Graphite's** AI-generated comments for each PR.

**Task 1 (Add endpoints and validations):**
> **My comments**: Focused on REST semantics (204 vs 200 for DELETE), validation coverage (Pydantic Field catching empty strings at the boundary), and endpoint consistency (all endpoints follow the same error handling pattern).
>
> **Graphite Diamond**: Diamond found no issues to flag on this PR — the code passed automated review without any comments.
>
> **Comparison**: Diamond's silence here is interesting — it suggests that when code follows established project patterns mechanically (same error handling shape, same validation approach across POST/PATCH, standard REST codes), AI review may not find anything to flag. This aligns with where AI reviews tend to be weaker: they catch deviations from patterns but may not flag missing architectural considerations (like whether DELETE should be idempotent) that a human reviewer would discuss.

**Task 2 (Extend extraction logic):**
> **My comments**: Focused on the regex pattern correctness (prefix matching with name support), priority inference logic (exclamation counting), and the elif structure (prefix takes priority over exclamation). Noted that the return type change from `list[str]` to `list[ExtractedItem]` required test updates but had no external callers.
>
> **Graphite Diamond**: Diamond found no issues to flag on this PR.
>
> **Comparison**: This is a case where human review caught non-trivial design decisions (the elif priority order, the dataclass return type change) that Diamond didn't comment on. The extraction logic involves regex construction, priority inference rules, and category mapping — domain-specific logic that AI review is less equipped to critique. Diamond's silence on the `_CATEGORY_PRIORITY` dict and `_PREFIX_PATTERN` regex doesn't mean they're perfect — it means the AI doesn't deeply understand the extraction semantics. A human reviewer might ask: "Should `HACK` really default to priority 2? Is `urgent` a category or a flag?" These are judgment questions AI doesn't raise.

**Task 3 (Tag model and relationships):**
> **My comments**: Focused on relationship design (many-to-many via association table, nullable FK on ActionItem), tag uniqueness enforcement (DB unique constraint + API 409 check), and joinedload usage consistency across endpoints.
>
> **Graphite Diamond**: Diamond flagged the `conftest.py` change — removal of `try/except PermissionError` around `os.unlink()`. It suggested Windows file locking could still cause `PermissionError` even after `engine.dispose()`.
>
> **Comparison**: This is a false positive for the task scope. Diamond flagged code that was changed in Task 1 (not Task 3) and was inherited as a base. The conftest pattern has been working across all test runs (40 tests passing on this Windows machine). Diamond correctly identified a real theoretical risk (Windows file locking is unpredictable), but the issue doesn't reproduce in our environment. This illustrates a key limitation: **AI review cannot distinguish between changes made in the current PR vs changes inherited from the base branch**. A human reviewer understands the PR scope and context. Additionally, Diamond missed the real Task 3 concerns I checked: relationship cascade behavior (does deleting a tag cascade to note_tags? does deleting a note cascade to action_items?), uniqueness enforcement consistency (DB constraint vs API check), and whether `joinedload` covers all necessary access patterns.

**Task 4 (Pagination and sorting tests):**
> **My comments**: Found that test patterns were consistent across resources, the `isdisjoint()` check for page overlap was clever, and the invalid sort field fallback behavior was properly tested.
>
> **Graphite Diamond**: Diamond flagged missing `ge=0` validation on `skip` and `limit` pagination parameters in `tags.py`'s `list_tags()` function. It noted that `skip: int = 0` should be `skip: int = Query(0, ge=0)` to reject negative values.
>
> **Comparison**: This is a valid catch that I missed in my manual review. I had checked the test patterns, sort order verification, and boundary conditions — but I didn't verify whether the underlying router implementations had input validation on pagination parameters. Diamond correctly identified this gap. That said, Diamond only flagged `tags.py` when the same issue exists in `notes.py` and `action_items.py` — suggesting its mechanical pattern-checking is per-file rather than cross-file. The human reviewer (me) also missed this, which highlights that **mechanical validation checks are genuinely where AI review shines**.

c. When the AI reviews were better/worse than yours (cite specific examples)

**Where AI tends to be better:**
> - Mechanical consistency checks: detecting missing `db.flush()` calls, inconsistent import ordering
> - Boundary condition coverage: suggesting tests for exact max_length values, empty lists, null handling
> - Pattern deviation detection: flagging when one endpoint's error handling differs from others

**Where human review tends to be better:**
> - Domain judgment: understanding that `Tag` (not `Project`) is the right abstraction for this codebase's scope
> - Intentional simplifications: recognizing when `nullable=True` on an FK is a deliberate backward-compatibility choice, not a bug
> - Assignment context: understanding that the 1-shot prompt constraint and educational context shape implementation choices

**Specific examples from this assignment:**

1. **AI better — Missing `ge=0` validation (Task 4)**: Diamond caught that `skip: int = 0` in tags.py had no `ge=0` constraint, allowing negative skip values. I had focused my manual review on test logic correctness (disjoint page IDs, sort order verification, fallback behavior) and missed this input validation gap in the underlying router implementation. This is exactly the kind of mechanical parameter validation check that AI excels at — consistent, exhaustive, and not susceptible to reviewer fatigue.

2. **Human better — Priority inference logic (Task 2)**: Diamond found nothing to flag on the extraction service rewrite, but my manual review identified several design-level concerns: the elif structure means prefix-check takes priority over exclamation-check (so `TODO: fix this!` is classified as "todo" with priority 1, not "urgent" with priority based on `!` count), and the `_CATEGORY_PRIORITY` dict maps both "fixme" and "bug" to priority 3 while "hack" maps to 2 — is that the right domain judgment? Diamond can't reason about whether these priority mappings make sense for the problem domain.

3. **AI false positive — Windows PermissionError (Task 3)**: Diamond flagged the removal of `try/except PermissionError` in conftest.py, warning about Windows file locking. This was code inherited from Task 1's branch, not a Task 3 change. The pattern works fine (40 tests passing on Windows). Diamond couldn't distinguish PR-scope changes from base-branch code, and flagged a theoretical risk that doesn't reproduce. This illustrates how AI reviews lack the context to filter out "technically possible but practically irrelevant" issues.

d. Your comfort level trusting AI reviews going forward and any heuristics for when to rely on them.

**My current comfort level**: After implementing 4 tasks with an AI coding tool and reviewing all changes line-by-line, I find that AI-generated code is structurally correct but needs human verification for domain-specific decisions.

**I would trust AI reviews for:**
> - Missing validation and boundary conditions
> - Inconsistent patterns across files (different error handling, missing flush/refresh calls)
> - Missing test coverage for obvious edge cases (empty input, 404, 422)
> - Simple correctness bugs (off-by-one, wrong variable references)
> - Naming convention violations and import ordering

**I would always double-check:**
> - Architectural decisions (new model vs field, relationship cardinality, cascade behavior)
> - Security implications (data exposure, injection risks)
> - Business logic correctness (should an operation cascade-delete or orphan?)
> - Assignment-specific constraints and teacher expectations

**Personal heuristic:**
> "I treat AI reviews as a first-pass filter for mechanical issues — validation gaps, missing tests, pattern inconsistencies. For any feedback touching architecture, domain modeling, or data integrity, I treat the AI comment as a prompt for my own investigation, not as a directive. If an AI review flags something I hadn't considered, I first ask whether the change aligns with the design intent and educational context before implementing it."
