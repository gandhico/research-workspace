# Runs in parallel with run_all_stages.ps1 (which is in the slow NMPC part of 'portability'). Every step resumes from
# summary.json, so when run_all_stages.ps1 later reaches 'neuronbasis' it finds these runs cached.
$sb = 'C:\Research\papers\ACC2027_Gate_Residual_Control\frame_aligned_2026-10-02'
$repo = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py = Join-Path $repo '.venv\Scripts\python.exe'
$log = Join-Path $sb 'extras.log'
$nn = Join-Path $sb 'experiments\nengo_nef_replication_2026-08-29'
$mc = Join-Path $sb 'experiments\cmg_mechanism_controls_2026-10-01'
$tools = Join-Path $repo 'tools\frame_aligned'

function Mark([string]$m) { "=== $m $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 $log }
function Step([string]$name, [string]$dir, [string[]]$cmd) {
    Mark "EXTRA $name start"
    Push-Location $dir
    try { & $py @cmd *>> $log; $code = $LASTEXITCODE } finally { Pop-Location }
    Mark "EXTRA $name end exit=$code"
    if ($code -ne 0) { Mark "EXTRA FAILED $name" }
}

Mark 'EXTRA neuronbasis start'
& powershell -ExecutionPolicy Bypass -File (Join-Path $sb 'reproduce\reproduce_all.ps1') -Stage neuronbasis *>> $log
Mark "EXTRA neuronbasis end exit=$LASTEXITCODE"
Step 'ladder-select' $nn @('select_rate_ff.py')
Step 'ladder-ff-cmg' $nn @('run_ff_cmg.py')
Step 'master-table' $tools @('build_master_table.py')
Step 'mc-phase0' $mc @('phase0_latch_diagnostics.py')
Step 'mc-development' $mc @('run_campaign.py', '--mode', 'development', '--workers', '8')
Step 'mc-confirm' $mc @('run_campaign.py', '--mode', 'confirm', '--workers', '8')
Step 'mc-analyze' $mc @('analyze.py')
Mark 'CHAIN B DONE'
