[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('codex', 'claude', 'agents', 'all')]
    [string]$Target = 'all',
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Destination,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$skillNames = @(
    'rdk-course-slides-generator',
    'rdk-model-zoo-demo-review',
    'rdk-x5-toolchain-quantization',
    'rdk-yolo-toolkit'
)

if (-not (Test-Path -LiteralPath $RepositoryRoot -PathType Container)) {
    throw "Repository root does not exist: $RepositoryRoot"
}

if ($Destination -and $Target -eq 'all') {
    throw 'Use -Destination only with one target: codex, claude, or agents.'
}

$defaultRoots = @{
    codex  = Join-Path $env:USERPROFILE '.codex\skills'
    claude = Join-Path $env:USERPROFILE '.claude\skills'
    agents = Join-Path $env:USERPROFILE '.agents\skills'
}

if ($Destination) {
    $targetRoots = @{$Target = $Destination}
} elseif ($Target -eq 'all') {
    $targetRoots = $defaultRoots
} else {
    $targetRoots = @{$Target = $defaultRoots[$Target]}
}

foreach ($targetName in $targetRoots.Keys) {
    $targetRoot = $targetRoots[$targetName]
    foreach ($skillName in $skillNames) {
        $source = Join-Path $RepositoryRoot "skills\\$skillName"
        $sourceSkill = Join-Path $source 'SKILL.md'
        $destinationSkill = Join-Path $targetRoot $skillName

        if (-not (Test-Path -LiteralPath $sourceSkill -PathType Leaf)) {
            throw "Missing source Skill entry point: $sourceSkill"
        }

        if (Test-Path -LiteralPath $destinationSkill) {
            if (-not $Force) {
                Write-Warning "Skipped existing $targetName Skill: $destinationSkill (rerun with -Force to replace it)"
                continue
            }
            if ($PSCmdlet.ShouldProcess($destinationSkill, "Replace $targetName Skill '$skillName'")) {
                Remove-Item -LiteralPath $destinationSkill -Recurse -Force
            }
        }

        if ($PSCmdlet.ShouldProcess($destinationSkill, "Install $targetName Skill '$skillName'")) {
            New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
            Copy-Item -LiteralPath $source -Destination $destinationSkill -Recurse
            Write-Host "Installed $skillName -> $destinationSkill"
        }
    }
}
