function summary = aero2_twin_pd(duration_s, targetHz)
%AERO2_TWIN_PD  MATLAB PD control of the QLabs Aero2 digital twin.
%   Replicates the Python `pd` controller (aero2.control) NATIVELY in MATLAB and
%   drives the SAME QLabs Aero2 digital twin through the Python PAL bridge
%   (matlab_bridge.TwinBridge). Exact gains and the square-wave reference mirror
%   aero2/config (the repo's single source of truth), so the MATLAB and Python
%   runs are directly comparable on identical hardware-in-simulation.
%
%   Requires: QLabs Aero2 open (localhost:18950); the `hyperlif` conda env.
%
%   Example:  aero2_twin_pd(15, 100)

    if nargin < 1 || isempty(duration_s), duration_s = 15;  end
    if nargin < 2 || isempty(targetHz),   targetHz   = 100; end

    REPO   = 'C:\Research\aero2';
    QPY    = 'C:\Users\gandhico\Documents\Quanser\0_libraries\python';
    ENVDIR = 'C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif';
    PYEXE  = fullfile(ENVDIR, 'python.exe');
    MATDIR = fullfile(REPO, 'matlab');
    OUTDIR = fullfile(REPO, 'results_matlab');
    if ~exist(OUTDIR, 'dir'); mkdir(OUTDIR); end

    % Make the conda env's DLLs visible to the out-of-process interpreter
    setenv('PATH', strjoin({ENVDIR, fullfile(ENVDIR,'Library','bin'), ...
                            fullfile(ENVDIR,'Scripts'), getenv('PATH')}, pathsep));

    % Python bridge (out-of-process avoids DLL clashes with MATLAB)
    try
        pyenv(Version = PYEXE, ExecutionMode = "OutOfProcess");
    catch
        % already loaded in this session -> keep it
    end
    insert(py.sys.path, int32(0), MATDIR);

    % --- Exact gains / reference (mirror aero2/config/gains.py & references.py)
    KpP = 116.24203523333735; KdP = 99.698951398313469;   % pitch PD
    KpY = 35.8625570008741;   KdY = 38.028899215266975;   % yaw   PD
    Ath = deg2rad(20); fth = 0.05;    % pitch square-wave reference (+/-20 deg @ 0.05 Hz)
    Aps = deg2rad(45); fps = 0.04;    % yaw   square-wave reference (+/-45 deg @ 0.04 Hz)
    VMAX = 24.0;                      % HIL command clip (config.params.V_MAX)
    sq = @(t,A,f) A * (2*(mod(f.*t,1) >= 0.5) - 1);   % bipolar square wave

    fprintf('Connecting MATLAB -> QLabs Aero2 twin via Python bridge...\n');
    br = py.matlab_bridge.TwinBridge(QPY, REPO);

    dt = 1/targetHz;
    Nmax = ceil(duration_s*targetHz) + 50;
    L = zeros(Nmax, 7);   % [t, ref_theta, ref_psi, theta, psi, u_p, u_y]
    u = [0, 0];  k = 0;  t0 = tic;
    try
        while true
            t = toc(t0);
            if t > duration_s, break; end
            k = k + 1;
            out = double(br.step(u(1), u(2)));   % apply prev u -> new measurement
            th = out(2); ps = out(3); thd = out(4); psd = out(5);
            rth = sq(t, Ath, fth);  rps = sq(t, Aps, fps);
            up = KpP*(rth - th) - KdP*thd;       % PD, ref_dot = 0
            uy = KpY*(rps - ps) - KdY*psd;
            up = max(min(up, VMAX), -VMAX);
            uy = max(min(uy, VMAX), -VMAX);
            u = [up, uy];
            L(k,:) = [t, rth, rps, th, ps, up, uy];
            nextT = k*dt;
            while toc(t0) < nextT && toc(t0) <= duration_s; end   % pace to targetHz
        end
    catch ME
        fprintf(2, 'loop error: %s\n', ME.message);
    end
    br.close();
    L = L(1:k, :);

    % --- Metrics (mirror run_control's printed summary) ------------------
    e_th = L(:,2) - L(:,4);  e_ps = L(:,3) - L(:,5);
    tail = L(:,1) >= (L(end,1) * 0.5);
    summary = struct( ...
        'samples',      k, ...
        'duration',     L(end,1), ...
        'realizedHz',   k / L(end,1), ...
        'pitchRMS',     sqrt(mean(e_th.^2)), ...
        'yawRMS',       sqrt(mean(e_ps.^2)), ...
        'tailPitchMAE', mean(abs(e_th(tail))), ...
        'tailYawMAE',   mean(abs(e_ps(tail))), ...
        'pitchSat',     mean(abs(L(:,6)) >= VMAX*0.999), ...
        'yawSat',       mean(abs(L(:,7)) >= VMAX*0.999));

    stamp = char(datetime('now','Format','yyyyMMdd_HHmmss'));
    T = array2table(L, 'VariableNames', ...
        {'t','ref_theta','ref_psi','theta','psi','u_pitch','u_yaw'});
    csv = fullfile(OUTDIR, ['aero2_twin_matlab_pd_' stamp '.csv']);
    writetable(T, csv);
    save(fullfile(OUTDIR, ['aero2_twin_matlab_pd_' stamp '.mat']), 'L', 'summary');

    fprintf('[Aero2 twin | MATLAB | pd | reference_tracking]\n');
    fprintf('  samples=%d duration=%.2fs realized=%.1f Hz\n', ...
        summary.samples, summary.duration, summary.realizedHz);
    fprintf('  pitch RMS=%.4f  yaw RMS=%.4f rad\n', summary.pitchRMS, summary.yawRMS);
    fprintf('  tail pitch MAE=%.4f  tail yaw MAE=%.4f rad\n', ...
        summary.tailPitchMAE, summary.tailYawMAE);
    fprintf('  pitch sat=%.3f  yaw sat=%.3f\n', summary.pitchSat, summary.yawSat);
    fprintf('  saved -> %s\n', csv);
end
