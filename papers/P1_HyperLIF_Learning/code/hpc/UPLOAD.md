# Uploading to the HPC (Open OnDemand) — HyperLIF_Learning

Upload is **code-only**; data is produced on the cluster. Two items at most:

| # | File | → Destination | Size |
|---|---|---|---|
| A | `hyperlif_learning_hpc.zip` | `/fs1/home/gandhico/HyperLIF_Learning/` (unzip there) | ~80 KB |
| B *(optional)* | `shd_wide_T20.pt` | `/fs1/scratch/gandhico/HyperLIF_Learning/cache/` | 150 MB |

B is optional — SHD downloads fine from zenkelab on the cluster, so you can regenerate it with
`make_caches.py` instead of uploading.

## Build the code zip (Windows, PowerShell 7) — Linux-safe

`Compress-Archive` / Explorer "Send to zip" on Windows can store **backslash** paths that unzip into
broken filenames on Linux. Build the entries with explicit forward slashes:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage
$stage = "$PWD\_upload_stage"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Path "$stage\hpc" | Out-Null
Copy-Item hpc\*.py, hpc\*.sh, hpc\*.slurm, hpc\*.md -Destination "$stage\hpc"
Copy-Item hpc\adhyperlif_triage "$stage\hpc\adhyperlif_triage" -Recurse
Copy-Item hpc\scripts "$stage\hpc\scripts" -Recurse
New-Item -ItemType Directory -Path "$stage\hpc\docs" | Out-Null
Copy-Item docs\*.md -Destination "$stage\hpc\docs"
Get-ChildItem $stage -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
$zip = "$PWD\hyperlif_learning_hpc.zip"; if (Test-Path $zip) { Remove-Item -Force $zip }
Add-Type -AssemblyName System.IO.Compression
$fs = [System.IO.File]::Open($zip,'Create'); $arch = New-Object System.IO.Compression.ZipArchive($fs,'Create')
$bs=[char]92; $fwd=[char]47
Get-ChildItem $stage -Recurse -File | ForEach-Object {
  $rel = $_.FullName.Substring($stage.Length+1).Replace($bs,$fwd)
  $e=$arch.CreateEntry($rel,'Optimal'); $s=$e.Open()
  $b=[System.IO.File]::ReadAllBytes($_.FullName); $s.Write($b,0,$b.Length); $s.Close() }
$arch.Dispose(); $fs.Dispose(); Remove-Item -Recurse -Force $stage
```

Excludes `.venv/`, `data/`, `results/`, `__pycache__`, and the `.pt` cache (data goes to scratch).

## On the cluster

```bash
# 1. OnDemand → Files → /fs1/home/gandhico/HyperLIF_Learning/ → Upload the zip
# 2. OnDemand → Clusters → Shell Access (Files has no unzip button):
cd /fs1/home/gandhico/HyperLIF_Learning
unzip -o hyperlif_learning_hpc.zip            # writes only under hpc/ (src/ untouched)

# 3. one-time env (creates .venv, installs deps, runs the parity gate)
bash hpc/setup_env.sh

# 4. EACH login: prepare the shell (sets HLL_* + PYTHONPATH AND activates .venv)
source hpc/paths.sh

# 5. caches, preflight, array, aggregate — see README.md
```

> **Gotcha:** `setup_env.sh` activates the venv only inside the script. In your interactive shell run
> `source hpc/paths.sh` (auto-activates `.venv`) — or `source .venv/bin/activate` — before any
> `python hpc/...` command, or you'll get `ModuleNotFoundError: No module named 'torch'`.
