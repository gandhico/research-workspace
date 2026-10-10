%HW1_P207  Problem 2.7 -- x1 (*) x2  versus  x3 (*) x4.
%
%   Shows that the identity x1[n](*)x2[n] = x3[n](*)x4[n] fails for the
%   sequence x4 as printed, and holds for the evidently intended x4.

clc;
x1 = [1 0 1 0 1 0 1 0 1 0 1 0 1 0 1];   % 15 samples, ones at even indices
x2 = [1 1];
x3 = [1 1 0 0 0 0 0 0 1 1];
x4_printed  = [1 1 0 0 0 1 1];
x4_intended = [1 0 1 0 1 0 1];

lhs = conv(x1,x2);
fprintf('x1 (*) x2            = %s\n', mat2str(lhs));
fprintf('x3 (*) x4 (printed)  = %s   -> %s\n', mat2str(conv(x3,x4_printed)), ...
        ternary(isequal(conv(x3,x4_printed),lhs),'equal','NOT equal'));
fprintf('x3 (*) x4 (intended) = %s   -> %s\n', mat2str(conv(x3,x4_intended)), ...
        ternary(isequal(conv(x3,x4_intended),lhs),'equal','NOT equal'));

% The reason, in factored form.  Represent each sequence by its z-polynomial
% coefficients and factor the target 1 + z^-1 + ... + z^-15 :
%
%   X1*X2 = (1-z^-16)/(1-z^-1) = (1+z^-1)(1+z^-2)(1+z^-4)(1+z^-8)
%   X3    = (1+z^-1)(1+z^-8)          <- 1s at n = 0,1,8,9
%   X4    = (1+z^-2)(1+z^-4)          <- 1s at n = 0,2,4,6   (intended)
fprintf('\nFactor check: (1+z^-1)(1+z^-2)(1+z^-4)(1+z^-8) = %s\n', ...
        mat2str(conv(conv([1 1],[1 0 1]), conv([1 0 0 0 1],[1 0 0 0 0 0 0 0 1]))));

function s = ternary(c,a,b)
if c, s = a; else, s = b; end
end
