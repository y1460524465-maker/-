param(
    [int]$DevToolsPort = 9226
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
python (Join-Path $repoRoot '01-agent-layer\scripts\dsh_desktop_bridge.py') --devtools-port $DevToolsPort launch
