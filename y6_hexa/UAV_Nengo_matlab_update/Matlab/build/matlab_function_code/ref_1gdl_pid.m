function ref = fcn(t, p)
%#codegen
k = p(6);
amp = p(7);
center = p(8);
q = exp(-k*(t - center));
den = 1.0 + q;
z_ref = amp/den;
dz_ref = amp*k*q/(den*den);
ref = [z_ref; dz_ref];
end
