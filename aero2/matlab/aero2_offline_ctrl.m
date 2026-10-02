%% aero2_offline_ctrl.m — native MATLAB reproduction of the OFFLINE figure.
% PD (linear) vs Backstepping (nonlinear) on square-wave reference tracking.
% Ports the exact Python plant (helicopter_2dof, RK4), controllers, and config
% so the MATLAB result matches the Python offline result to machine precision.
%   State x = [theta, theta_dot, psi, psi_dot];  u = [u_p, u_y];  dt = 0.005 s.
% Outputs: results_paper/figures/fig_ctrl_offline_matlab.png  and
%          results_matlab/offline_{pd,backstepping}.csv  (t,theta,psi,u_p,u_y).
clear; clc;
REPO = 'C:\Research\aero2';
FIGDIR = fullfile(REPO,'results_paper','figures');
CSVDIR = fullfile(REPO,'results_matlab');
if ~exist(FIGDIR,'dir'); mkdir(FIGDIR); end
if ~exist(CSVDIR,'dir'); mkdir(CSVDIR); end

DT   = 0.005;        % loop timestep [s]  (200 Hz)
DUR  = 18.0;         % duration [s]
VLIM = 24.0;         % command clip [V]
N    = round(DUR/DT);% 3600 samples

fprintf('Simulating PD ...\n');       PD = simulate('pd',          N, DT, VLIM);
fprintf('Simulating Backstepping ...\n'); BS = simulate('backstepping', N, DT, VLIM);

% ---- save trajectories (radians) for the Python<->MATLAB cross-check --------
writematrix([PD.t, PD.theta, PD.psi, PD.up, PD.uy], fullfile(CSVDIR,'offline_pd.csv'));
writematrix([BS.t, BS.theta, BS.psi, BS.up, BS.uy], fullfile(CSVDIR,'offline_backstepping.csv'));
fprintf('Saved CSVs to %s\n', CSVDIR);

%% ---- figure (same 2x2 minimal layout as the Python plot) -------------------
blue = [31 119 180]/255;  red = [214 39 40]/255;  d2r = 180/pi;
fig = figure('Visible','off','Color','w','Position',[100 100 1000 600]);
tl = tiledlayout(fig,2,2,'TileSpacing','compact','Padding','compact');

% pitch (top-left)
ax1 = nexttile(tl,1); hold(ax1,'on'); grid(ax1,'on');
plot(ax1, PD.t, PD.reft*d2r, 'k--','LineWidth',1.0);
plot(ax1, PD.t, PD.theta*d2r, 'Color',blue,'LineWidth',1.5);
plot(ax1, BS.t, BS.theta*d2r, 'Color',red, 'LineWidth',1.5);
ylabel(ax1,'pitch \theta [deg]'); xlim(ax1,[0 DUR]); set(ax1,'GridAlpha',0.25);

% yaw (top-right)
ax2 = nexttile(tl,2); hold(ax2,'on'); grid(ax2,'on');
plot(ax2, PD.t, PD.refp*d2r, 'k--','LineWidth',1.0);
plot(ax2, PD.t, PD.psi*d2r, 'Color',blue,'LineWidth',1.5);
plot(ax2, BS.t, BS.psi*d2r, 'Color',red, 'LineWidth',1.5);
ylabel(ax2,'yaw \psi [deg]'); xlim(ax2,[0 DUR]); set(ax2,'GridAlpha',0.25);

% u_theta (bottom-left)
ax3 = nexttile(tl,3); hold(ax3,'on'); grid(ax3,'on');
plot(ax3, PD.t, PD.up, 'Color',blue,'LineWidth',1.5);
plot(ax3, BS.t, BS.up, 'Color',red, 'LineWidth',1.5);
ylabel(ax3,'u_\theta [V]'); xlabel(ax3,'time [s]'); xlim(ax3,[0 DUR]); set(ax3,'GridAlpha',0.25);

% u_psi (bottom-right)
ax4 = nexttile(tl,4); hold(ax4,'on'); grid(ax4,'on');
plot(ax4, PD.t, PD.uy, 'Color',blue,'LineWidth',1.5);
plot(ax4, BS.t, BS.uy, 'Color',red, 'LineWidth',1.5);
ylabel(ax4,'u_\psi [V]'); xlabel(ax4,'time [s]'); xlim(ax4,[0 DUR]); set(ax4,'GridAlpha',0.25);

lg = legend(ax1, {'reference','PD (linear)','Backstepping (nonlinear)'}, ...
    'Orientation','horizontal','FontSize',9,'Box','off');
lg.Layout.Tile = 'north';
title(tl, sprintf('Aero2 reference tracking  |  offline  |  matlab  (%d Hz)', round(1/DT)), ...
    'FontSize',11);

out = fullfile(FIGDIR,'fig_ctrl_offline_matlab.png');
exportgraphics(fig, out, 'Resolution', 220);
fprintf('SAVED %s\n', out);

% quick metrics (RMS tracking error in deg, control effort = mean|u|)
fprintf('PD : pitchRMS=%.4f deg  yawRMS=%.4f deg  effort=%.3f V\n', ...
    rms((PD.theta-PD.reft))*d2r, rms((PD.psi-PD.refp))*d2r, mean(abs([PD.up;PD.uy])));
fprintf('BS : pitchRMS=%.4f deg  yawRMS=%.4f deg  effort=%.3f V\n', ...
    rms((BS.theta-BS.reft))*d2r, rms((BS.psi-BS.refp))*d2r, mean(abs([BS.up;BS.uy])));
fprintf('DONE\n');

%% ========================= local functions ================================
function S = simulate(ctrl, N, dt, vlim)
    % references (Ref 3, Eqs. 3-4)
    Ath = deg2rad(20); Aps = deg2rad(45); fth = 0.05; fps = 0.04;
    % PD gains + derivative filter
    kpP=116.24203523333735; kdP=99.698951398313469;
    kpY=35.8625570008741;   kdY=38.028899215266975;
    wn=100.0; zeta=1.0;
    % backstepping gains — pitch defaults + YAWBOOST yaw gains (matches the
    % approved Python offline run: BS_K1_THETA/K2_THETA + BS_YAWBOOST_K1/K2_PSI)
    k1P=2.0; k2P=3.0; k1Y=4.0; k2Y=3.5;

    x = [0;0;0;0]; t = 0.0;
    % derivative-filter state (pitch, yaw): [x1; x2]
    fp = [0;0]; fy = [0;0];

    T=zeros(N,1); TH=zeros(N,1); PS=zeros(N,1); UP=zeros(N,1); UY=zeros(N,1);
    RT=zeros(N,1); RP=zeros(N,1);

    for k=1:N
        rth = square_ref(t,Ath,fth);
        rps = square_ref(t,Aps,fps);
        theta=x(1); theta_dot=x(2); psi=x(3); psi_dot=x(4);

        if strcmp(ctrl,'pd')
            % read filtered rate BEFORE updating the filter (original ordering)
            rate_th = wn*fp(2);  rate_ps = wn*fy(2);
            e_th = rth - theta;  e_ps = rps - psi;
            up = clip(kpP*e_th - kdP*rate_th, vlim);
            uy = clip(kpY*e_ps - kdY*rate_ps, vlim);
            u = [up; uy];
            % explicit-Euler filter update with measured dt
            fp = deriv_update(fp, theta, dt, wn, zeta);
            fy = deriv_update(fy, psi,   dt, wn, zeta);
        else % backstepping / computed torque
            e_th = theta - rth;  e_ps = psi - rps;
            v = [ -k1P*e_th - k2P*theta_dot ;
                  -k1Y*e_ps - k2Y*psi_dot ];
            u = inverse_dynamics(x, v, vlim);
        end

        T(k)=t; TH(k)=theta; PS(k)=psi; UP(k)=u(1); UY(k)=u(2); RT(k)=rth; RP(k)=rps;
        x = rk4(x, u, dt);
        t = t + dt;
    end
    S = struct('t',T,'theta',TH,'psi',PS,'up',UP,'uy',UY,'reft',RT,'refp',RP);
end

function r = square_ref(t, A, f)
    if mod(f*t, 1.0) < 0.5, r = -A; else, r = A; end
end

function y = clip(v, lim)
    y = min(max(v, -abs(lim)), abs(lim));
end

function fnew = deriv_update(f, value, dt, wn, zeta)
    x1=f(1); x2=f(2);
    x1_dot = wn*x2;
    x2_dot = wn*((value - x1) - 2.0*zeta*x2);
    fnew = [x1 + dt*x1_dot ; x2 + dt*x2_dot];
end

function M = input_matrix(theta)
    DT_ARM=0.16743; KPP=0.00321; KPY=0.00137; KYY=0.00610; KYP=-0.00319;
    JP=23188500.45/1000*0.001^2; JY=23810415.95/1000*0.001^2; MINC=0.25;
    c = cos(theta);
    if abs(c) < MINC
        if c==0, c = MINC; else, c = sign(c)*MINC; end
    end
    M = [ DT_ARM*KPP/JP, DT_ARM*KPY/JP ;
          c*KYP/JY,      c*KYY/JY ];
end

function b = drift(theta, theta_dot, psi_dot)
    KSP=0.00744; DP=0.00199; DY=0.00192;
    JP=23188500.45/1000*0.001^2; JY=23810415.95/1000*0.001^2;
    b = [ (-KSP*sin(theta) - DP*theta_dot)/JP ;
          (-DY*psi_dot)/JY ];
end

function xdot = fdyn(x, u)
    theta=x(1); theta_dot=x(2); psi_dot=x(4);
    accel = drift(theta, theta_dot, psi_dot) + input_matrix(theta)*u;
    xdot = [theta_dot; accel(1); x(4); accel(2)];  % x(4)=psi_dot
end

function u = inverse_dynamics(x, v, vlim)
    theta=x(1); theta_dot=x(2); psi_dot=x(4);
    M = input_matrix(theta);
    b = drift(theta, theta_dot, psi_dot);
    u_raw = M \ (v - b);          % square full-rank -> same as lstsq
    u = clip_vec(u_raw, vlim);
end

function y = clip_vec(v, lim)
    y = min(max(v, -abs(lim)), abs(lim));
end

function xn = rk4(x, u, dt)
    k1 = fdyn(x, u);
    k2 = fdyn(x + 0.5*dt*k1, u);
    k3 = fdyn(x + 0.5*dt*k2, u);
    k4 = fdyn(x + dt*k3, u);
    xn = x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4);
end
