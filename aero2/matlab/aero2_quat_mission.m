function summary = aero2_quat_mission(backend, duration_s, targetHz)
%AERO2_QUAT_MISSION  MATLAB quaternion-yaw + pitch-hold on the complex yaw mission.
%   Native MATLAB controller (shortest-path quaternion yaw error + rate-limited
%   setpoint slew, PD pitch-hold at 0) driving the Aero2 through the Python bridge
%   (twin or hardware). Mirrors the Python `qpd` on `yaw_complex_mission` for a
%   cross-platform comparison. Data saved to results_matlab/.
%
%   Example:  aero2_quat_mission('hardware', 25, 100)

    if nargin < 1 || isempty(backend),   backend = 'hardware'; end
    if nargin < 2 || isempty(duration_s), duration_s = 25; end
    if nargin < 3 || isempty(targetHz),  targetHz   = 100; end

    REPO   = 'C:\Research\aero2';
    QPY    = 'C:\Users\gandhico\Documents\Quanser\0_libraries\python';
    ENVDIR = 'C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif';
    PYEXE  = fullfile(ENVDIR, 'python.exe');
    MATDIR = fullfile(REPO, 'matlab');
    OUTDIR = fullfile(REPO, 'results_matlab');
    if ~exist(OUTDIR, 'dir'); mkdir(OUTDIR); end
    setenv('PATH', strjoin({ENVDIR, fullfile(ENVDIR,'Library','bin'), ...
                            fullfile(ENVDIR,'Scripts'), getenv('PATH')}, pathsep));
    try
        pyenv(Version = PYEXE, ExecutionMode = "OutOfProcess");
    catch
    end
    insert(py.sys.path, int32(0), MATDIR);

    % gains (mirror qpd + the hardware run)
    KpP = 116.24203523333735; KdP = 99.698951398313469;   % pitch hold @0
    KpY = 20.0; KdY = 10.0;                                % yaw (hardware-boosted)
    slew = deg2rad(120);                                   % yaw setpoint slew [rad/s]
    Vlim = 14.0;

    % complex yaw schedule (deg): (t_start, yaw_target) -- same as Python
    STEPS = [0 0; 2.5 200; 5 -150; 7.5 300; 10 -90; 12.5 170; 15 -270; 17.5 45; 20 -200; 22.5 0];
    yaw_ref = @(t) deg2rad(STEPS(find(STEPS(:,1) <= t, 1, 'last'), 2));

    fprintf('MATLAB quaternion mission on %s ...\n', backend);
    br = py.matlab_bridge.TwinBridge(QPY, REPO, 200.0, 'mixed', Vlim, backend);

    dt = 1/targetHz; Nmax = ceil(duration_s*targetHz) + 50;
    L = zeros(Nmax, 6);   % t, psi_ref, theta, psi, u_p, u_y
    psi_cmd = [];  u = [0 0];  k = 0;  t0 = tic;
    try
        while true
            t = toc(t0);
            if t > duration_s, break; end
            k = k + 1;
            out = double(br.step(u(1), u(2)));   % [t, theta, psi, theta_dot, psi_dot]
            th = out(2); ps = out(3); thd = out(4); psd = out(5);
            if isempty(psi_cmd), psi_cmd = ps; end
            rp = yaw_ref(t);
            % rate-limited quaternion setpoint slew toward target (shortest path)
            to_t = yaw_err_quat(rp, psi_cmd);
            psi_cmd = psi_cmd + max(min(to_t, slew*dt), -slew*dt);
            e_yaw = yaw_err_quat(psi_cmd, ps);          % wrap-aware tracking error
            u_p = max(min(KpP*(0 - th) - KdP*thd, Vlim), -Vlim);   % hold pitch @0
            u_y = max(min(KpY*e_yaw - KdY*psd, Vlim), -Vlim);
            u = [u_p, u_y];
            L(k,:) = [t, rp, th, ps, u_p, u_y];
            nextT = k*dt;
            while toc(t0) < nextT && toc(t0) <= duration_s; end
        end
    catch ME
        fprintf(2, 'loop error: %s\n', ME.message);
    end
    br.close();
    L = L(1:k, :);

    summary = struct('backend', backend, 'samples', k, 'duration', L(end,1), ...
        'realizedHz', k/L(end,1), ...
        'pitch_hold_rms_deg', rad2deg(sqrt(mean(L(:,3).^2))), ...
        'yaw_reach_deg', rad2deg(max(abs(L(:,4)))), ...
        'yaw_travel_deg', rad2deg(sum(abs(diff(L(:,4))))));

    stamp = char(datetime('now','Format','yyyyMMdd_HHmmss'));
    T = array2table(L, 'VariableNames', {'t','psi_ref','theta','psi','u_pitch','u_yaw'});
    writetable(T, fullfile(OUTDIR, ['aero2_quat_mission_' backend '_' stamp '.csv']));
    save(fullfile(OUTDIR, ['aero2_quat_mission_' backend '_' stamp '.mat']), 'L', 'summary');

    fprintf('[MATLAB quat-mission | %s]\n', backend);
    fprintf('  samples=%d duration=%.2fs realized=%.1f Hz\n', k, summary.duration, summary.realizedHz);
    fprintf('  pitch-hold RMS=%.1f deg  yaw reach=%.0f deg  yaw travel=%.0f deg\n', ...
        summary.pitch_hold_rms_deg, summary.yaw_reach_deg, summary.yaw_travel_deg);
end

function e = yaw_err_quat(psi_ref, psi_meas)
% shortest-path yaw error via canonicalized error quaternion about +z
    qr = [cos(psi_ref/2); 0; 0; sin(psi_ref/2)];
    qm = [cos(psi_meas/2); 0; 0; sin(psi_meas/2)];
    qmc = [qm(1); -qm(2); -qm(3); -qm(4)];
    qe = quatmul(qr, qmc);
    if qe(1) < 0, qe = -qe; end
    e = 2*atan2(qe(4), qe(1));
end

function q = quatmul(a, b)
    q = [a(1)*b(1)-a(2)*b(2)-a(3)*b(3)-a(4)*b(4);
         a(1)*b(2)+a(2)*b(1)+a(3)*b(4)-a(4)*b(3);
         a(1)*b(3)-a(2)*b(4)+a(3)*b(1)+a(4)*b(2);
         a(1)*b(4)+a(2)*b(3)-a(3)*b(2)+a(4)*b(1)];
end
