%%
% Find Total Inertia
Jt = (Jr+mp*r^2)*Jp - mp^2*l^2*r^2;
%Jt = Jr*Jp - mp^2*l^2*r^2;
% 
% State Space Representation
A = [0 0 1 0;
     0 0 0 1;
     0  mp^2*l^2*r*g/Jt    -br*Jp/Jt   -mp*l*r*bp/Jt;
     0  mp*g*l*(Jr+mp*r^2)/Jt     -mp*l*r*br/Jt   -(Jr+mp*r^2)*bp/Jt];
    %0  mp*g*l*Jr/Jt     -mp*l*r*br/Jt   -Jr*bp/Jt];

B = [0; 0; Jp/Jt; mp*l*r/Jt];
C = eye(2,4);
D = zeros(2,1);
% 
% Convert torque input to voltage input
A(3,3) = A(3,3) - km*km/Rm*B(3);
A(4,3) = A(4,3) - km*km/Rm*B(4);
B = km * B / Rm;