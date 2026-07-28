<#
.SYNOPSIS
    ECMS foundation verification gate (Master Prompt Section 109 / Section 111).

.DESCRIPTION
    Runs the complete static and structural verification suite for the ECMS
    enterprise foundation and reports a single pass/fail summary. Core language
    gates (lint, format, type-check, tests) are always enforced. Infrastructure
    validators (kubeconform, helm, terraform, docker) and the documentation build
    are enforced when their tools are available and skipped with a warning when
    they are not, so the script runs both locally and in CI.

.PARAMETER SkipDocker
    Skip the backend Docker image build even when Docker is available.

.EXAMPLE
    pwsh ./scripts/verify.ps1

.EXAMPLE
    pwsh ./scripts/verify.ps1 -SkipDocker
#>
[CmdletBinding()]
param(
    [switch]$SkipDocker
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot 'backend'
$ToolsDir = Join-Path $RepoRoot '.tools'

$script:Results = [System.Collections.Generic.List[object]]::new()

function Resolve-Tool {
    param([string]$Name, [string]$LocalPath)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    if ($LocalPath -and (Test-Path $LocalPath)) { return $LocalPath }
    return $null
}

function Invoke-Gate {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Action,
        [switch]$Optional,
        [string]$SkipReason
    )
    if ($SkipReason) {
        Write-Host "SKIP  $Name — $SkipReason" -ForegroundColor Yellow
        $script:Results.Add([pscustomobject]@{ Gate = $Name; Status = 'SKIP' })
        return
    }
    Write-Host "RUN   $Name" -ForegroundColor Cyan
    try {
        & $Action
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            throw "$Name exited with code $LASTEXITCODE"
        }
        Write-Host "PASS  $Name" -ForegroundColor Green
        $script:Results.Add([pscustomobject]@{ Gate = $Name; Status = 'PASS' })
    }
    catch {
        Write-Host "FAIL  $Name — $($_.Exception.Message)" -ForegroundColor Red
        $status = if ($Optional) { 'WARN' } else { 'FAIL' }
        $script:Results.Add([pscustomobject]@{ Gate = $Name; Status = $status })
    }
}

Write-Host "== ECMS Foundation Verification Gate ==" -ForegroundColor Magenta
Write-Host "Repo: $RepoRoot"

# --- Core language gates (always enforced) ---
Push-Location $BackendDir
try {
    Invoke-Gate 'ruff lint'      { uv run ruff check . }
    Invoke-Gate 'ruff format'    { uv run ruff format --check . }
    Invoke-Gate 'mypy (strict)'  { uv run mypy ecms }
    Invoke-Gate 'pytest + cov'   { uv run pytest }
}
finally {
    Pop-Location
}

# --- Kubernetes validation (kubeconform) ---
$kubeconform = Resolve-Tool 'kubeconform' (Join-Path $ToolsDir 'kubeconform\kubeconform.exe')
$kustomizeBase = Join-Path $RepoRoot 'kubernetes\base'
if ($kubeconform) {
    Invoke-Gate 'kubeconform (kustomize base)' {
        Get-ChildItem -Path $kustomizeBase -Filter *.yaml -Recurse |
            Where-Object { $_.Name -ne 'kustomization.yaml' } |
            ForEach-Object { & $kubeconform -strict -summary $_.FullName }
    }
}
else {
    Invoke-Gate 'kubeconform (kustomize base)' { } -SkipReason 'kubeconform not found'
}

# --- Helm chart lint + render + validate ---
$helm = Resolve-Tool 'helm' (Join-Path $ToolsDir 'helm\windows-amd64\helm.exe')
$chart = Join-Path $RepoRoot 'kubernetes\helm\ecms'
if ($helm) {
    Invoke-Gate 'helm lint' { & $helm lint $chart }
    if ($kubeconform) {
        Invoke-Gate 'helm template + kubeconform' {
            $rendered = & $helm template ecms $chart
            $tmp = New-TemporaryFile
            Set-Content -Path $tmp -Value $rendered
            & $kubeconform -strict -summary $tmp
            Remove-Item $tmp -Force
        }
    }
}
else {
    Invoke-Gate 'helm lint' { } -SkipReason 'helm not found'
}

# --- Terraform validate ---
$terraform = Resolve-Tool 'terraform' (Join-Path $ToolsDir 'terraform\terraform.exe')
$tfDir = Join-Path $RepoRoot 'terraform'
if ($terraform) {
    Invoke-Gate 'terraform validate' {
        Push-Location $tfDir
        try {
            & $terraform init -backend=false -input=false | Out-Null
            & $terraform validate
        }
        finally { Pop-Location }
    }
}
else {
    Invoke-Gate 'terraform validate' { } -SkipReason 'terraform not found'
}

# --- Documentation build (strict) ---
Invoke-Gate 'mkdocs build --strict' {
    Push-Location $RepoRoot
    try { uv run --project backend mkdocs build --strict }
    finally { Pop-Location }
} -Optional

# --- Docker backend image build (optional) ---
$docker = Resolve-Tool 'docker' $null
if ($SkipDocker) {
    Invoke-Gate 'docker build (backend)' { } -SkipReason '-SkipDocker specified'
}
elseif ($docker) {
    Invoke-Gate 'docker build (backend)' {
        Push-Location $RepoRoot
        try { & $docker build -f docker/backend.Dockerfile -t ecms-backend:verify . | Out-Null }
        finally { Pop-Location }
    }
}
else {
    Invoke-Gate 'docker build (backend)' { } -SkipReason 'docker not found'
}

# --- Summary ---
Write-Host ""
Write-Host "== Verification Summary ==" -ForegroundColor Magenta
$script:Results | Format-Table -AutoSize

$failed = @($script:Results | Where-Object { $_.Status -eq 'FAIL' })
if ($failed.Count -gt 0) {
    Write-Host "RESULT: FAIL ($($failed.Count) gate(s) failed)" -ForegroundColor Red
    exit 1
}
Write-Host "RESULT: PASS (all enforced gates passed)" -ForegroundColor Green
exit 0
