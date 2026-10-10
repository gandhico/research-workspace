%% M5.2  Circular convolution via the DFT-based approach
%  Mitra 4th ed., Chapter 5.  Uses circconv_dft.m; verified with circonv.m.
clear; clc;
fprintf('=========  M 5.2  Circular convolution via the DFT  =========\n\n');

cases = { ...
  '(a)', [3 2 -2 1 0 1],              [-5 -1 3 -2 4 4]; ...
  '(b)', [3-2j, 4-1j, -2+3j, 1j, 0],  [1-3j, -2-1j, 2+2j, 3, -2+4j]; ...
  '(c)', cos(pi*(0:4)/2),             3.^(0:4) };

for c = 1:size(cases,1)
    tag = cases{c,1};  g = cases{c,2};  h = cases{c,3};
    N = length(g);

    yd = circconv_dft(g, h);     % DFT-based
    yt = circonv(g, h);          % direct, time domain

    fprintf('%s  N = %d\n', tag, N);
    fprintf('    g[n] = %s\n', seqstr(g));
    fprintf('    h[n] = %s\n', seqstr(h));
    fprintf('    y[n] = %s   (DFT based)\n', seqstr(yd));
    fprintf('    max |y_dft - y_circonv| = %.3e   -->  %s\n\n', ...
            max(abs(yd - yt)), ternary(max(abs(yd-yt)) < 1e-10, 'PASS', 'FAIL'));
end

%% local helpers -------------------------------------------------------
function s = seqstr(v)
if isreal(v)
    s = ['{' sprintf(' %g', v) ' }'];
else
    s = '{';
    for i = 1:numel(v)
        re = real(v(i)); im = imag(v(i));
        if abs(im) < 1e-12
            s = [s sprintf(' %g', re)];                      %#ok<AGROW>
        else
            s = [s sprintf(' %g%+gj', re, im)];              %#ok<AGROW>
        end
        if i < numel(v), s = [s ',']; end                    %#ok<AGROW>
    end
    s = [s ' }'];
end
end

function out = ternary(cond, a, b)
if cond, out = a; else, out = b; end
end
