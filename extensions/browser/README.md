# PickyLens for Gemini Chat — v0.1 candidate

This is the new extension, not devtools/browser_spike. Disable the old feasibility probe before loading it. Browser/live acceptance is still pending.

## Judge installation (operator-supplied HTTPS package)
1. Extract the supplied PickyLens ZIP into a permanent folder.
2. Open chrome://extensions (or edge://extensions), enable Developer mode, select Load unpacked, and select that folder.
3. Click the Chrome Extensions puzzle-piece menu, then PickyLens, to open its Judge Pass popup. Enter the bounded Judge Pass supplied by the operator. Never enter an OpenAI key.
4. Open normal gemini.google.com using your own Google account. Refresh any already-open Gemini tab.
5. Write normally. Review your request, explicitly choose any edits, or Send original anyway.
6. Once Gemini finishes, click Check this answer beside that answer. Review findings and evidence. Fix only what's missing creates a draft; placing it in the composer does not send it.
7. Disable the extension and refresh Gemini to remove its controls. Remove the pass in extension options if you no longer need it.

No CLI, Python, Node, shared Google account, or provider key is needed by judges. The source folder points to loopback for developer validation only; do not distribute it as the deployed package.

## Data and limits
Only explicit review actions send the selected request/answer to the pinned PickyLens backend and its OpenAI provider. Suggestions are not automatically accepted. Automatic answer review and automatic follow-up submission are deliberately absent. Reviews live in page memory and disappear on refresh; Web supplies the persistent full experience. Judge Pass is bounded and stored locally in extension trusted-context storage, not synced. Provider credentials remain server-side. Host DOM dependencies may change; unknown request structures are skipped rather than guessed. Wait for an answer to finish before checking; the manual check is not a claim of automatic lifecycle detection.

The service worker requires Gemini content-script access, storage, and exactly one backend origin. No cookies, browser history, tabs permission, or broad all-sites permission. The package builder replaces loopback permission with the selected HTTPS origin. Backend authentication is mandatory; host permissions are not authentication.
