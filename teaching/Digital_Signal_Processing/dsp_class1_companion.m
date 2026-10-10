%% EE 545 - Digital Signal Processing II
%  Class 1 Prep: Foundations Refresher Companion Script
%  Pairs with dsp_class1_guide.md -- run cell by cell (Ctrl+Enter in each %% block)
%  Instructor: Chuck Creusere | Textbook: Mitra, 4th Ed.

close all; clear; clc;

%% 1. Complex exponentials
n = 0:20;
omega = pi/6;                 % normalized frequency (rad/sample)
x = exp(1j*omega*n);

figure('Name','1. Complex Exponential');
subplot(2,1,1); stem(n, real(x)); title('Re\{e^{j\omega n}\}'); xlabel('n');
subplot(2,1,2); stem(n, imag(x)); title('Im\{e^{j\omega n}\}'); xlabel('n');

figure('Name','1b. Unit Circle Trajectory');
plot(real(x), imag(x), 'o-'); axis equal; grid on;
title('Trajectory on the unit circle'); xlabel('Re'); ylabel('Im');

%% 2. Basic sequences: delta[n], u[n], causal exponential
n2 = -5:10;
delta = double(n2 == 0);
u     = double(n2 >= 0);

figure('Name','2. Basic Sequences');
subplot(2,1,1); stem(n2, delta); title('\delta[n]'); xlabel('n'); ylim([-0.2 1.2]);
subplot(2,1,2); stem(n2, u);     title('u[n]');      xlabel('n'); ylim([-0.2 1.2]);

alpha = 0.8;
xexp = (alpha.^n2) .* u;
figure('Name','2b. Causal Exponential');
stem(n2, xexp); title(['x[n] = ' num2str(alpha) '^n u[n]']); xlabel('n');

%% 3. Convolution sum: y[n] = x[n] (x) h[n]
xc = [1 2 3 4];          % length-4 input sequence
hc = [1 1 1];             % length-3 impulse response (3-point moving average)
yc = conv(xc, hc);         % MATLAB's built-in convolution sum

disp('y[n] ='); disp(yc);
fprintf('length(y) = %d, expected %d\n', length(yc), length(xc)+length(hc)-1);

figure('Name','3. Convolution Sum');
stem(0:length(yc)-1, yc); title('y[n] = x[n] conv h[n]'); xlabel('n');

%% 4. DTFT via direct numerical evaluation of X(e^{jw}) = sum x[n] e^{-jwn}
alpha4 = 0.5;
n4 = 0:50;
x4 = alpha4.^n4;                       % causal exponential (Mitra Eq. 3.12)

omega4 = linspace(-pi, pi, 1024);
X4 = zeros(size(omega4));
for k = 1:length(omega4)
    X4(k) = sum(x4 .* exp(-1j*omega4(k)*n4));
end

figure('Name','4. DTFT');
subplot(2,1,1); plot(omega4, abs(X4)); title('|X(e^{j\omega})|'); xlabel('\omega (rad)');
subplot(2,1,2); plot(omega4, angle(X4)); title('\angle X(e^{j\omega})'); xlabel('\omega (rad)');

% If you have the Signal Processing Toolbox, this does the same thing directly:
% [H4, w4] = freqz(1, [1 -alpha4], 1024, 'whole'); figure; plot(w4, abs(H4));

%% 5. z-transform / pole-zero plot (requires Signal Processing Toolbox)
b5 = 1;               % numerator coefficients (feedforward)
a5 = [1 -0.8];         % denominator coefficients -> pole at z = 0.8

try
    figure('Name','5. Pole-Zero Plot');
    zplane(b5, a5); title('Pole-Zero plot of H(z) = 1 / (1 - 0.8 z^{-1})');
catch ME
    warning('zplane requires the Signal Processing Toolbox: %s', ME.message);
end

%% 6a. Aliasing demo
fs_good = 1000;   fs_bad = 60;     % Hz
f0 = 50;                            % Hz, the true tone
t_good = 0:1/fs_good:0.1;
t_bad  = 0:1/fs_bad:0.1;

figure('Name','6a. Aliasing Demo');
plot(t_good, cos(2*pi*f0*t_good), 'b-'); hold on;
stem(t_bad, cos(2*pi*f0*t_bad), 'r', 'filled');
legend('true signal (well-sampled)', ['samples @ ' num2str(fs_bad) ' Hz (< Nyquist)']);
title('Aliasing: undersampling a 50 Hz tone'); xlabel('t (s)');

%% 6b. Bandpass sampling arithmetic (Mitra Sec 3.9, preview of Class 1 material)
OmegaL = 2*pi*40; OmegaH = 2*pi*60;   % rad/s, a 20 Hz-wide band centered at 50 Hz
B = OmegaH - OmegaL;
fprintf('Naive Nyquist rate: %.1f Hz\n', 2*OmegaH/(2*pi));
fprintf('Bandpass-sampling floor (~2B): %.1f Hz\n', 2*B/(2*pi));

%% End of companion script
disp('Done. Cross-reference each section with dsp_class1_guide.md.');
