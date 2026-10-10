%HW1_M2_07  Exercise M2.7
%   Verify experimentally that the family of continuous-time sinusoids of
%   Eq. (2.65),
%
%       x_{a,k}(t) = A*cos( +/-(Om_o*t + phi) + k*Om_T*t ),  k = 0,+/-1,+/-2,...
%
%   all lead to the SAME sampled signal x[n] = A*cos(Om_o*T*n + phi),
%   where Om_T = 2*pi/T is the sampling frequency.
%
%   Proof (Eq. 2.66):
%       x_{a,k}(nT) = A*cos( (Om_o + k*Om_T) n T + phi )
%                   = A*cos( Om_o*n*T + phi + 2*pi*k*n )
%                   = A*cos( Om_o*n*T + phi )          since k*n is an integer.
%   The minus sign works too, because cosine is even.

clc; close all;

A    = 1.3;
phi  = 0.7;
T    = 0.05;                  % sampling period, s   -> 20 Hz sampling rate
Om_T = 2*pi/T;                % sampling frequency, rad/s
Om_o = 2*pi*3;                % 3 Hz baseband sinusoid

n    = 0:40;
tn   = n*T;
t    = 0:T/200:max(tn);       % dense grid for the continuous-time curves
ref  = A*cos(Om_o*tn + phi);  % the reference sequence (k = 0)

figure('Name','M2.7  Eq. (2.65)','Position',[70 110 980 560]);
klist = [0 1 2 -1];
sgn   = [1 1 1 -1];           % last one exercises the "-" branch of (2.65)
leg   = cell(1,numel(klist));
for i = 1:numel(klist)
    k  = klist(i);  s = sgn(i);
    xa = @(tt) A*cos( s*(Om_o*tt + phi) + k*Om_T*tt );
    plot(t, xa(t), 'LineWidth', 1.0); hold on
    err = max(abs(xa(tn) - ref));
    leg{i} = sprintf('k = %+d, sign %+d   (max sample error %.2e)', k, s, err);
    fprintf('k = %+d, sign %+d : max |x_{a,k}(nT) - x[n]| = %.3e  -> %s\n', ...
            k, s, err, ternary(err<1e-10,'identical','DIFFERENT'));
end
stem(tn, ref, 'ko', 'filled', 'MarkerSize', 4, 'LineWidth', 1.0);
hold off; grid on; xlim([0 10*T]);
xlabel('Time t (s)'); ylabel('Amplitude');
legend([leg, {'common sampled sequence x[n]'}], ...
       'Location','southoutside');
title(sprintf(['Distinct continuous-time sinusoids of Eq. (2.65) ' ...
               'sharing one sampled sequence  (f_s = %g Hz)'], 1/T));

%% the frequencies involved, in Hz
fprintf('\nsampling rate            : %g Hz\n', 1/T);
fprintf('baseband frequency       : %g Hz\n', Om_o/(2*pi));
fprintf('aliases (k = -2..2)      : ');
fprintf('%g ', (Om_o + klist*Om_T)/(2*pi)); fprintf('Hz\n');
fprintf(['\nEvery one of these continuous-time signals is a different ' ...
         'function of t,\nbut they agree exactly at t = nT.\n']);

function s = ternary(c,a,b)
if c, s = a; else, s = b; end
end
