# PickyLens browser feasibility probe

Disposable Gemini-only Manifest V3 probe, not the full product. See RESULTS.md for the initial feasibility evidence and ROBUSTNESS.md for the follow-up blocker.

The current probe uses a deterministic local mock backend, never production Core or AI reviews. Run `python devtools/browser_spike/mock_backend.py` for the loopback endpoint on port 8033. The extension requires Gemini content-script access and http://127.0.0.1/* host permission; its worker fixes the destination to port 8033 and /probe/review. No secrets are needed.

Run `node devtools/browser_spike/lifecycle.test.cjs` for classifier checks. Reload the unpacked extension after manifest changes, then refresh Gemini. Disable the probe and refresh Gemini when finished. Do not use it for normal work: automatic completion detection has not passed robustness validation.
