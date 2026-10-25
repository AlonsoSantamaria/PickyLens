# Workspace reading polish — 2026-10-25

Authorized presentation-only exception. Not deployed to VESTA. No provider calls.

## Changes

Workspace prompts, improved/approved requests, answers, follow-up text and assessment lists are bounded. Desktop maximum uses clamp(420px,55vh,520px); narrow screens use 50vh. Short editors fit content with a 96px minimum. Headings, guidance, status counts and action buttons stay outside the reading regions. Evidence expansion stays inside the assessment list. Native scroll chaining remains enabled; only overflowing noninteractive regions receive a keyboard tab stop.

AI answer and follow-up text are rendered with locally vendored markdown-it 15.0.3. Raw HTML and images are disabled, URL schemes are restricted to HTTP(S)/mailto, and only escaped parser output reaches innerHTML. No highlighting/plugin execution. Tables have column-header semantics and independent horizontal wrappers; prose wraps. Original response text, exact evidence excerpts and stored records are unchanged. History remains unchanged as requested.

## Verification

- Full Python suite: 104 passed.
- Node checks: three Markdown/security/cache tests plus existing worker protocol suite passed.
- JavaScript syntax and Git whitespace checks passed.
- Desktop browser 1280px: long request/answer and assessment list bounded near 420px at this viewport; long answer scroll height exceeded 13,000px without expanding the page by that amount.
- Expanded evidence increased list scroll height from 1,108px to 2,385px while its visible height stayed 419px. Summary chips remained outside.
- Keyboard PageDown moved the evidence list internally.
- 390x844 browser: stacked workbench, answer bounded near 422px, no viewport overflow. Table width 471px inside its own 299px scroll wrapper; answer prose had no horizontal overflow.
- Short fixture: request height 96px, answer 51px with no excess scrollbar or extra tab stop.
- Improved-request fixture: 24 requirements and long revised prompt bounded independently.
- Full deterministic browser journey: request review, original approval, answer, POST (7 Complete / 1 Missing), NEXT, follow-up and VERIFY (8 Complete), History read-only completion, new-case orientation, pause/reload/resume.
- No executable script/image/iframe elements from hostile Markdown; browser console had no errors.

Reproduce local fixture previews with `python -m uvicorn devtools.ui_preview:app --host 127.0.0.1 --port 8011`, then visit /short, /long and /pre. This fixture server has no inference routes. Full-flow stub remains devtools.stub_app:app.

Limitations: physical touch hardware was not tested; responsive browser layout and native overflow behavior were checked. Raw HTML, embedded images, relative links and syntax highlighting are intentionally unsupported. Existing History uses its original plain-text presentation. No production deployment, extension changes, backend logic, persistence or allowance changes are included.
