function summary = aero2_spin360_mission(backend, duration_s, targetHz)
%AERO2_SPIN360_MISSION  Pitch tracks +/-25 deg triangle; yaw quaternion-sweeps
%   +360 then -360 deg. Native MATLAB controller via the Python bridge (hardware
%   or twin). Mirrors the Python `qpd` on `pitch_track_yaw_spin360`. Saved to
%   results_matlab/. Example: aero2_spin360_mission('hardware', 24, 100)

    if nargin < 1 || isempty(backend),    backend = 'hardware'; end
    if nargin < 2 || isempty(duration_s), duration_s = 24; end
    if nargin < 3 || isempty(targetHz),   targetHz   = 100; end

    REPO = 'C:\Research\aero2'; QPY = 'C:\Users\gandhico\Documents\Quanser\0_libraries\python';
    ENVDIR = 'C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif';
    MATDIR = fullfile(REPO,'matlab'); OUTDIR = fullfile(REPO,'results_matlab');
    if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end
    setenv('PATH', strjoin({ENVDIR, fullfile(ENVDIR,'Library','bin'), fullfile(ENVDIR,'Scripts'), getenv('PATH')}, pathsep));
    try, pyenv(Version = fullfile(ENVDIR,'python.exe'), ExecutionMode = "OutOfProcess"); catch, end
    insert(py.sys.path, int32(0), MATDIR);

    KpP=116.24203523333735; KdP=99.698951398313469; KpY=20.0; KdY=10.0;
    slew=deg2rad(120); Vlim=14.0; pa=deg2rad(25); yr=deg2rad(90); half=duration_s/2;
    pitch_ref = @(t) pa*(4*abs(mod(t/12,1)-0.5)-1);
    yaw_ref   = @(t) (t<half).*(yr*t) + (t>=half).*(yr*half - yr*(t-half));

    fprintf('MATLAB spin360 mission on %s ...\n', backend);
    br = py.matlab_bridge.TwinBridge(QPY, REPO, 200.0, 'mixed', Vlim, backend);

    dt=1/targetHz; Nmax=ceil(duration_s*targetHz)+50; L=zeros(Nmax,6);
    psi_cmd=[]; u=[0 0]; k=0; t0=tic;
    try
        while true
            t=toc(t0); if t>duration_s, break; end
            k=k+1;
            out=double(br.step(u(1),u(2)));  th=out(2); ps=out(3); thd=out(4); psd=out(5);
            if isempty(psi_cmd), psi_cmd=ps; end
            rp=yaw_ref(t); rth=pitch_ref(t);
            to_t=yaw_err_quat(rp,psi_cmd);
            psi_cmd=psi_cmd + max(min(to_t,slew*dt),-slew*dt);
            e_yaw=yaw_err_quat(psi_cmd,ps);
            u_p=max(min(KpP*(rth-th)-KdP*thd, Vlim),-Vlim);
            u_y=max(min(KpY*e_yaw-KdY*psd, Vlim),-Vlim);
            u=[u_p,u_y]; L(k,:)=[t, rth, th, ps, u_p, u_y];
            nextT=k*dt; while toc(t0)<nextT && toc(t0)<=duration_s; end
        end
    catch ME, fprintf(2,'loop error: %s\n',ME.message); end
    br.close(); L=L(1:k,:);

    e_th=L(:,2)-L(:,3);
    summary=struct('backend',backend,'samples',k,'duration',L(end,1),'realizedHz',k/L(end,1), ...
        'pitch_track_rms_deg',rad2deg(sqrt(mean(e_th.^2))), 'yaw_reach_deg',rad2deg(max(abs(L(:,4)))), ...
        'yaw_travel_deg',rad2deg(sum(abs(diff(L(:,4))))));
    stamp=char(datetime('now','Format','yyyyMMdd_HHmmss'));
    T=array2table(L,'VariableNames',{'t','theta_ref','theta','psi','u_pitch','u_yaw'});
    writetable(T, fullfile(OUTDIR,['aero2_spin360_' backend '_' stamp '.csv']));
    save(fullfile(OUTDIR,['aero2_spin360_' backend '_' stamp '.mat']),'L','summary');
    fprintf('[MATLAB spin360 | %s] samples=%d realized=%.1f Hz pitch_track_RMS=%.1f deg yaw_travel=%.0f deg\n', ...
        backend, k, summary.realizedHz, summary.pitch_track_rms_deg, summary.yaw_travel_deg);
end

function e = yaw_err_quat(psi_ref, psi_meas)
    qr=[cos(psi_ref/2);0;0;sin(psi_ref/2)]; qm=[cos(psi_meas/2);0;0;sin(psi_meas/2)];
    qmc=[qm(1);-qm(2);-qm(3);-qm(4)]; qe=quatmul(qr,qmc);
    if qe(1)<0, qe=-qe; end
    e=2*atan2(qe(4),qe(1));
end
function q = quatmul(a,b)
    q=[a(1)*b(1)-a(2)*b(2)-a(3)*b(3)-a(4)*b(4);
       a(1)*b(2)+a(2)*b(1)+a(3)*b(4)-a(4)*b(3);
       a(1)*b(3)-a(2)*b(4)+a(3)*b(1)+a(4)*b(2);
       a(1)*b(4)+a(2)*b(3)-a(3)*b(2)+a(4)*b(1)];
end
