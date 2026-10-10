# Reproduce the ACC 2027 paper, stage by stage. See REPRODUCE_ACC2027.md for the claim map.
#   powershell -ExecutionPolicy Bypass -File reproduce\reproduce_all.ps1 -Stage verify
# Stages: verify | validation | primary | robustness | portability | izhikevich | neuronbasis | figures | all
# Every campaign resumes from existing summary.json files and never overwrites archived runs.
param([string]$Stage = 'verify')

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'
$fr = Join-Path $root 'experiments\final_robustness_gating_2026-09-20'
$nb = Join-Path $root 'experiments\neuron_basis_decisive_2026-09-24'
if (-not (Test-Path -LiteralPath $py)) { throw "Python environment not found: $py" }

function Run([string]$dir, [string[]]$cmd) {
    Push-Location $dir
    try {
        & $py @cmd
        if ($LASTEXITCODE -ne 0) { throw "Failed: $($cmd -join ' ')" }
    } finally { Pop-Location }
}

function Stage-Validation { Run $fr @('run_validation.py') }

function Stage-Primary {
    Run $fr @('run_campaign.py', '--campaign', 'nominal')
    Run $fr @('run_campaign.py', '--campaign', 'hardstep-development')
    Run $fr @('run_campaign_a2.py', 'dev')
    Run $fr @('run_campaign_a2.py', 'nominal', 'gated_b02')
    Run $fr @('run_campaign_a2.py', 'confirm', 'gated_b02')
    Run $fr @('build_final_csv.py')
    Run $fr @('analyze_nominal.py')
}

function Stage-Robustness {
    Run $fr @('run_campaign.py', '--campaign', 'disturbance')
    Run $fr @('run_campaign.py', '--campaign', 'noise')
    Run $fr @('run_campaign_a2.py', 'disturbance', 'gated_b02')
    Run $fr @('run_campaign_a2.py', 'noise_rest', 'gated_b02')
    Run $fr @('build_final_csv.py')
    Run $fr @('analyze_robustness.py')
    Run $fr @('noise_numbers.py')
    Run $fr @('hardstep_profile.py')
}

function Stage-Portability {
    Run $fr @('run_campaign_a5.py')
    Run $fr @('run_campaign_a5_backstepping.py')
    Run $fr @('run_campaign_a5_nmpc_corrected.py')
    Run $fr @('certify_beta0_recovery.py')
    Run $fr @('analyze_a5.py')
}

function Stage-Izhikevich {
    $out = Join-Path $fr 'results_izh_corrected\table2_full_2026-09-29'
    $cells = @(@('x2', '0.5', '1.0', 'x2'), @('cf2-rotor', '0.2', '1.5', 'cf2'))
    foreach ($c in $cells) {
        foreach ($m in @('roll', 'full3', 'hard45', 'hardstep', 'yaw360')) {
            $dest = Join-Path $out "$($c[3])_$m"
            if (Test-Path -LiteralPath (Join-Path $dest 'summary.json')) { continue }
            Run $fr @('run_izh_corrected.py', '--platform', $c[0], '--controller', 'nengo-izhikevich-pes', '--mission', $m,
                      '--duration', '45', '--beta', $c[1], '--actuator-scale', $c[2], '--output-gate', 'torque-saturation-opposition',
                      '--gate-load-threshold', '1.0', '--log-every', '10', '--no-neural-archive', '--seed', '1', '--output', $dest)
        }
    }
}

function Stage-NeuronBasis {
    & (Join-Path $nb 'reproduce_all.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Neuron-basis study failed.' }
}

function Stage-Figures {
    Run $fr @('make_ladder_figure.py', '--platforms', 'x2', '--missions', 'hard45', '--variants', 'C')
    Run $fr @('make_paper_figures.py', 'hardstep_zoom')
    # prints the regenerated Table II primary rows; add '--write' only to overwrite the local table file
    Run $fr @('make_table2.py', (Join-Path $root 'paper\v15_2026-09-29_corrected\tables\table_all_restructured.tex'))
}

function Stage-Verify { Run $root @('reproduce\verify_acc2027_claims.py') }

switch ($Stage) {
    'verify'      { Stage-Verify }
    'validation'  { Stage-Validation }
    'primary'     { Stage-Primary }
    'robustness'  { Stage-Robustness }
    'portability' { Stage-Portability }
    'izhikevich'  { Stage-Izhikevich }
    'neuronbasis' { Stage-NeuronBasis }
    'figures'     { Stage-Figures }
    'all' {
        Stage-Validation; Stage-Primary; Stage-Robustness; Stage-Portability
        Stage-Izhikevich; Stage-NeuronBasis; Stage-Figures; Stage-Verify
    }
    default { throw "Unknown stage '$Stage'. Use verify, validation, primary, robustness, portability, izhikevich, neuronbasis, figures, or all." }
}
