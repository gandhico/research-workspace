function aero2_twin_ctrl(ctrl, backend, duration_s)
%AERO2_TWIN_CTRL  Native MATLAB PD / Backstepping on square-wave reference
% tracking, driving the QLabs Aero2 digital twin (or hardware) via the bridge.
% SAME control laws as aero2_offline_ctrl.m — only the plant/backend changes
% (offline RK4 model -> real-time QLabs twin). This is the backend-agnostic
% demonstration: the controller code is identical across offline/twin/hardware.
% Logs t,theta,psi,u_p,u_y,ref_theta,ref_psi -> results_matlab/<backend>_<ctrl>.csv
    if nargin<1||isempty(ctrl), ctrl='pd'; end
    if nargin<2||isempty(backend), backend='twin'; end
    if nargin<3||isempty(duration_s), duration_s=18; end

    REPO='C:\Research\aero2'; QPY='C:\Users\gandhico\Documents\Quanser\0_libraries\python';
    ENVDIR='C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif';
    MATDIR=fullfile(REPO,'matlab'); OUTDIR=fullfile(REPO,'results_matlab');
    if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end
    setenv('PATH', strjoin({ENVDIR, fullfile(ENVDIR,'Library','bin'), fullfile(ENVDIR,'Scripts'), getenv('PATH')}, pathsep));
    try, pyenv(Version=fullfile(ENVDIR,'python.exe'), ExecutionMode="OutOfProcess"); catch, end
    insert(py.sys.path, int32(0), MATDIR);

    VLIM=24.0;
    kpP=116.24203523333735; kdP=99.698951398313469;      % PD pitch
    kpY=35.8625570008741;   kdY=38.028899215266975;      % PD yaw
    wn=100.0; zeta=1.0;                                   % derivative filter
    k1P=2.0; k2P=3.0; k1Y=4.0; k2Y=3.5;                  % backstepping (pitch default + yawboost yaw)
    Ath=deg2rad(20); Aps=deg2rad(45); fth=0.05; fps=0.04;

    fprintf('MATLAB %s | %s | reference_tracking ...\n', backend, ctrl);
    br = py.matlab_bridge.TwinBridge(QPY, REPO, 200.0, 'mixed', VLIM, backend);

    Nmax=ceil(duration_s*300)+200; L=zeros(Nmax,7);
    u=[0 0]; fp=[0;0]; fy=[0;0]; k=0; tprev=0; t0=tic;
    isbs = strcmp(ctrl,'backstepping');
    try
        while true
            t=toc(t0); if t>duration_s, break; end
            k=k+1;
            out=double(br.step(u(1),u(2)));   % [t,theta,psi,theta_dot,psi_dot]
            th=out(2); ps=out(3); thd=out(4); psd=out(5);
            dt=t-tprev; if dt<=0, dt=1/200; end; tprev=t;   % measured loop dt
            rth=sqref(t,Ath,fth); rps=sqref(t,Aps,fps);
            rate_th=wn*fp(2); rate_ps=wn*fy(2);      % filtered encoder rates (read before update)
            if isbs
                v1=-k1P*(th-rth)-k2P*rate_th;        % desired virtual accelerations
                v2=-k1Y*(ps-rps)-k2Y*rate_ps;
                uu=inv_dyn(th,rate_th,rate_ps,v1,v2,VLIM);  % least-squares inverse dynamics
                u_p=uu(1); u_y=uu(2);
            else
                u_p=clip(kpP*(rth-th)-kdP*rate_th, VLIM);
                u_y=clip(kpY*(rps-ps)-kdY*rate_ps, VLIM);
            end
            fp=dfilt(fp,th,dt,wn,zeta); fy=dfilt(fy,ps,dt,wn,zeta);   % advance filters every step
            u=[clip(u_p,VLIM), clip(u_y,VLIM)];
            L(k,:)=[t, th, ps, u(1), u(2), rth, rps];
        end
    catch ME, fprintf(2,'loop error: %s\n', ME.message); end
    try, br.close(); catch, end
    L=L(1:k,:);

    d2r=180/pi;
    realizedHz = k / max(L(end,1),eps);
    prms=rad2deg(sqrt(mean((L(:,2)-L(:,6)).^2)));
    yrms=rad2deg(sqrt(mean((L(:,3)-L(:,7)).^2)));
    writematrix(L, fullfile(OUTDIR, ['twin_' ctrl '.csv']));
    fprintf('[MATLAB %s | %s] samples=%d realized=%.1f Hz pitch_rms=%.2f deg yaw_rms=%.2f deg\n', ...
        backend, ctrl, k, realizedHz, prms, yrms);
end

% ---- reference + controller helpers (identical math to the offline script) ----
function r = sqref(t, A, f)
    if mod(f*t,1.0) < 0.5, r=-A; else, r=A; end
end
function y = clip(v, lim)
    y = min(max(v,-abs(lim)), abs(lim));
end
function fnew = dfilt(f, value, dt, wn, zeta)
    % EXACT (matrix-exponential) discretization of the same 2nd-order filter,
    % unconditionally stable at the bridge's ~90 Hz where the explicit-Euler
    % form (used at Python's 200 Hz) diverges -> the platform-rate lesson.
    A=[0 wn; -wn -2.0*zeta*wn]; B=[0; wn];
    Ad=expm(A*dt); Bd=A\((Ad-eye(2))*B);
    fnew = Ad*f + Bd*value;
end
function u = inv_dyn(theta, theta_dot, psi_dot, v1, v2, vlim)
    DT_ARM=0.16743; KPP=0.00321; KPY=0.00137; KYY=0.00610; KYP=-0.00319;
    KSP=0.00744; DP=0.00199; DY=0.00192;
    JP=23188500.45/1000*0.001^2; JY=23810415.95/1000*0.001^2; MINC=0.25;
    c=cos(theta); if abs(c)<MINC, if c==0, c=MINC; else, c=sign(c)*MINC; end; end
    M=[DT_ARM*KPP/JP, DT_ARM*KPY/JP; c*KYP/JY, c*KYY/JY];
    b=[(-KSP*sin(theta)-DP*theta_dot)/JP; (-DY*psi_dot)/JY];
    ur=M\([v1;v2]-b);
    u=[clip(ur(1),vlim), clip(ur(2),vlim)];
end
