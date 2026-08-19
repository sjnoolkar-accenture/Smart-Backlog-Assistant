# Quickstart: Smart Backlog Assistant

The commands below are PowerShell commands and run from the repository root.

## Create the Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Run Deterministically

```powershell
smart-backlog data\meeting_notes.txt `
  --backlog data\existing_backlog.json `
  --output output\meeting `
  --mode offline
```

Expected files:

```text
output\meeting\backlog_proposal.json
output\meeting\backlog_proposal.md
logs\smart_backlog_assistant.log
```

## Run With OpenAI

Set the values in `.env` without committing secrets:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

Then run:

```powershell
smart-backlog data\meeting_notes.txt `
  --backlog data\existing_backlog.json `
  --output output\live\meeting `
  --mode live
```

## Run With Azure OpenAI

Set:

```text
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_CHAT_MODEL=...
AZURE_OPENAI_API_VERSION=preview
```

Use the same `--mode live` command.

## Run Tests

```powershell
python -m pytest
```

## Validate the Result

Confirm that:

1. JSON and Markdown outputs were created.
2. `approval_required` is `true`.
3. Five tool invocation records exist and each has `call_count` equal to one.
4. Referenced requirement and backlog identifiers exist.
5. `data\existing_backlog.json` was not modified.
