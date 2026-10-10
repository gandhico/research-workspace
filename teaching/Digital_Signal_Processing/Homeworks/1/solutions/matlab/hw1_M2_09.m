%HW1_M2_09  Exercise M2.9
%   Modify the correlation program to compute the autocorrelation of a
%   sequence corrupted by a uniformly distributed random signal (RAND), and
%   demonstrate that the autocorrelation of the noise-corrupted signal still
%   exhibits a peak at zero lag.
%
%   Why it works:  with  s[n] = x[n] + d[n],  d[n] white and independent of
%   x[n],
%
%       r_ss[l] = r_xx[l] + r_dd[l] + r_xd[l] + r_dx[l]
%               ~ r_xx[l] + (sigma_d^2 * L) * delta[l]      for large L,
%
%   so the noise adds energy ONLY at l = 0 and leaves the periodic structure
%   of r_xx untouched at every other lag.  That is exactly why correlation is
%   the standard tool for finding periodicity buried in noise.

clc; close all;
rng(0);                          % reproducible

L  = 96;                         % sequence length
N  = 8;                          % period of the clean signal
n  = 0:L-1;
x  = cos(2*pi*n/N);              % clean periodic signal
d  = rand(1,L) - 0.5;            % uniform noise on [-0.5, 0.5]
amp = 1.5;                       % noise amplitude multiplier
s  = x + amp*d;                  % noise-corrupted signal

[rxx, lag] = prog_corr_noisy(x, x);
[rss, ~  ] = prog_corr_noisy(s, s);
[rdd, ~  ] = prog_corr_noisy(amp*d, amp*d);

%% the peak at zero lag
[~,k]   = max(rss);
fprintf('sequence length L            : %d\n', L);
fprintf('SNR                          : %.2f dB\n', ...
        10*log10(sum(x.^2)/sum((amp*d).^2)));
fprintf('r_ss peaks at lag            : %d   (expected 0)\n', lag(k));
fprintf('r_ss[0]                      : %.3f\n', rss(lag==0));
fprintf('largest |r_ss| at any l ~= 0 : %.3f\n', max(abs(rss(lag~=0))));
fprintf('r_dd[0] / r_dd elsewhere     : %.3f  vs  %.3f  (noise is white)\n', ...
        rdd(lag==0), max(abs(rdd(lag~=0))));
fprintf(['\nThe period of the underlying signal is still readable from the ' ...
         'side lobes:\n']);
side = rss;  side(abs(lag) < 2) = -Inf;
[~,k2] = max(side);
fprintf('  strongest secondary peak at lag %d   (signal period N = %d)\n', ...
        lag(k2), N);

%% plots
figure('Name','M2.9  autocorrelation of a noise-corrupted signal', ...
       'Position',[60 60 980 720]);
subplot(4,1,1); stem(n,x,'filled','MarkerSize',3); grid on
ylabel('x[n]'); title(sprintf('clean signal, period N = %d', N));
subplot(4,1,2); stem(n,s,'filled','MarkerSize',3,'Color',[0.85 0.33 0.1]); grid on
ylabel('s[n]'); title('signal + uniform noise');
subplot(4,1,3); stem(lag,rxx,'filled','MarkerSize',3); grid on
ylabel('r_{xx}[\ell]'); title('autocorrelation of the clean signal');
subplot(4,1,4); stem(lag,rss,'filled','MarkerSize',3, ...
                     'Color',[0.47 0.67 0.19]); grid on; hold on
plot(0, rss(lag==0), 'ro','MarkerSize',10,'LineWidth',1.5);
ylabel('r_{ss}[\ell]'); xlabel('Lag index \ell');
title('autocorrelation of the noise-corrupted signal: peak at \ell = 0');

%% how the zero-lag peak grows with noise power
fprintf('\n  noise amp   r_ss[0]   max|r_ss[l~=0]|   ratio\n');
for a = [0 0.5 1 2 4 8]
    ss = x + a*(rand(1,L)-0.5);
    [r,lg] = prog_corr_noisy(ss,ss);
    p0 = r(lg==0);  ps = max(abs(r(lg~=0)));
    fprintf('  %8.1f  %8.2f  %14.2f  %7.2f\n', a, p0, ps, p0/ps);
end

% ==========================================================================
function [r, lag] = prog_corr_noisy(x, y)
%PROG_CORR_NOISY  r[l] = sum_n x[n]*y[n-l] for two equal-length, causal
%   sequences (the correlation program with the noise experiment in mind).
r   = conv(x, fliplr(y));
lag = -(numel(y)-1) : (numel(x)-1);
end
