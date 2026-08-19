[CmdletBinding()]
param(
    [string]$Feature = "001-smart-backlog-assistant"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$featureRoot = Join-Path $repoRoot "specs\$Feature"

$requiredFiles = @(
    ".specify\memory\constitution.md",
    ".specify\scripts\powershell\verify-alignment.ps1",
    "scripts\verify_alignment.py",
    "specs\$Feature\spec.md",
    "specs\$Feature\plan.md",
    "specs\$Feature\research.md",
    "specs\$Feature\data-model.md",
    "specs\$Feature\quickstart.md",
    "specs\$Feature\test-traceability.md",
    "specs\$Feature\tasks.md",
    "specs\$Feature\contracts\cli-contract.md",
    "specs\$Feature\contracts\backlog-proposal.schema.json"
)

$errors = [System.Collections.Generic.List[string]]::new()

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $errors.Add("Missing required file: $relativePath")
    }
}

if (Test-Path -LiteralPath $featureRoot -PathType Container) {
    $markdownFiles = Get-ChildItem -LiteralPath $featureRoot -Recurse `
        -File -Filter "*.md"
    $placeholderPattern = "\[(FEATURE NAME|DATE|###-feature-name)\]|" +
        "NEEDS CLARIFICATION|ACTION REQUIRED"

    foreach ($file in $markdownFiles) {
        $matches = Select-String -LiteralPath $file.FullName `
            -Pattern $placeholderPattern
        if ($matches) {
            $relativePath = [IO.Path]::GetRelativePath(
                $repoRoot,
                $file.FullName
            )
            $errors.Add("Unresolved template placeholder in $relativePath")
        }
    }

    $quickstartPath = Join-Path $featureRoot "quickstart.md"
    if (Test-Path -LiteralPath $quickstartPath) {
        $quickstart = Get-Content -LiteralPath $quickstartPath -Raw
        if ($quickstart -notmatch '```powershell') {
            $errors.Add("quickstart.md must contain PowerShell commands")
        }
        if ($quickstart -match '```bash') {
            $errors.Add("quickstart.md must not contain Bash command blocks")
        }
    }

    $schemaPath = Join-Path $featureRoot `
        "contracts\backlog-proposal.schema.json"
    if (Test-Path -LiteralPath $schemaPath) {
        try {
            Get-Content -LiteralPath $schemaPath -Raw |
                ConvertFrom-Json | Out-Null
        }
        catch {
            $errors.Add("Invalid JSON schema: $($_.Exception.Message)")
        }
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Output "Spec Kit artifacts are complete and PowerShell-compatible."
