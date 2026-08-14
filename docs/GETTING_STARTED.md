# Installation and Running the Application

## Prerequisites

- Windows PowerShell;
- Python 3.10 or later;
- network access for the initial package installation;
- optional Azure OpenAI or OpenAI-compatible credentials for live mode.

Run all commands from the project root:

```powershell
Set-Location C:\sonali\POC\Smart-Backlog-Assistant
```

## Install packages

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the application and development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The editable installation exposes both:

- `smart-backlog`, the command-line entry point;
- `python -m smart_backlog_assistant`, the package entry point.

## Run offline mode

Offline mode requires no AI credentials. It executes all five agent stages with
their request-bound deterministic tools and records each call as a fallback
execution.

```powershell
smart-backlog data\meeting_notes.txt `
  --backlog data\existing_backlog.json `
  --output output\meeting `
  --mode offline
```

Equivalent package command:

```powershell
python -m smart_backlog_assistant data\meeting_notes.txt `
  --backlog data\existing_backlog.json `
  --output output\meeting `
  --mode offline
```

The command writes:

```text
output\meeting\backlog_proposal.json
output\meeting\backlog_proposal.md
```

## Run live AI mode

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure either Azure OpenAI:

```text
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_CHAT_MODEL=<deployment-name>
AZURE_OPENAI_API_VERSION=preview
```

Or an OpenAI-compatible provider:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=<model-name>
OPENAI_BASE_URL=
```

Then run:

```powershell
smart-backlog data\bicep_requirements.txt `
  --backlog data\existing_backlog.json `
  --output output\live\bicep `
  --mode live
```

Each Agent Framework agent receives its assigned callable tool. If a model call
fails or omits the required call, the workflow executes the deterministic tool
and records fallback use. Final proposal validation always runs before output
is written.

Live results are kept under `output\live` so they do not overwrite the
deterministic reference outputs.

## Automatic mode

`--mode auto` uses live AI when valid provider settings are available and
otherwise uses the offline deterministic flow:

```powershell
smart-backlog data\proposed_pipeline_requirement.txt `
  --backlog data\existing_backlog.json `
  --output output\pipeline `
  --mode auto
```

## Run another sample

Choose a source from `data\backlog_requests_sample.csv`, then use its
`source_file`, `backlog_file`, and `output_directory` columns:

```powershell
smart-backlog data\proposed_modernization_extension.txt `
  --backlog data\existing_backlog.json `
  --output output\modernization `
  --mode offline
```

## Run all sample scenarios

Run all six scenarios in live mode:

```powershell
$scenarios = @(
  @('meeting_notes.txt', 'meeting'),
  @('bicep_requirements.txt', 'bicep'),
  @('proposed_modernization_extension.txt', 'modernization'),
  @('proposed_pipeline_requirement.txt', 'pipeline'),
  @('security_requirements.txt', 'security'),
  @('platform_requirements.txt', 'platform')
)

foreach ($scenario in $scenarios) {
  smart-backlog (Join-Path 'data' $scenario[0]) `
    --backlog data\existing_backlog.json `
    --output (Join-Path 'output\live' $scenario[1]) `
    --mode live
}
```

For deterministic execution without model calls, change `--mode live` to
`--mode offline` and change the output base from `output\live` to `output`.

## Run tests

```powershell
python -m pytest
```

The tests cover input loading, prompt contracts, all five required tool calls,
guardrails, source grounding, backlog immutability, output traceability, and
the CSV request manifest.

## Log files

Every CLI run writes terminal output and a persistent rotating log:

```text
logs\smart_backlog_assistant.log
```

Rotated backups use names such as:

```text
logs\smart_backlog_assistant.log.1
logs\smart_backlog_assistant.log.2
```

The defaults can be changed in `.env`:

```text
LOG_FILE=logs/smart_backlog_assistant.log
LOG_MAX_BYTES=1048576
LOG_BACKUP_COUNT=3
```

Each workflow writes a safe process trail containing:

- workflow start and completion;
- correlation identifier and execution mode;
- all five ordered agent steps;
- assigned tool and exactly-once call count;
- model or fallback execution;
- stage and workflow duration;
- requirement, match, gap, story, and validation counts;
- validation failures and written output paths.

Source text, model responses, tool payloads, and provider credentials are not
written to the application log.

## Command help

```powershell
smart-backlog --help
```

Use `--verbose` to enable application debug logging. Verbose logs are written
to both the terminal and configured log file.
