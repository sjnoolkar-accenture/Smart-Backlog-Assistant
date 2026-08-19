# CLI Contract

## Command

```powershell
smart-backlog <source> --backlog <backlog-json> `
  [--output <directory>] [--mode <mode>] [--verbose]
```

## Arguments

| Argument | Required | Values | Behavior |
|---|---:|---|---|
| `source` | Yes | Existing `.txt`, `.md`, or `.pdf` path | Requirement evidence |
| `--backlog` | Yes | Existing valid JSON path | Read-only backlog input |
| `--output` | No | Directory path | Defaults to `output` |
| `--mode` | No | `auto`, `live`, `offline` | Defaults to `auto` |
| `--verbose` | No | Switch | Enables debug-level application logging |

## Successful Behavior

- Creates the output directory if needed.
- Writes `backlog_proposal.json`.
- Writes `backlog_proposal.md`.
- Writes safe process events to the configured rotating log.
- Does not modify the source or backlog input.

## Error Behavior

The CLI reports an error and does not write a successful proposal when:

- the source or backlog file is missing;
- the source format is unsupported or has no readable text;
- the backlog JSON is invalid;
- operational configuration is invalid;
- live mode lacks valid provider configuration;
- an unexpected OS or application input error occurs.

Expected model-stage failures may produce validated deterministic fallback
output and are recorded in review notes and logs.

## Exit and Output Boundary

The command is successful only after final proposal validation. No command
option publishes or modifies a live backlog.
