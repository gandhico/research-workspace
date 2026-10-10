%HW1_M2_06  Exercise M2.6
%   Plot a continuous-time sinusoid together with its sampled version and
%   verify Figure 2.28 (the HOLD function keeps both plots on one axis).
%
%   Figure 2.28:  g1(t) = cos(6*pi*t), g2(t) = cos(14*pi*t), g3(t) = cos(26*pi*t)
%   (3 Hz, 7 Hz, 13 Hz) sampled at 10 Hz, i.e. T = 0.1 s.  All three produce
%   exactly the same sequence, because
%
%       g2[n] = cos(1.4*pi*n) = cos((2*pi - 0.6*pi)n) = cos(0.6*pi*n)
%       g3[n] = cos(2.6*pi*n) = cos((2*pi + 0.6*pi)n) = cos(0.6*pi*n).

clc; close all;

T  = 0.1;                 % sampling period, s   (10 Hz sampling rate)
f  = [3 7 13];            % Hz
t  = 0:0.0005:1;          % dense grid for the "continuous-time" curves
n  = 0:round(1/T);        % sample indices covering 0 <= t <= 1

figure('Name','M2.6  Figure 2.28','Position',[80 120 950 520]);
sty = {'-','--','-.'};
for k = 1:3
    plot(t, cos(2*pi*f(k)*t), sty{k}, 'LineWidth', 1.1); hold on
end
plot(n*T, cos(2*pi*f(1)*n*T), 'ko', 'MarkerSize', 8, 'LineWidth', 1.4);
hold off; grid on
xlabel('Time'); ylabel('Amplitude'); ylim([-1.4 1.4]);
legend('g_1(t) = cos(6\pi t)','g_2(t) = cos(14\pi t)','g_3(t) = cos(26\pi t)', ...
       'samples at 10 Hz', 'Location','southoutside','Orientation','horizontal');
title('Ambiguity in the discrete-time representation of continuous-time signals');

%% verification: the three sampled sequences are identical
g = zeros(3, numel(n));
for k = 1:3, g(k,:) = cos(2*pi*f(k)*n*T); end
fprintf('g1[n] : %s\n', mat2str(round(g(1,:),4)));
fprintf('g2[n] : %s\n', mat2str(round(g(2,:),4)));
fprintf('g3[n] : %s\n', mat2str(round(g(3,:),4)));
fprintf('\nall three sampled sequences identical : %d\n', ...
        max(max(abs(diff(g,1,1)))) < 1e-12);

%% the general statement: (10k +/- 3) Hz all alias onto cos(0.6*pi*n)
fprintf('\nfrequencies aliasing onto cos(0.6*pi*n) at a 10 Hz rate:\n');
ref = cos(0.6*pi*n);
for k = 0:4
    for s = [-1 1]
        fk = 10*k + s*3;
        if fk <= 0, continue; end
        same = max(abs(cos(2*pi*fk*n*T) - ref)) < 1e-12;
        fprintf('   %4d Hz -> %s\n', fk, ternary(same,'same sequence','different'));
    end
end

function s = ternary(c,a,b)
if c, s = a; else, s = b; end
end
