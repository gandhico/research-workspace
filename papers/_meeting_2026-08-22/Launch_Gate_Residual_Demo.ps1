[CmdletBinding()]
param(
    [ValidateSet(
        'classical-cf2',
        'fixed-cf2',
        'adaptive-cf2',
        'fixed-x2',
        'rotor-x2',
        'fixed-table1',
        'learned-cf2',
        'learned-all',
        'learned-x2',
        'frontier-balanced',
        'frontier-strong'
    )]
    [string]$Mode = 'adaptive-cf2',

    [string]$Python = 'C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe',
    [switch]$Viewer,
    [switch]$Dashboard,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$FixedRoot = 'C:\Research\papers\P3_Gate_Residual\fixed_adaptive'
$FixedRunner = Join-Path $FixedRoot 'runners\run_rotor_level.py'
$LearnedRoot = 'C:\Research\papers\P3_Gate_Residual\learned\code\experiments\controller_benchmarks'
$LearnedRunner = Join-Path $LearnedRoot 'learned_gate_experiment.py'
$FixedModels = 'C:\Research\papers\P3_Gate_Residual\models\mujoco_menagerie'
$LearnedModels = 'C:\Research\papers\P3_Gate_Residual\learned\code\third_party\mujoco_menagerie'

function Assert-File([string]$Path, [string]$Message) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Message`nMissing: $Path"
    }
}

function Assert-Python([switch]$NeedNengo) {
    if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
        throw "Python was not found: $Python. Pass the environment interpreter with -Python C:\path\to\python.exe"
    }

    $modules = if ($NeedNengo) { 'mujoco,numpy,matplotlib,nengo' } else { 'mujoco,numpy,matplotlib' }
    & $Python -c "import $modules" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "The selected Python lacks required packages: $modules. Install them in the intended research environment, then pass that interpreter with -Python."
    }
}

function Invoke-CheckedPython([string]$WorkingDirectory, [string[]]$Arguments, [string]$ModelXml, [switch]$NeedNengo) {
    $display = "& '$Python' " + (($Arguments | ForEach-Object { if ($_ -match '\s') { "'$_'" } else { $_ } }) -join ' ')
    Write-Host ""
    Write-Host "Working directory: $WorkingDirectory" -ForegroundColor Cyan
    Write-Host $display -ForegroundColor Green

    if ($DryRun) {
        return
    }

    Assert-Python -NeedNengo:$NeedNengo
    Assert-File $ModelXml "MuJoCo Menagerie assets are not installed at the path expected by this runner. See Gate_Residual_Runners_Quick_Start.txt."

    Push-Location -LiteralPath $WorkingDirectory
    try {
        & $Python @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Runner exited with code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function Fixed-VisualFlags {
    $flags = @()
    if ($Viewer) { $flags += '--viewer' }
    if ($Dashboard) { $flags += '--dashboard' }
    return $flags
}

$cf2FixedXml = Join-Path $FixedModels 'bitcraze_crazyflie_2\scene.xml'
$x2FixedXml = Join-Path $FixedModels 'skydio_x2\scene.xml'
$cf2LearnedXml = Join-Path $LearnedModels 'bitcraze_crazyflie_2\scene.xml'
$x2LearnedXml = Join-Path $LearnedModels 'skydio_x2\scene.xml'

switch ($Mode) {
    'classical-cf2' {
        $a = @($FixedRunner, '--quad','bitcraze_crazyflie_2','--controller','classical','--mission','hard45','--sim-time','45','--save-csv','--save-figures') + (Fixed-VisualFlags)
        Invoke-CheckedPython $FixedRoot $a $cf2FixedXml
    }
    'fixed-cf2' {
        $a = @($FixedRunner, '--quad','bitcraze_crazyflie_2','--controller','direct_hyperlif','--mission','hard45','--sim-time','45','--blend','0.50','--direct-scale','control','--activity-mode','gate','--gate-gain','100000','--save-csv','--save-figures') + (Fixed-VisualFlags)
        Invoke-CheckedPython $FixedRoot $a $cf2FixedXml
    }
    'adaptive-cf2' {
        $a = @($FixedRunner, '--quad','bitcraze_crazyflie_2','--controller','direct_adaptive_hyperlif','--mission','hard45','--sim-time','45','--blend','0.50','--direct-scale','control','--activity-mode','gate','--gate-gain','100000','--save-csv','--save-figures') + (Fixed-VisualFlags)
        Invoke-CheckedPython $FixedRoot $a $cf2FixedXml
    }
    'fixed-x2' {
        $a = @($FixedRunner, '--quad','skydio_x2','--controller','direct_hyperlif','--mission','hard45','--sim-time','45','--blend','0.50','--direct-scale','control','--activity-mode','gate','--gate-gain','100000','--save-csv','--save-figures') + (Fixed-VisualFlags)
        Invoke-CheckedPython $FixedRoot $a $x2FixedXml
    }
    'rotor-x2' {
        $a = @($FixedRunner, '--quad','skydio_x2','--controller','rotor_residual_adaptive_hyperlif','--mission','hard45','--sim-time','45','--residual-blend','0.10','--gate-gain','100000','--save-csv','--save-figures') + (Fixed-VisualFlags)
        Invoke-CheckedPython $FixedRoot $a $x2FixedXml
    }
    'fixed-table1' {
        foreach ($controller in @('classical','direct_lif','direct_hyperlif','direct_adaptive_hyperlif','nengo_lifrate')) {
            $a = @($FixedRunner, '--quad','bitcraze_crazyflie_2','--controller',$controller,'--mission','hard45','--sim-time','45','--blend','0.50','--direct-scale','control','--activity-mode','gate','--gate-gain','100000','--save-csv','--save-figures')
            Invoke-CheckedPython $FixedRoot $a $cf2FixedXml -NeedNengo:($controller -eq 'nengo_lifrate')
        }
    }
    'learned-cf2' {
        $out = Join-Path $LearnedRoot 'learned_gate_cf2_meeting_rerun.json'
        $a = @($LearnedRunner, '--quad','bitcraze_crazyflie_2','--mission','hard45','--methods','classical,fixed_gate,online_pes,eprop_anneal','--out',$out)
        Invoke-CheckedPython $LearnedRoot $a $cf2LearnedXml
    }
    'learned-all' {
        $out = Join-Path $LearnedRoot 'learned_gate_all_meeting_rerun.json'
        $a = @($LearnedRunner, '--quad','bitcraze_crazyflie_2','--mission','hard45','--methods','all','--out',$out)
        Invoke-CheckedPython $LearnedRoot $a $cf2LearnedXml
    }
    'learned-x2' {
        $out = Join-Path $LearnedRoot 'learned_gate_x2_meeting_rerun.json'
        $a = @($LearnedRunner, '--quad','skydio_x2','--mission','hard45','--methods','classical,fixed_gate,online_pes,eprop_anneal','--out',$out)
        Invoke-CheckedPython $LearnedRoot $a $x2LearnedXml
    }
    'frontier-balanced' {
        $out = Join-Path $LearnedRoot 'learned_gate_hardstep_balanced_rerun.json'
        $a = @($LearnedRunner, '--quad','bitcraze_crazyflie_2','--mission','hardstep','--z-ref','1.5','--methods','online_pes,eprop_anneal','--k-rate','0.3','--leak','1e-3','--out',$out)
        Invoke-CheckedPython $LearnedRoot $a $cf2LearnedXml
    }
    'frontier-strong' {
        $out = Join-Path $LearnedRoot 'learned_gate_hardstep_strong_rerun.json'
        $a = @($LearnedRunner, '--quad','bitcraze_crazyflie_2','--mission','hardstep','--z-ref','1.5','--methods','online_pes,eprop_anneal','--k-rate','1.0','--leak','2e-3','--out',$out)
        Invoke-CheckedPython $LearnedRoot $a $cf2LearnedXml
    }
}
