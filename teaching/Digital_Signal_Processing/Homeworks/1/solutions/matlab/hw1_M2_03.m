%HW1_M2_03  Exercise M2.3
%   Generate the periodic sequences of Problem 2.39(b) to 2.39(e) and confirm
%   the fundamental periods derived analytically.
%
%       (b) cos(0.6*pi*n + 0.3*pi)                              N = 10
%       (c) Re{exp(j*pi*n/8)} + Im{exp(j*pi*n/5)}               N = 80
%       (d) 6*sin(0.15*pi*n) - cos(0.12*pi*n + 0.1*pi)          N = 200
%       (e) sin(0.1*pi*n+0.75*pi) - 3*cos(0.8*pi*n+0.2*pi)
%                                       + cos(1.3*pi*n)         N = 20

clc; close all;

seqs = { @(n) cos(0.6*pi*n + 0.3*pi), ...
         @(n) real(exp(1j*pi*n/8)) + imag(exp(1j*pi*n/5)), ...
         @(n) 6*sin(0.15*pi*n) - cos(0.12*pi*n + 0.1*pi), ...
         @(n) sin(0.1*pi*n+0.75*pi) - 3*cos(0.8*pi*n+0.2*pi) + cos(1.3*pi*n) };
names   = {'2.39(b)','2.39(c)','2.39(d)','2.39(e)'};
Ntheory = [10 80 200 20];

figure('Name','M2.3  periodic sequences','Position',[60 60 980 720]);
for k = 1:4
    N = Ntheory(k);
    n = 0:3*N-1;                       % three periods
    x = seqs{k}(n);

    Nmeas = measure_period(seqs{k});   % period found numerically

    subplot(4,1,k);
    stem(n, x, 'filled', 'MarkerSize', 3); grid on; hold on
    for p = N:N:max(n), xline(p, 'r--'); end
    ylabel('Amplitude');
    title(sprintf('%s :  N_{theory} = %d,   N_{measured} = %d   (%s)', ...
          names{k}, N, Nmeas, ternary(N==Nmeas,'agree','DISAGREE')));
    fprintf('%s : theoretical N = %4d, measured N = %4d  -> %s\n', ...
            names{k}, N, Nmeas, ternary(N==Nmeas,'PASS','FAIL'));
end
xlabel('Time index n');

% ==========================================================================
function N = measure_period(f)
%MEASURE_PERIOD  Smallest N>0 with f(n+N) == f(n) for a long stretch of n.
n = 0:2000;
x = f(n);
for N = 1:1000
    if max(abs(x(1:end-N) - x(1+N:end))) < 1e-9
        return
    end
end
N = NaN;                                % aperiodic within the search range
end

function s = ternary(c,a,b)
if c, s = a; else, s = b; end
end
