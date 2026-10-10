%% M5.6  DFTs of two real sequences of equal length using a single DFT
%  Method of Section 5.9.1, Mitra 4th ed.  Uses dft2real.m.
clear; clc;
fprintf('=====  M 5.6  Two real DFTs from one complex DFT (Sec. 5.9.1)  =====\n\n');

cases = { ...
  '(a)', [-3 2 4 -6 1 2], [2 -1 3 -4 5 6]; ...
  '(b)', [ 5 -4 -2 6 1 3], [4 -5 5  1 -2 3] };

for c = 1:size(cases,1)
    tag = cases{c,1};  x = cases{c,2};  h = cases{c,3};
    N = length(x);

    [X_dft, H_dft, Xc] = dft2real(x, h);   % one complex DFT -> two real DFTs
    X_ref = fft(x);                        % reference: two separate DFTs
    H_ref = fft(h);

    fprintf('%s  N = %d\n', tag, N);
    fprintf('    x[n] = {%s}\n', strtrim(sprintf(' %g', x)));
    fprintf('    h[n] = {%s}\n', strtrim(sprintf(' %g', h)));
    fprintf('    packed x[n] + j*h[n]  ->  single %d-point DFT\n\n', N);
    fprintf('     k |        Xc[k] (packed)      |          X[k] (DFT of x)     |          H[k] (DFT of h)\n');
    fprintf('    ---+----------------------------+------------------------------+-----------------------------\n');
    for k = 0:N-1
        fprintf('    %2d | %10.4f %+10.4fj | %10.4f %+10.4fj  | %10.4f %+10.4fj\n', k, ...
            real(Xc(k+1)),    imag(Xc(k+1)), ...
            real(X_dft(k+1)), imag(X_dft(k+1)), ...
            real(H_dft(k+1)), imag(H_dft(k+1)));
    end
    eX = max(abs(X_dft - X_ref));  eH = max(abs(H_dft - H_ref));
    fprintf('\n    max error vs. fft(x): %.3e     vs. fft(h): %.3e   -->  %s\n\n\n', ...
            eX, eH, ternary(max(eX,eH) < 1e-10, 'PASS', 'FAIL'));
end

function out = ternary(cond, a, b)
if cond, out = a; else, out = b; end
end
