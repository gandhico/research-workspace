$sb = 'C:\Research\papers\ACC2027_Gate_Residual_Control\frame_aligned_2026-10-02'
foreach ($st in @('primary','portability','izhikevich','robustness','neuronbasis')) {
  "=== STAGE $st start $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 (Join-Path $sb 'campaign_all.log')
  & powershell -ExecutionPolicy Bypass -File (Join-Path $sb 'reproduce\reproduce_all.ps1') -Stage $st *>> (Join-Path $sb 'campaign_all.log')
  "=== STAGE $st end $(Get-Date -Format s) exit=$LASTEXITCODE" | Out-File -Append -Encoding utf8 (Join-Path $sb 'campaign_all.log')
}
"=== ALL DONE $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 (Join-Path $sb 'campaign_all.log')
