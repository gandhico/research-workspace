[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('hover','roll','full3','hard45','hardstep','yaw360')]
    [string]$Mission,

    [Parameter(Mandatory = $true)]
    [ValidateSet(
        'pd','nengo-pes','nengo-nef-pes','nengo-cmg-fixed',
        'nengo-lif-fixed','nengo-lif-pes',
        'nengo-alif-fixed','nengo-alif-pes',
        'nengo-izhikevich-fixed','nengo-izhikevich-pes',
        'nengo-lifrate-fixed','nengo-lifrate-pes'
    )]
    [string]$Controller,

    [ValidateSet('gui','headless','q8-shadow','hardware')]
    [string]$Mode = 'gui',

    [ValidateSet('none','hard-pulses')]
    [string]$Disturbance = 'none',

    [switch]$ConfirmHardwareReview,
    [string]$GuiPassword,

    # Optional override for the per-mission default duration (seconds). 0 = use the
    # mission's own tuned default (unchanged behavior). Added 2026-09-03.
    [int]$DurationOverride = 0
)

$ErrorActionPreference = 'Stop'
$python = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\nengo_gui_hil_2026-08-29'
$gui = Join-Path $root 'launch_hover_nengo_gui.py'
$headless = Join-Path $root 'run_hover_headless.py'

if (-not (Test-Path -LiteralPath $python)) { throw "Missing Python environment: $python" }

# Simulation profiles reproduce the frozen 25-s nominal/hard-pulse matrix.
$simulationProfiles = @{
    hover    = @{ duration=25; scale=1.0; transition=0.0; allocator='fixed-bias'; pulse=1.0 }
    roll     = @{ duration=25; scale=1.0; transition=0.0; allocator='fixed-bias'; pulse=1.0 }
    full3    = @{ duration=25; scale=1.0; transition=0.0; allocator='fixed-bias'; pulse=1.0 }
    hard45   = @{ duration=25; scale=1.0; transition=0.0; allocator='fixed-bias'; pulse=0.05 }
    hardstep = @{ duration=25; scale=0.7; transition=0.5; allocator='stability-priority'; pulse=0.10 }
    yaw360   = @{ duration=25; scale=0.8; transition=0.0; allocator='stability-priority'; pulse=0.05 }
}

# Hardware profiles reproduce the qualified/safely attempted physical runs.
$hardwareProfiles = @{
    hover    = @{ duration=5;  scale=1.0;  transition=0.0; allocator='fixed-bias'; maxPitch=20; maxRoll=20 }
    roll     = @{ duration=8;  scale=1.0;  transition=0.0; allocator='fixed-bias'; maxPitch=15; maxRoll=25 }
    full3    = @{ duration=12; scale=0.5;  transition=0.0; allocator='fixed-bias'; maxPitch=25; maxRoll=25 }
    hard45   = @{ duration=12; scale=0.4;  transition=0.0; allocator='fixed-bias'; maxPitch=25; maxRoll=30 }
    hardstep = @{ duration=12; scale=0.35; transition=0.3; allocator='fixed-bias'; maxPitch=30; maxRoll=30 }
    yaw360   = @{ duration=45; scale=1.0;  transition=0.0; allocator='stability-priority'; maxPitch=20; maxRoll=20 }
}

$commonNeural = @(
    '--beta','0.2',
    '--motor-residual-cap-volts','0.2',
    '--learning-rate','0.0002',
    '--k-error','2',
    '--k-rate','0',
    '--residual-slew-v-per-s','1'
)

if ($Mode -eq 'hardware') {
    if (-not $ConfirmHardwareReview) {
        throw 'Hardware mode requires -ConfirmHardwareReview after reading the safety checklist and confirming the E-stop.'
    }
    if ($Controller -notin @('pd','nengo-pes')) {
        throw 'Only pd and the qualified nengo-pes controller may drive Q8 hardware.'
    }
    if ($Disturbance -ne 'none') {
        throw 'Software torque disturbances are not permitted in physical hardware mode.'
    }
    if ($DurationOverride -gt 60) {
        throw "DurationOverride capped at 60s for physical hardware safety; requested $DurationOverride. Use q8-shadow or simulation mode for longer runs."
    }
    $profile = $hardwareProfiles[$Mission]
    $hwDuration = if ($DurationOverride -gt 0) { $DurationOverride } else { $profile.duration }
    $arguments = @(
        $gui, '--io','q8','--armed','--confirm-hardware-review',
        '--controller',$Controller,'--mission',$Mission,
        '--duration',[string]$hwDuration,
        '--reference-scale',[string]$profile.scale,
        '--hardstep-transition-s',[string]$profile.transition,
        '--allocation-policy',$profile.allocator,
        '--motor-floor-volts','2',
        '--max-abs-pitch-deg',[string]$profile.maxPitch,
        '--max-abs-roll-deg',[string]$profile.maxRoll,
        '--max-encoder-step-deg','5',
        '--output-root',(Join-Path $root 'results\hardware')
    ) + $commonNeural
} elseif ($Mode -eq 'q8-shadow') {
    if ($Disturbance -ne 'none') { throw 'Q8 shadow mode does not inject software disturbances.' }
    $profile = $simulationProfiles[$Mission]
    $shadowDuration = if ($DurationOverride -gt 0) { $DurationOverride } else { 5 }
    $arguments = @(
        $gui, '--io','q8','--controller',$Controller,'--mission',$Mission,
        '--duration',[string]$shadowDuration,'--reference-scale',[string]$profile.scale,
        '--hardstep-transition-s',[string]$profile.transition,
        '--allocation-policy',$profile.allocator,
        '--max-abs-pitch-deg','55','--max-abs-roll-deg','55',
        '--output-root',(Join-Path $root 'results\q8_gui_shadow')
    ) + $commonNeural
} else {
    $profile = $simulationProfiles[$Mission]
    $disturbanceScale = if ($Disturbance -eq 'hard-pulses') { $profile.pulse } else { 0.0 }
    $output = Join-Path $root "results\gui_and_manual_runs"
    $simDuration = if ($DurationOverride -gt 0) { $DurationOverride } else { $profile.duration }
    $arguments = @(
        $(if ($Mode -eq 'gui') { $gui } else { $headless }),
        '--io','emulated','--controller',$Controller,'--mission',$Mission,
        '--duration',[string]$simDuration,
        '--reference-scale',[string]$profile.scale,
        '--hardstep-transition-s',[string]$profile.transition,
        '--allocation-policy',$profile.allocator,
        '--disturbance',$Disturbance,
        '--disturbance-scale',[string]$disturbanceScale,
        '--max-abs-pitch-deg','180','--max-abs-roll-deg','180',
        '--output-root',$output
    ) + $commonNeural
}

if ($GuiPassword -and $Mode -ne 'headless') {
    $arguments += @('--gui-password',$GuiPassword)
}

Write-Host "Launching $Mode | $Mission | $Controller | disturbance=$Disturbance"
Write-Host "Python: $python"
& $python @arguments
exit $LASTEXITCODE
