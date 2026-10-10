# Reproduce the corrected neuron-basis study from raw simulations to audit.
# Existing campaign cases with a summary.json are reused; add --force to the
# individual Python campaign command when an intentional rerun is required.

$pythonPath = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$studyRoot = $PSScriptRoot

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python environment not found: $pythonPath"
}

& $pythonPath "$studyRoot\run_campaign.py" --mode strict --workers 10
if ($LASTEXITCODE -ne 0) { throw 'Strict campaign failed.' }

& $pythonPath "$studyRoot\analyze_strict.py"
if ($LASTEXITCODE -ne 0) { throw 'Strict analysis failed.' }

$developmentBaselineRoot = "$studyRoot\results\development_baseline"
foreach ($missionName in @('roll', 'hard45')) {
    $baselineOutput = "$developmentBaselineRoot\$missionName\classical"
    if (-not (Test-Path -LiteralPath "$baselineOutput\summary.json")) {
        & $pythonPath "$studyRoot\run_neuron_basis.py" `
            --platform x2 --controller classical --mission $missionName `
            --duration 15 --beta 0.5 --output $baselineOutput
        if ($LASTEXITCODE -ne 0) { throw "Development baseline failed: $missionName" }
    }
}

& $pythonPath "$studyRoot\run_campaign.py" --mode development --workers 10
if ($LASTEXITCODE -ne 0) { throw 'Development screen failed.' }

& $pythonPath "$studyRoot\select_development.py"
if ($LASTEXITCODE -ne 0) { throw 'Development selection failed.' }

& $pythonPath "$studyRoot\run_selected_validation.py" --phase confirm --workers 8
if ($LASTEXITCODE -ne 0) { throw '45 s confirmation failed.' }

& $pythonPath "$studyRoot\run_selected_validation.py" --phase validate --workers 10
if ($LASTEXITCODE -ne 0) { throw 'Held-out validation failed.' }

& $pythonPath "$studyRoot\analyze_final.py"
if ($LASTEXITCODE -ne 0) { throw 'Final analysis failed.' }

& $pythonPath "$studyRoot\audit_results.py"
if ($LASTEXITCODE -ne 0) { throw 'Artifact audit failed.' }

Write-Output "Complete. Read $studyRoot\analysis\final\FINAL_NEURON_BASIS_REPORT.md"
