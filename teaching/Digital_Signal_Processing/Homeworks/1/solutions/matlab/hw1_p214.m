%HW1_P214  Problem 2.14 -- location and value of the largest sample of
%          y[n] = x[n] (*) h[n]  with  x[n] = n (0<=n<=N-1),
%                                      h[n] = n (0<=n<=N-3).
%
%   Compares the closed-form prediction
%
%       m*    = ( 5 - 2N + sqrt(8N^2 - 24N + 25) ) / 2
%       n_max = ceil(m*) + N - 3
%
%   with the answer obtained by actually convolving.

clc;
fprintf('   N     m*      n_max(pred)  n_max(conv)   y[n_max]     sqrt(2)*N\n');
fprintf('  ---------------------------------------------------------------\n');
for N = [5 6 7 8 9 10 12 15 20 40 100]
    y  = conv(0:N-1, 0:N-3);
    [ymax,k] = max(y);
    nmax_conv = k-1;
    mstar     = (5-2*N+sqrt(8*N^2-24*N+25))/2;
    nmax_pred = ceil(mstar)+N-3;
    fprintf('  %4d  %7.3f   %8d     %8d   %10g   %9.1f\n', ...
            N, mstar, nmax_pred, nmax_conv, ymax, sqrt(2)*N);
end

% Why the peak is NOT at the midpoint: both sequences are ramps, so the
% product x[k]h[n-k] is weighted towards large k.  Asymptotically
% m* -> (sqrt(2)-1)N and n_max -> sqrt(2)*N, i.e. about 71% of the way
% along the support 0..2N-4 rather than 50%.
figure('Name','Problem 2.14');
N = 40;  y = conv(0:N-1, 0:N-3);
stem(0:numel(y)-1, y, 'filled', 'MarkerSize', 3); grid on
[~,k] = max(y);  hold on
plot(k-1, y(k), 'ro', 'MarkerSize', 10, 'LineWidth', 1.5);
xline((numel(y)-1)/2, '--', 'midpoint');
xlabel('Time index n'); ylabel('Amplitude');
title(sprintf('y[n] = x[n] \\circledast h[n], N = %d  (peak at n = %d)', N, k-1));
legend('y[n]','maximum','Location','northwest');
