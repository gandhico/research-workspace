%HW1_M2_04  Exercise M2.4
%   (a) A sinusoidal-sequence generator  x[n] = A*sin(w0*n + phi)  whose
%       length L, amplitude A, angular frequency w0 (0 < w0 < pi) and phase
%       phi (0 <= phi <= 2*pi) are supplied by the user; used to reproduce
%       the family of Figure 2.22.
%   (b) The angular frequencies of Problem 2.40; the period is read off the
%       plot and compared with the theoretical value N = 2*pi*r/w0.
%
%   Run  hw1_M2_04            -> non-interactive demo (parts a and b)
%        hw1_M2_04('ask')     -> prompts for L, A, w0, phi as the problem asks

function hw1_M2_04(mode)
if nargin > 0 && strcmpi(mode,'ask')
    L   = input('Desired length L                : ');
    A   = input('Amplitude A                     : ');
    w0  = input('Angular frequency w0 (0<w0<pi)  : ');
    phi = input('Phase phi (0<=phi<=2*pi)        : ');
    [x,n] = gensin(L,A,w0,phi);
    figure; stem(n,x,'filled'); grid on
    xlabel('Time index n'); ylabel('Amplitude');
    title(sprintf('x[n] = %g sin(%.4g n + %.4g)', A, w0, phi));
    fprintf('fundamental period N = %d\n', fper(w0));
    return
end

clc; close all;

%% (a) the family of Figure 2.22:  x[n] = 1.5*cos(w0*n)  =  1.5*sin(w0*n + pi/2)
w0list = pi*[0 0.1 0.2 0.8 0.9 1 1.1 1.2];
labels = {'0','0.1\pi','0.2\pi','0.8\pi','0.9\pi','\pi','1.1\pi','1.2\pi'};
figure('Name','M2.4(a)  Figure 2.22','Position',[40 40 1000 700]);
for k = 1:8
    [x,n] = gensin(41, 1.5, w0list(k), pi/2);
    subplot(4,2,k); stem(n,x,'filled','MarkerSize',3); grid on
    ylim([-2 2]); ylabel('Amplitude');
    title(sprintf('\\omega_o = %s', labels{k}));
    if k >= 7, xlabel('Time index n'); end
end
sgtitle('Figure 2.22:  x[n] = 1.5 cos(\omega_o n)');

% Note the folding effect:  w0 = 1.2*pi produces exactly the same samples as
% w0 = 2*pi - 1.2*pi = 0.8*pi, and w0 = 1.1*pi the same as 0.9*pi.
[a1,~] = gensin(41,1.5,1.2*pi,pi/2);  [a2,~] = gensin(41,1.5,0.8*pi,pi/2);
fprintf('1.2*pi and 0.8*pi give identical samples : %d\n', max(abs(a1-a2))<1e-12);
[b1,~] = gensin(41,1.5,1.1*pi,pi/2);  [b2,~] = gensin(41,1.5,0.9*pi,pi/2);
fprintf('1.1*pi and 0.9*pi give identical samples : %d\n\n', max(abs(b1-b2))<1e-12);

%% (b) the angular frequencies of Problem 2.40
w0list = pi*[0.3 0.48 0.45 0.525 0.75 0.75];
tags   = {'(a) 0.3\pi','(b) 0.48\pi','(c) 0.45\pi','(d) 0.525\pi', ...
          '(e) 0.75\pi','(f) 0.75\pi'};
fprintf('Problem 2.40 -- fundamental periods\n');
fprintf('   w0/pi    N (theory)   N (from the sequence)\n');
figure('Name','M2.4(b)  Problem 2.40','Position',[80 80 1000 720]);
for k = 1:6
    w0 = w0list(k);
    Nth = fper(w0);
    [x,n] = gensin(3*Nth+1, 1, w0, 0);
    Nnum  = measure_period(@(m) sin(w0*m));
    fprintf('   %6.3f   %8d     %12d   %s\n', w0/pi, Nth, Nnum, ...
            ternary(Nth==Nnum,'PASS','FAIL'));
    subplot(3,2,k); stem(n,x,'filled','MarkerSize',3); grid on; hold on
    for p = Nth:Nth:max(n), xline(p,'r--'); end
    title(sprintf('%s  ->  N = %d', tags{k}, Nth));
    ylabel('Amplitude'); if k>=5, xlabel('Time index n'); end
end
sgtitle('Problem 2.40:  x[n] = sin(\omega_o n), dashed lines one period apart');
end

% ==========================================================================
function [x, n] = gensin(L, A, w0, phi)
%GENSIN  x[n] = A*sin(w0*n + phi) for n = 0:L-1.
n = 0:L-1;
x = A*sin(w0*n + phi);
end

function N = fper(w)
%FPER  Smallest N with w*N = 2*pi*r  (Inf if w/(2*pi) is irrational).
if w == 0, N = 1; return; end
[num, den] = rat(w/(2*pi), 1e-12);
if num == 0, N = 1; else, N = den; end
end

function N = measure_period(f)
n = 0:3000;  x = f(n);
for N = 1:1500
    if max(abs(x(1:end-N) - x(1+N:end))) < 1e-9, return; end
end
N = NaN;
end

function s = ternary(c,a,b)
if c, s = a; else, s = b; end
end
