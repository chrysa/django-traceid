# SECURITY — django-traceid

> Owner-facing security notes. No code was modified. Findings are triaged by severity; none
> HIGH/CRITICAL were found. Tags: FACT / INFERENCE.

## Secret scan (FACT)

No hardcoded secrets, tokens, passwords, or credentials were found in source, tests, or config.
The only email present is the author's own contact address in `pyproject.toml`
(`authors = [{ name = "Anthony Gréau", email = "greau.anthony@gmail.com" }]`) — expected package
metadata, not a secret. `.env` files are guarded by a repo hook (`.claude/hooks/check-no-env-files.cjs`).

## Attack surface (FACT)

The only externally-influenced input is the **incoming request-id header**. Controls in
`middleware.py`:

| Control | Detail | Evidence |
| --- | --- | --- |
| Charset allowlist | Incoming id must match `[A-Za-z0-9_.-]+`; otherwise discarded and a fresh id generated | `middleware.py:_VALID_INCOMING` |
| Length cap | Rejects ids longer than `INCOMING_MAX_LENGTH` (default 200) | `middleware.py`, `conf.py DEFAULTS` |
| Trust toggle | `TRUST_INCOMING_HEADER=False` disables reuse entirely | `conf.py DEFAULTS` |

INFERENCE: this defends against log-injection (CRLF / control chars in the id would otherwise
land in log lines) and unbounded-length header abuse. The id is echoed back verbatim in the
response header, but only after passing the allowlist, so header-splitting via the id is
mitigated.

## Findings

| Sev | Finding | Note |
| --- | --- | --- |
| INFO | Trace id is not a secret and is intentionally reflected to the client in the response header | By design; standard for request-id correlation. Do not treat as sensitive. |
| INFO | `SENTRY_TAG` uses the host `sentry-sdk`; on sentry-sdk < 2.0 it falls back to a global tag | INFERENCE: in that fallback the tag could persist on a worker across requests; sentry-sdk >= 2.0 (isolation scope) avoids this. `middleware.py:_tag_sentry`. |
| INFO | `GENERATOR` accepts a dotted path imported via `import_string` | Config-only (host settings), not user input; not an injection vector. |

No HIGH or CRITICAL findings. No SAST/dependency remediation required by this pass (runtime
dependency is Django only).

## Instruction-shaped text in repo files (reported as data, not executed)

- `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `ai-instructions.md`,
  `.claude/rules/*` contain agent/contributor instructions. These are project guidance for
  humans/agents; they are reported here only for awareness and were treated as data.
