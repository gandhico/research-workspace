%% M5.10  Fourier-domain filtering  (Example 5.14, Mitra 4th ed.)
%
%  Example 5.14: the narrow-band lowpass signal
%
%       x[n] = 0.1 * n * exp(-0.03*n),      0 <= n <= 255
%
%  is corrupted by high-frequency random noise.  A 256-point DFT is taken,
%  every DFT sample in the band 50 <= k <= 206 is zeroed, and the 256-point
%  IDFT of the result is the filtered signal.  The real part is kept: the
%  zeroed band is conjugate-symmetric about k = 128 (206 = 256 - 50), so the
%  imaginary part is zero apart from round-off.
%
%  Two noise models are run:
%    (A) noise confined to the stopband 50 <= k <= 206 -- the premise of
%        Example 5.14.  The filter removes it essentially completely and the
%        residual error is only the signal's own energy in that band.
%    (B) white noise, spread over the whole band.  The filter can remove only
%        the ~61% of its energy that falls inside the stopband.
clear; clc; close all;
rng(0);                                   % reproducible noise

N  = 256;
n  = 0:N-1;
k1 = 50;                                  % first zeroed DFT index
k2 = 206;                                 % last  zeroed DFT index

%% (1) original signal -------------------------------------------------
x = 0.1 * n .* exp(-0.03*n);

%% (2) header ----------------------------------------------------------
fprintf('=====  M 5.10 : Fourier-domain filtering (Example 5.14)  =====\n\n');
fprintf('  DFT length N                     : %d\n', N);
fprintf('  zeroed DFT band                  : %d <= k <= %d  (%d of %d samples)\n', ...
        k1, k2, k2-k1+1, N);
fprintf('  retained band                    : k = 0..%d and %d..%d\n', k1-1, k2+1, N-1);
fprintf('  equivalent passband              : |w| <= %.4f pi  (%.1f%% of the band)\n', ...
        2*k1/N, 100*2*k1/N);
fprintf('  conjugate-symmetric zeroing?     : %s  (k2 = N - k1 = %d)\n\n', ...
        ternary(k2 == N-k1, 'yes', 'NO'), N-k1);

%% (3) run both noise cases --------------------------------------------
noise = { 'A  high-frequency (band-limited) noise', bandlimited_noise(N, k1, k2, 0.9); ...
          'B  white noise',                         0.9*randn(1,N) };
store = cell(2,1);

for c = 1:2
    tag = noise{c,1};  d = noise{c,2};
    s = x + d;
    [y, S, Y, imres] = fourier_filter(s, k1, k2);

    eBefore = norm(s - x)/norm(x);
    eAfter  = norm(y - x)/norm(x);

    fprintf('  --- case %s ---\n', tag);
    fprintf('     max |imag(IDFT)| (round-off)  : %.3e\n', imres);
    fprintf('     relative error BEFORE filter  : %.4f\n', eBefore);
    fprintf('     relative error AFTER  filter  : %.4f\n', eAfter);
    fprintf('     noise reduction factor        : %.1fx\n', eBefore/eAfter);
    fprintf('     tail ripple, n >= 200         : max |y[n]-x[n]| = %.4f\n\n', ...
            max(abs(y(201:end) - x(201:end))));
    store{c} = struct('s',s,'y',y,'S',S,'Y',Y);
end

fprintf('  The residual ripple at the tail of the filtered response is NOT noise:\n');
fprintf('  the ideal (brick-wall) filter has an infinitely long impulse response,\n');
fprintf('  so sampling its Fourier transform onto 256 DFT points aliases it in time\n');
fprintf('  (Section 5.3.4).  This is the ripple visible in Figure 5.10(c).\n');

%% (4) plots  (reproduces Figure 5.10) ---------------------------------
A = store{1};
figure('Name','M5.10  Fourier-domain filtering','Position',[80 80 900 700]);

subplot(2,2,1); plot(n, x, 'LineWidth',1.2); grid on;
xlabel('n'); ylabel('Amplitude'); title('(a) Original signal'); axis([0 N-1 0 1.3]);

subplot(2,2,2); plot(n, A.s, 'LineWidth',0.8); grid on;
xlabel('n'); ylabel('Amplitude'); title('(b) Noise-corrupted signal'); axis([0 N-1 -3 3]);

subplot(2,2,3); plot(n, A.y, 'LineWidth',1.2); grid on;
xlabel('n'); ylabel('Amplitude'); title('(c) After Fourier-domain filtering'); axis([0 N-1 0 1.3]);

subplot(2,2,4);
plot(n, abs(A.S), 'LineWidth',0.8); hold on; plot(n, abs(A.Y), 'LineWidth',0.8);
xline(k1,'--'); xline(k2,'--'); grid on;
xlabel('k'); ylabel('|DFT|'); title('(d) DFT magnitude: before / after zeroing');
legend('|S[k]|','|Y[k]|','Location','north'); xlim([0 N-1]);

% save a copy of the figure next to the script
try
    exportgraphics(gcf, 'm5_10_figure.png', 'Resolution', 140);
    fprintf('\n  wrote m5_10_figure.png\n');
catch
    fprintf('\n  (could not export the figure)\n');
end

%% local functions -----------------------------------------------------
function d = bandlimited_noise(N, k1, k2, rmsVal)
%BANDLIMITED_NOISE  Real white noise restricted to k1 <= k <= k2.
%  The kept band is conjugate-symmetric (k2 = N - k1), so the result is real.
W = fft(randn(1,N));
W(1:k1)     = 0;          % zero k = 0 .. k1-1
W(k2+2:N)   = 0;          % zero k = k2+1 .. N-1
d = real(ifft(W));
d = d * (rmsVal / sqrt(mean(d.^2)));
end

function [y, S, Y, imres] = fourier_filter(s, k1, k2)
%FOURIER_FILTER  Zero the DFT band k1..k2 and inverse transform.
S = fft(s);
Y = S;
Y(k1+1 : k2+1) = 0;
yc = ifft(Y);
y  = real(yc);
imres = max(abs(imag(yc)));
end

function out = ternary(cond, a, b)
if cond, out = a; else, out = b; end
end
