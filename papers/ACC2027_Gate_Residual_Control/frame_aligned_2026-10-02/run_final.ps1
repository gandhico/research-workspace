# After run_all_stages.ps1 (ALL DONE) and run_chain_b.ps1 (CHAIN B DONE): Fig. 4 ladder, sandbox verifier, comparison.
$sb = 'C:\Research\papers\ACC2027_Gate_Residual_Control\frame_aligned_2026-10-02'
$repo = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py = Join-Path $repo '.venv\Scripts\python.exe'
$log = Join-Path $sb 'extras.log'
$fr = Join-Path $sb 'experiments\final_robustness_gating_2026-09-20'
$tools = Join-Path $repo 'tools\frame_aligned'

function Mark([string]$m) { "=== $m $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 $log }
function Step([string]$name, [string]$dir, [string[]]$cmd) {
    Mark "EXTRA $name start"
    Push-Location $dir
    try { & $py @cmd *>> $log; $code = $LASTEXITCODE } finally { Pop-Location }
    Mark "EXTRA $name end exit=$code"
}

Mark 'FINAL waiting'
while (-not ((Select-String -Path (Join-Path $sb 'campaign_all.log') -Pattern 'ALL DONE' -Quiet) -and
             (Select-String -Path $log -Pattern 'CHAIN B DONE' -Quiet))) { Start-Sleep -Seconds 60 }
Step 'fig4-ladder' $fr @('make_ladder_figure.py', '--platforms', 'x2', '--missions', 'hard45', '--variants', 'C')
Step 'verify-sandbox' $sb @('reproduce\verify_acc2027_claims.py')
# published reproduce\claims_check.csv (02:11 today, identical verifier file, 75/75 OK) is the comparison baseline
Step 'compare' $tools @('compare_claims.py')
Mark 'FINAL ALL DONE'
