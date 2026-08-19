[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$cli = Join-Path $repoRoot ".venv\Scripts\smart-backlog.exe"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Virtual environment not found. Create .venv and install .[dev]."
}

Push-Location $repoRoot
try {
    & (Join-Path $PSScriptRoot "validate-specs.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Spec Kit validation failed."
    }

    & $python "scripts\verify_alignment.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Specification, code, test, and report alignment failed."
    }

    & $python -m pytest
    if ($LASTEXITCODE -ne 0) {
        throw "Automated tests failed."
    }

    $smokeRoot = Join-Path $env:TEMP (
        "smart-backlog-alignment-" + [guid]::NewGuid().ToString("N")
    )
    $backlogPath = Join-Path $repoRoot "data\existing_backlog.json"
    $beforeHash = (Get-FileHash -LiteralPath $backlogPath `
        -Algorithm SHA256).Hash

    try {
        & $cli "data\meeting_notes.txt" `
            --backlog "data\existing_backlog.json" `
            --output $smokeRoot `
            --mode offline
        if ($LASTEXITCODE -ne 0) {
            throw "End-to-end smoke execution failed."
        }

        $proposalPath = Join-Path $smokeRoot "backlog_proposal.json"
        $markdownPath = Join-Path $smokeRoot "backlog_proposal.md"
        $proposal = Get-Content -LiteralPath $proposalPath -Raw |
            ConvertFrom-Json
        $afterHash = (Get-FileHash -LiteralPath $backlogPath `
            -Algorithm SHA256).Hash

        if ($beforeHash -ne $afterHash) {
            throw "Smoke execution modified the existing backlog."
        }
        if ($proposal.approval_required -ne $true) {
            throw "Smoke proposal does not require human approval."
        }
        if ($proposal.tool_invocations.Count -ne 5) {
            throw "Smoke proposal does not contain five tool records."
        }
        if (
            ($proposal.requirements |
                Where-Object { $_.source_locations.Count -eq 0 }).Count -ne 0
        ) {
            throw "Smoke proposal contains requirements without source locations."
        }
        if (-not (Test-Path -LiteralPath $markdownPath -PathType Leaf)) {
            throw "Smoke execution did not create Markdown output."
        }

        Write-Output (
            (
                "SMOKE_OK requirements={0} stories={1} tools={2} " +
                "backlog_unchanged=true"
            ) -f @(
                $proposal.requirements.Count,
                $proposal.stories.Count,
                $proposal.tool_invocations.Count
            )
        )
    }
    finally {
        if (Test-Path -LiteralPath $smokeRoot) {
            Remove-Item -LiteralPath $smokeRoot -Recurse -Force
        }
    }

    Write-Output "VERIFICATION_COMPLETE all alignment checks passed."
}
finally {
    Pop-Location
}
