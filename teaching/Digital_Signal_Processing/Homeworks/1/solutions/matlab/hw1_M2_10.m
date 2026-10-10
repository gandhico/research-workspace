%HW1_M2_10  Exercise M2.10
%   Determine and plot the autocorrelation of the causal exponentially
%   decaying sequence  x[n] = alpha^n * mu[n]  for (a) alpha = 0.6 and
%   (b) alpha = 0.8, and compare with the closed form of Problem 2.53(a):
%
%       r_xx[l] = alpha^|l| / (1 - alpha^2).

clc; close all;

alphas = [0.6 0.8];
L      = 200;                       % truncation length (alpha^200 is ~0)
Lplot  = 25;                        % lags to display

figure('Name','M2.10  autocorrelation of alpha^n u[n]','Position',[70 80 980 640]);
for k = 1:2
    a = alphas(k);
    n = 0:L-1;
    x = a.^n;

    r   = conv(x, fliplr(x));
    lag = -(L-1):(L-1);

    theory = a.^abs(lag)/(1-a^2);
    err    = max(abs(r(abs(lag)<=Lplot) - theory(abs(lag)<=Lplot)));

    fprintf('alpha = %.1f\n', a);
    fprintf('   r_xx[0]  measured = %.6f   theory = %.6f\n', ...
            r(lag==0), 1/(1-a^2));
    fprintf('   r_xx[5]  measured = %.6f   theory = %.6f\n', ...
            r(lag==5), a^5/(1-a^2));
    fprintf('   max error over |l| <= %d : %.2e\n', Lplot, err);
    fprintf('   even sequence : %d,  maximum at l = 0 : %d\n\n', ...
            max(abs(r-fliplr(r)))<1e-12, lag(find(r==max(r),1))==0);

    subplot(2,2,2*k-1);
    stem(0:Lplot, x(1:Lplot+1), 'filled','MarkerSize',4); grid on
    xlabel('Time index n'); ylabel('x[n]');
    title(sprintf('x[n] = %.1f^n \\mu[n]', a));

    subplot(2,2,2*k);
    idx = abs(lag) <= Lplot;
    stem(lag(idx), r(idx), 'filled','MarkerSize',4); grid on; hold on
    plot(lag(idx), theory(idx), 'r-', 'LineWidth', 1.1);
    xlabel('Lag index \ell'); ylabel('r_{xx}[\ell]');
    title(sprintf('\\alpha = %.1f:  r_{xx}[0] = 1/(1-\\alpha^2) = %.4f', ...
                  a, 1/(1-a^2)));
    legend('computed','\alpha^{|\ell|}/(1-\alpha^2)','Location','northeast');
end

% Observation: the autocorrelation decays at exactly the same rate as the
% sequence itself (both are geometric with ratio alpha), but it is two-sided
% and even.  A slower decay (alpha = 0.8) gives both a larger peak and a
% wider correlation "width" -- the sequence stays correlated with itself for
% longer, which is the time-domain signature of a narrower bandwidth.
fprintf(['Note: r_xx decays with the same ratio alpha as x[n], is even, ' ...
         'and\npeaks at l = 0 with value E_x = 1/(1-alpha^2).\n']);
