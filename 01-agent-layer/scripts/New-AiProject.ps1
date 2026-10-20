[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [string]$SharedLayer
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SharedLayer)) {
    $SharedLayer = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
}

$sharedRoot = (Resolve-Path -LiteralPath $SharedLayer).Path
$guidePath = Join-Path $sharedRoot "AGENT_GUIDE.md"
$templateRoot = Join-Path $sharedRoot "templates\project"
$workspaceScript = Join-Path $sharedRoot "scripts\workspace.py"

foreach ($required in @($guidePath, $templateRoot, $workspaceScript)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "共享规则层不完整，缺少: $required"
    }
}

$projectRoot = [System.IO.Path]::GetFullPath($Path)
if (Test-Path -LiteralPath $projectRoot) {
    if (@(Get-ChildItem -LiteralPath $projectRoot -Force).Count -gt 0) {
        throw "目标目录已存在且非空，拒绝覆盖: $projectRoot"
    }
}
else {
    New-Item -ItemType Directory -Path $projectRoot | Out-Null
}

$layerPath = Join-Path $projectRoot "01-agent-layer"
if (Test-Path -LiteralPath $layerPath) {
    throw "目标中已存在 01-agent-layer，拒绝覆盖: $layerPath"
}

New-Item -ItemType Junction -Path $layerPath -Target $sharedRoot | Out-Null

foreach ($entry in @(Get-ChildItem -LiteralPath $templateRoot -Force)) {
    Copy-Item -LiteralPath $entry.FullName -Destination $projectRoot -Recurse -Force
}

foreach ($relative in @(
    "02-work-items\active",
    "02-work-items\archived",
    "03-session-state\active",
    "03-session-state\archived",
    "03-session-state\knowledge"
)) {
    New-Item -ItemType Directory -Path (Join-Path $projectRoot $relative) -Force | Out-Null
}

$projectName = Split-Path -Leaf $projectRoot
$config = [ordered]@{
    schemaVersion = 1
    mode = "project"
    name = $projectName
    sharedAgentLayer = $sharedRoot
}
$config | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $projectRoot ".ai-workspace.json") -Encoding utf8

$git = Get-Command git -ErrorAction Stop
& $git.Source -C $projectRoot init --quiet
if ($LASTEXITCODE -ne 0) {
    throw "git init 失败: $projectRoot"
}
& $git.Source -C $projectRoot config core.hooksPath "01-agent-layer/githooks"
if ($LASTEXITCODE -ne 0) {
    throw "设置 core.hooksPath 失败: $projectRoot"
}

$python = Get-Command python -ErrorAction Stop
& $python.Source $workspaceScript --root $projectRoot validate
if ($LASTEXITCODE -ne 0) {
    throw "工程结构校验失败: $projectRoot"
}

Write-Output $projectRoot
