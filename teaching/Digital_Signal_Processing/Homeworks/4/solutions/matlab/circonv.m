function y = circonv(x, h)
%CIRCONV  N-point circular convolution computed directly in the time domain.
%
%   y = CIRCONV(x,h) evaluates
%
%       y[n] = sum_{m=0}^{N-1} x[m] * h[<n-m>_N],    0 <= n <= N-1
%
%   from the definition, with no transform.  Used as the independent check
%   for CIRCCONV_DFT in Problem M5.2.
%
%   This is a stand-alone equivalent of the circonv.m M-file distributed
%   with Mitra 4th ed.

x = x(:).';  h = h(:).';
N = length(x);
if length(h) ~= N
    error('circonv:lengthMismatch', ...
          'Sequences must have equal length (x: %d, h: %d).', N, length(h));
end

y = zeros(1, N);
if isreal(x) && isreal(h), y = real(y); end

for n = 0:N-1
    acc = 0;
    for m = 0:N-1
        acc = acc + x(m+1) * h(mod(n-m, N) + 1);
    end
    y(n+1) = acc;
end
end
