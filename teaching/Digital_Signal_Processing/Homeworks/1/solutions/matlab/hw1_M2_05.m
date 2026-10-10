%HW1_M2_05  Exercise M2.5 -- verify the result of Example 2.15.
%
%   In this printing, Example 2.15 is "Determination of the fundamental
%   period of a sum of sinusoidal sequences":
%
%       x~[n] = 3*cos(1.3*pi*n) - 4*sin(0.5*pi*n + 0.5)
%
%       1.3*pi*Na = 2*pi*ra  ->  Na = 20  (ra = 13)
%       0.5*pi*Nb = 2*pi*rb  ->  Nb =  4  (rb =  1)
%       N = LCM(20,4) = 20.
%
%   (If your printing numbers the "ambiguity in the discrete-time
%   representation" example as 2.15 instead, that one is verified by
%   hw1_M2_06, which reproduces Figure 2.28.)

clc; close all;

xfun = @(n) 3*cos(1.3*pi*n) - 4*sin(0.5*pi*n + 0.5);

Na = fper(1.3*pi);
Nb = fper(0.5*pi);
Nth = lcm(Na,Nb);
Nnum = measure_period(xfun);

fprintf('component 3*cos(1.3*pi*n)          : Na = %d\n', Na);
fprintf('component -4*sin(0.5*pi*n + 0.5)   : Nb = %d\n', Nb);
fprintf('LCM(Na,Nb)                         : N  = %d   (theory)\n', Nth);
fprintf('smallest N with x[n+N] == x[n]     : N  = %d   (measured)\n', Nnum);
fprintf('\nresult verified : %d\n', Nth == Nnum);

n = 0:3*Nth-1;
figure('Name','M2.5  Example 2.15','Position',[80 120 980 560]);
subplot(3,1,1); stem(n, 3*cos(1.3*pi*n), 'filled','MarkerSize',3); grid on
ylabel('3cos(1.3\pi n)'); title(sprintf('N_a = %d', Na));
subplot(3,1,2); stem(n, -4*sin(0.5*pi*n+0.5), 'filled','MarkerSize',3, ...
                     'Color',[0.85 0.33 0.1]); grid on
ylabel('-4sin(0.5\pi n+0.5)'); title(sprintf('N_b = %d', Nb));
subplot(3,1,3); stem(n, xfun(n), 'filled','MarkerSize',3, ...
                     'Color',[0.47 0.67 0.19]); grid on; hold on
for p = Nth:Nth:max(n), xline(p,'r--','LineWidth',1.2); end
ylabel('x~[n]'); xlabel('Time index n');
title(sprintf('sum:  N = LCM(%d,%d) = %d', Na, Nb, Nth));

% A subtlety worth noting: 1.3*pi is above pi, so 3*cos(1.3*pi*n) is
% indistinguishable from 3*cos(0.7*pi*n) -- which has the same period 20.
fprintf('\ncos(1.3*pi*n) == cos(0.7*pi*n) : %d   (folding about omega = pi)\n', ...
        max(abs(cos(1.3*pi*n) - cos(0.7*pi*n))) < 1e-12);

% ==========================================================================
function N = fper(w)
if w == 0, N = 1; return; end
[num, den] = rat(w/(2*pi), 1e-12);
if num == 0, N = 1; else, N = den; end
end

function N = measure_period(f)
n = 0:2000;  x = f(n);
for N = 1:1000
    if max(abs(x(1:end-N) - x(1+N:end))) < 1e-9, return; end
end
N = NaN;
end
