%HW2_M4_02  MATLAB Exercise M4.2  (Mitra, 4th ed., Chapter 4)
%   Implement the discrete-time system of Eq. (4.109), Problem 4.11,
%
%           y[n] = 0.5 * ( y[n-1] + x[n]/y[n-1] ),
%
%   and show that for x[n] = alpha*mu[n] with y[-1] = 1 the output converges
%   to sqrt(alpha) as n -> infinity (alpha > 0).
%
%   Why it works: with x[n] = alpha for n >= 0 the recursion is exactly
%   Newton-Raphson applied to f(y) = y^2 - alpha,
%
%           y[n] = y[n-1] - f(y[n-1])/f'(y[n-1]) = 0.5*(y[n-1] + alpha/y[n-1]),
%
%   whose fixed point y = 0.5*(y + alpha/y) gives y^2 = alpha.  Writing
%   e[n] = y[n] - sqrt(alpha),
%
%           e[n] = e[n-1]^2 / (2*y[n-1]),
%
%   so the error squares at every step (quadratic convergence) and, after the
%   first step, e[n] > 0 -- the output approaches sqrt(alpha) from above and
%   never oscillates.
%
%   Run:  matlab -batch hw2_M4_02

clc; close all;

alphas = [0.25 2 9 100 1e4];
N      = 12;                      % samples n = 0 ... N-1
yinit  = 1;                       % y[-1] = 1, as specified

%% ---- Table: y[n] and the error for each alpha --------------------------
for a = alphas
    y = sqrtsys(a*ones(1,N), yinit);          % x[n] = alpha*mu[n]
    fprintf('\nalpha = %g   (sqrt(alpha) = %.12f)\n', a, sqrt(a));
    fprintf('   n        y[n]            |y[n]-sqrt(alpha)|\n');
    for n = 0:N-1
        fprintf('%4d  %18.12f  %18.3e\n', n, y(n+1), abs(y(n+1)-sqrt(a)));
    end
    fprintf('   converged to sqrt(alpha) : %d\n', ...
            abs(y(end)-sqrt(a)) < 1e-12*max(1,sqrt(a)));
end

%% ---- Convergence plots --------------------------------------------------
figure('Name','M4.2  convergence of y[n] to sqrt(alpha)','Position',[60 60 960 420]);

subplot(1,2,1); hold on; grid on
for a = alphas
    y = sqrtsys(a*ones(1,N), yinit);
    stem(0:N-1, y/sqrt(a), 'filled', 'LineWidth', 1);
end
yline(1,'k--'); xlabel('Time index n'); ylabel('y[n] / \surd\alpha');
title('Normalized output  (first samples clipped for large \alpha)');
ylim([0 4]);
legend(arrayfun(@(a) sprintf('\\alpha = %g',a), alphas, 'uni', 0), 'Location','best');

subplot(1,2,2); hold on; grid on
for a = alphas
    y = sqrtsys(a*ones(1,N), yinit);
    e = abs(y - sqrt(a)) + eps;                % +eps so the log plot survives 0
    semilogy(0:N-1, e, 'o-', 'LineWidth', 1);
end
set(gca,'YScale','log');
xlabel('Time index n'); ylabel('|y[n] - \surd\alpha|');
title('Error (note the doubling of correct digits each step)');
legend(arrayfun(@(a) sprintf('\\alpha = %g',a), alphas, 'uni', 0), 'Location','best');

%% ---- Verify the quadratic error recursion e[n] = e[n-1]^2/(2 y[n-1]) ----
a  = 2; y = sqrtsys(a*ones(1,N), yinit); s = sqrt(a);
e  = y - s;
ep = [yinit-s, e(1:end-1)];                    % e[n-1], starting from y[-1]
yp = [yinit,   y(1:end-1)];                    % y[n-1]
fprintf('\ne[n] == e[n-1]^2/(2 y[n-1]) : %d  (max err %.2e)\n', ...
        max(abs(e - ep.^2./(2*yp))) < 1e-12, max(abs(e - ep.^2./(2*yp))));

%% ---- Problem 4.11 follow-ups: the system is nonlinear and time-varying --
% Nonlinear: doubling the input does not double the output.
x  = 4*ones(1,N);
y1 = sqrtsys(x,   yinit);     % -> sqrt(4)  = 2
y2 = sqrtsys(2*x, yinit);     % -> sqrt(8) ~= 2.828, not 2*2 = 4
fprintf('nonlinear  (2x -> 2y fails) : %d   [y=%.4f, y(2x)=%.4f, 2y=%.4f]\n', ...
        abs(y2(end)-2*y1(end)) > 1e-6, y1(end), y2(end), 2*y1(end));

% Time-varying: delaying the input by n0 does not simply delay the output,
% because the stored y[n-1] keeps evolving while the input is zero.
n0 = 3;
xd = [zeros(1,n0) 4*ones(1,N-n0)];
yd = sqrtsys(xd, yinit);
fprintf('time-varying (delay not preserved) : %d\n', ...
        max(abs(yd(n0+1:end) - y1(1:end-n0))) > 1e-6);

%% ========================================================================
function y = sqrtsys(x, yinit)
%SQRTSYS  Eq. (4.109):  y[n] = 0.5*( y[n-1] + x[n]/y[n-1] ),  y[-1] = yinit.
y  = zeros(size(x));
ym = yinit;                                   % y[n-1]
for n = 1:numel(x)
    y(n) = 0.5*(ym + x(n)/ym);
    ym   = y(n);
end
end
