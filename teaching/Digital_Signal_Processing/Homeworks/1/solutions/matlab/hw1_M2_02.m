%HW1_M2_02  Exercise M2.2
%   (a) Use the exponential-sequence generator ("Program 2_2") to reproduce
%       Figures 2.23 and 2.24 of the text.
%   (b) Generate and plot  x[n] = -2.7 * exp((-0.4 + j*pi/6)*n),  0 <= n <= 82.
%
%   PROG_EXPSEQ below is a self-contained equivalent of the text's Program 2_2:
%   it generates  x[n] = K * exp(c*n)  for  0 <= n <= L-1, real or complex.

clc; close all;

%% (a) Figure 2.23 -- complex exponential  x[n] = exp((-1/12 + j*pi/6)*n)
[x, n] = prog_expseq(1, -1/12 + 1j*pi/6, 41);
figure('Name','M2.2(a)  Figure 2.23','Position',[60 400 900 300]);
subplot(1,2,1); stem(n,real(x),'filled'); grid on
xlabel('Time index n'); ylabel('Amplitude'); title('Real part');
subplot(1,2,2); stem(n,imag(x),'filled','Color',[0.85 0.33 0.1]); grid on
xlabel('Time index n'); ylabel('Amplitude'); title('Imaginary part');
sgtitle('Figure 2.23:  x[n] = e^{(-1/12 + j\pi/6)n}');

%% (a) Figure 2.24 -- real exponentials, one growing and one decaying
[xa, na] = prog_expseq(0.2, log(1.2), 36);     % 0.2*(1.2)^n
[xb, nb] = prog_expseq(20,  log(0.9), 36);     % 20*(0.9)^n
figure('Name','M2.2(a)  Figure 2.24','Position',[60 40 900 300]);
subplot(1,2,1); stem(na,xa,'filled'); grid on
xlabel('Time index n'); ylabel('Amplitude'); title('x[n] = 0.2(1.2)^n  (growing)');
subplot(1,2,2); stem(nb,xb,'filled'); grid on
xlabel('Time index n'); ylabel('Amplitude'); title('x[n] = 20(0.9)^n  (decaying)');
sgtitle('Figure 2.24:  real exponential sequences');

%% (b) x[n] = -2.7 * exp((-0.4 + j*pi/6)*n),  0 <= n <= 82
[y, ny] = prog_expseq(-2.7, -0.4 + 1j*pi/6, 83);
figure('Name','M2.2(b)','Position',[500 200 950 620]);
subplot(3,1,1); stem(ny,real(y),'filled','MarkerSize',3); grid on
ylabel('Re\{x[n]\}'); title('x[n] = -2.7 e^{(-0.4 + j\pi/6)n},   0 \leq n \leq 82');
subplot(3,1,2); stem(ny,imag(y),'filled','MarkerSize',3,'Color',[0.85 0.33 0.1]); grid on
ylabel('Im\{x[n]\}');
subplot(3,1,3); stem(ny,abs(y),'filled','MarkerSize',3,'Color',[0.47 0.67 0.19]); grid on
ylabel('|x[n]|'); xlabel('Time index n');

% The real part of the exponent is -0.4, so the envelope is 2.7*e^(-0.4n):
% by n = 20 the amplitude has already fallen below 1e-3 of its initial value.
fprintf('|x[0]|  = %.4f\n', abs(y(1)));
fprintf('|x[20]| = %.3e   (envelope 2.7*exp(-0.4*20) = %.3e)\n', ...
        abs(y(21)), 2.7*exp(-0.4*20));
fprintf('the sequence is numerically zero well before n = 82.\n');

% ==========================================================================
function [x, n] = prog_expseq(K, c, L)
%PROG_EXPSEQ  Exponential sequence generator (equivalent of Program 2_2).
%   [X,N] = PROG_EXPSEQ(K,C,L) returns X[n] = K*exp(C*n) for N = 0:L-1.
%   C real  -> real exponential;  C complex -> complex exponential.
n = 0:L-1;
x = K*exp(c*n);
end
