function summary = aero2_steps_mission(backend, mode, duration_s, targetHz)
%AERO2_STEPS_MISSION  Native MATLAB controller on pitch_yaw_steps via the bridge.
%   mode='pd'  : naive PD both axes (best LINEAR).
%   mode='qpd' : PD pitch + quaternion shortest-path yaw w/ rate-limited slew (NONLINEAR).
%   Saves CSV to results_matlab/. Example: aero2_steps_mission('twin','qpd',24,100)

    if nargin<1||isempty(backend), backend='twin'; end
    if nargin<2||isempty(mode), mode='pd'; end
    if nargin<3||isempty(duration_s), duration_s=24; end
    if nargin<4||isempty(targetHz), targetHz=100; end

    REPO='C:\Research\aero2'; QPY='C:\Users\gandhico\Documents\Quanser\0_libraries\python';
    ENVDIR='C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif';
    MATDIR=fullfile(REPO,'matlab'); OUTDIR=fullfile(REPO,'results_matlab');
    if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end
    setenv('PATH', strjoin({ENVDIR, fullfile(ENVDIR,'Library','bin'), fullfile(ENVDIR,'Scripts'), getenv('PATH')}, pathsep));
    try, pyenv(Version=fullfile(ENVDIR,'python.exe'), ExecutionMode="OutOfProcess"); catch, end
    insert(py.sys.path, int32(0), MATDIR);

    KpP=116.24203523333735; KdP=99.698951398313469;   % pitch PD
    KpYn=35.8625570008741; KdYn=38.028899215266975;   % naive yaw PD (pd mode)
    KpYq=20.0; KdYq=10.0; slew=deg2rad(120);          % quaternion yaw (qpd mode)
    Vlim=14.0;
    PS=[0 0;3 20;8 -20;13 20;18 0]; YS=[0 0;3 90;8 180;13 270;18 90;22 0];
    pref=@(t) deg2rad(PS(find(PS(:,1)<=t,1,'last'),2));
    yref=@(t) deg2rad(YS(find(YS(:,1)<=t,1,'last'),2));
    useq = strcmp(mode,'qpd');

    fprintf('MATLAB steps | %s | %s ...\n', backend, mode);
    br = py.matlab_bridge.TwinBridge(QPY, REPO, 200.0, 'mixed', Vlim, backend);

    dt=1/targetHz; Nmax=ceil(duration_s*targetHz)+50; L=zeros(Nmax,5);
    u=[0 0]; psi_cmd=[]; k=0; t0=tic;
    try
        while true
            t=toc(t0); if t>duration_s, break; end
            k=k+1;
            out=double(br.step(u(1),u(2)));  th=out(2); ps=out(3); thd=out(4); psd=out(5);
            rth=pref(t); rps=yref(t);
            u_p=KpP*(rth-th)-KdP*thd;
            if useq
                if isempty(psi_cmd), psi_cmd=ps; end
                psi_cmd=psi_cmd + max(min(yaw_err_quat(rps,psi_cmd),slew*dt),-slew*dt);
                u_y=KpYq*yaw_err_quat(psi_cmd,ps)-KdYq*psd;
            else
                u_y=KpYn*(rps-ps)-KdYn*psd;   % naive yaw error
            end
            u=[max(min(u_p,Vlim),-Vlim), max(min(u_y,Vlim),-Vlim)];
            L(k,:)=[t, rth, th, rps, ps];
            nextT=k*dt; while toc(t0)<nextT && toc(t0)<=duration_s; end
        end
    catch ME, fprintf(2,'loop error: %s\n',ME.message); end
    br.close(); L=L(1:k,:);

    summary=struct('backend',backend,'mode',mode,'samples',k,'realizedHz',k/L(end,1), ...
        'pitch_rms_deg',rad2deg(sqrt(mean((L(:,2)-L(:,3)).^2))));
    stamp=char(datetime('now','Format','yyyyMMdd_HHmmss'));
    T=array2table(L,'VariableNames',{'t','theta_ref','theta','psi_ref','psi'});
    writetable(T, fullfile(OUTDIR,['steps_' backend '_' mode '_' stamp '.csv']));
    fprintf('[MATLAB steps | %s | %s] samples=%d realized=%.1f Hz pitch_rms=%.1f deg\n', ...
        backend, mode, k, summary.realizedHz, summary.pitch_rms_deg);
end

function e = yaw_err_quat(psi_ref, psi_meas)
    qr=[cos(psi_ref/2);0;0;sin(psi_ref/2)]; qm=[cos(psi_meas/2);0;0;sin(psi_meas/2)];
    qmc=[qm(1);-qm(2);-qm(3);-qm(4)];
    qe=[qr(1)*qmc(1)-qr(2)*qmc(2)-qr(3)*qmc(3)-qr(4)*qmc(4);
        qr(1)*qmc(2)+qr(2)*qmc(1)+qr(3)*qmc(4)-qr(4)*qmc(3);
        qr(1)*qmc(3)-qr(2)*qmc(4)+qr(3)*qmc(1)+qr(4)*qmc(2);
        qr(1)*qmc(4)+qr(2)*qmc(3)-qr(3)*qmc(2)+qr(4)*qmc(1)];
    if qe(1)<0, qe=-qe; end
    e=2*atan2(qe(4),qe(1));
end
