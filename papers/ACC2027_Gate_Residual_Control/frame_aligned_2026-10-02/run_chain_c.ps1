# Izhikevich and robustness stages in parallel with the slow NMPC part of run_all_stages.ps1 (started 2026-10-02 21:05).
# Both stages resume from summary.json, so when run_all_stages.ps1 reaches them after NMPC it finds these runs cached.
$sb = 'C:\Research\papers\ACC2027_Gate_Residual_Control\frame_aligned_2026-10-02'
$log = Join-Path $sb 'chain_c.log'
foreach ($st in @('izhikevich', 'robustness')) {
  "=== CHAIN C $st start $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 $log
  & powershell -ExecutionPolicy Bypass -File (Join-Path $sb 'reproduce\reproduce_all.ps1') -Stage $st *>> $log
  "=== CHAIN C $st end $(Get-Date -Format s) exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 $log
}
"=== CHAIN C DONE $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 $log
