"""
    gui_exp04_trirotor_classical.py - classical coaxial Y6 trirotor cascade and allocator.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp04_trirotor_classical.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror Exp04, trirotor_pd.py, coaxial_trirotor.py, and y6_allocation.py; the
    benchmark remains the source of truth.
    """

import numpy as np
import nengo

DT, TAU = 0.001, 0.01
MASS, GRAVITY = 1.412, 9.81
L1, L2, L3 = 0.28, 0.243, 0.14
IXX, IYY, IZZ, IXZ = 0.014965, 0.021915, 0.034433, 0.0
JP, KF, KTAU, OMEGA_MAX = 6e-5, 6.85e-6, 3.35e-7, 900.0
KP_XY, KD_XY = 2.0, 2.6
KP_Z, KD_Z = 9.0, 5.2
KP_PHI, KD_PHI = 1.3, 0.28
KP_THETA, KD_THETA = 1.8, 0.36
KP_PSI, KD_PSI = 1.0, 0.32
TILT_MAX, THRUST_MAX = np.radians(35.0), 2.5*MASS*GRAVITY


def _reference(t):
    return [0.0, 0.0, 1.5, 0.0] if t < 2.0 else [1.0, -0.5, 2.0, np.radians(20.0)]


def _rotation(phi, theta, psi):
    cp,sp,ct,st,cs,ss = np.cos(phi),np.sin(phi),np.cos(theta),np.sin(theta),np.cos(psi),np.sin(psi)
    return np.array([[ct*cs, sp*st*cs-ss*cp, cp*st*cs+sp*ss],
                     [ct*ss, sp*st*ss+cs*cp, cp*st*ss-sp*cs],
                     [-st, sp*ct, cp*ct]])


def _euler_map(phi, theta):
    cp,sp,ct,tt = np.cos(phi),np.sin(phi),np.cos(theta),np.tan(theta)
    return np.array([[1,sp*tt,np.cos(phi)*tt],[0,cp,-sp],[0,sp/ct,cp/ct]])


def _allocate(command):
    T, tx, ty, tz = command
    k1, ky = 1.0/(L1+L3), KF/(6.0*KTAU)
    sb = (L1*T-ty)*k1; front = T-sb
    br = 0.5*(sb-tx/L2); bl = 0.5*(sb+tx/L2); d = ky*tz
    return np.array([.5*br+d,.5*br-d,.5*front+d,.5*front-d,.5*bl+d,.5*bl-d])


def _mixer():
    k1, ky = 1.0/(L1+L3), KF/(6.0*KTAU)
    return np.array([[.5*L1*k1/2,-1/(4*L2),-k1/4,ky],[.5*L1*k1/2,-1/(4*L2),-k1/4,-ky],
                     [.5*(1-L1*k1),0,k1/2,ky],[.5*(1-L1*k1),0,k1/2,-ky],
                     [.5*L1*k1/2,1/(4*L2),-k1/4,ky],[.5*L1*k1/2,1/(4*L2),-k1/4,-ky]])


def _to_omega(t, forces):
    return np.clip(np.sqrt(np.clip(forces,0,None)/KF),0,OMEGA_MAX)


class _TrirotorPlant:
    """Full rigid-body Y6 RK4 plant; six rotor speeds -> 12 states."""
    def __init__(self, dt): self.dt, self.state = dt, np.zeros(12)

    @staticmethod
    def _f(s, omega):
        x,y,z,u,v,w,phi,theta,psi,p,q,r = s
        F = KF*np.asarray(omega)**2; drag = KTAU*np.asarray(omega)**2
        F1,F2,F3,F4,F5,F6 = F; fz = np.sum(F)
        tx = ((F5+F6)-(F1+F2))*L2 + JP*q*((omega[1]+omega[3]+omega[5])-(omega[0]+omega[2]+omega[4]))
        ty = (F3+F4)*L1-(F1+F2+F5+F6)*L3 + JP*p*((omega[0]+omega[2]+omega[4])-(omega[1]+omega[3]+omega[5]))
        tz = (drag[0]+drag[2]+drag[4])-(drag[1]+drag[3]+drag[5])
        out=np.empty(12); out[0:3]=_rotation(phi,theta,psi)@np.array([u,v,w])
        out[3]=r*v-q*w+GRAVITY*np.sin(theta)
        out[4]=p*w-r*u-GRAVITY*np.sin(phi)*np.cos(theta)
        out[5]=q*u-p*v-GRAVITY*np.cos(phi)*np.cos(theta)+fz/MASS
        out[6:9]=_euler_map(phi,theta)@np.array([p,q,r])
        D=IXX*IZZ-IXZ**2
        out[9]=(((-p*q*IXZ+q*r*(IYY-IZZ))*IZZ-(q*r*IXZ+p*q*(IXX-IYY))*IXZ+tx*IZZ-tz*IXZ)/D)
        out[10]=p*r*(IZZ-IXX)/IYY-(r*r-p*p)*IXZ/IYY+ty/IYY
        out[11]=(((q*r*IXZ+p*q*(IXX-IYY))*IXX-(-p*q*IXZ+q*r*(IYY-IZZ))*IXZ+tz*IXX-tx*IXZ)/D)
        return out

    def __call__(self,t,omega):
        h,s=self.dt,self.state; k1=self._f(s,omega); k2=self._f(s+.5*h*k1,omega)
        k3=self._f(s+.5*h*k2,omega); k4=self._f(s+h*k3,omega)
        self.state=s+h*(k1+2*k2+2*k3+k4)/6.0; return self.state


def _world_velocity(t,v): return _rotation(v[0],v[1],v[2])@v[3:6]


def _attitude_desired(t,v):
    ax,ay,psi=v; cp,sp=np.cos(psi),np.sin(psi)
    theta=np.clip((ax*cp+ay*sp)/GRAVITY,-TILT_MAX,TILT_MAX)
    phi=np.clip((ax*sp-ay*cp)/GRAVITY,-TILT_MAX,TILT_MAX)
    return [theta,phi]


def _total_thrust(t,v):
    return float(np.clip((MASS*GRAVITY+v[0])/max(np.cos(v[1])*np.cos(v[2]),.5),0,THRUST_MAX))


model=nengo.Network(label="Exp04 - classical coaxial Y6 trirotor")
with model:
    reference=nengo.Node(_reference,size_out=4,label="reference [x,y,z,yaw]")
    plant=nengo.Node(_TrirotorPlant(DT),size_in=6,size_out=12,label="Y6 plant state (12)")
    world_velocity=nengo.Node(_world_velocity,size_in=6,size_out=3,label="world velocity [vx,vy,vz]")
    nengo.Connection(plant[[6,7,8,3,4,5]],world_velocity,synapse=TAU)
    tracking_error=nengo.Node(size_in=4,label="controller error [ex,ey,ez,eyaw]")
    for i,state_i in enumerate((0,1,2,8)):
        nengo.Connection(reference[i],tracking_error[i],synapse=0)
        nengo.Connection(plant[state_i],tracking_error[i],transform=-1,synapse=0)
    outer_feedback=nengo.Node(lambda t,v:[KP_XY*v[0]-KD_XY*v[1],KP_XY*v[2]-KD_XY*v[3],KP_Z*v[4]-KD_Z*v[5]],
                              size_in=6,size_out=3,label="position feedback [ax,ay,u_fb_z]")
    nengo.Connection(tracking_error[0],outer_feedback[0],synapse=0); nengo.Connection(world_velocity[0],outer_feedback[1],synapse=0)
    nengo.Connection(tracking_error[1],outer_feedback[2],synapse=0); nengo.Connection(world_velocity[1],outer_feedback[3],synapse=0)
    nengo.Connection(tracking_error[2],outer_feedback[4],synapse=0); nengo.Connection(world_velocity[2],outer_feedback[5],synapse=0)
    desired_attitude=nengo.Node(_attitude_desired,size_in=3,size_out=2,label="desired attitude [theta_d,phi_d]")
    nengo.Connection(outer_feedback[0:2],desired_attitude[0:2],synapse=0); nengo.Connection(plant[8],desired_attitude[2],synapse=0)
    total_thrust=nengo.Node(_total_thrust,size_in=3,size_out=1,label="total thrust T")
    nengo.Connection(outer_feedback[2],total_thrust[0],synapse=0); nengo.Connection(plant[[6,7]],total_thrust[1:3],synapse=0)
    attitude_error=nengo.Node(size_in=3,label="attitude/yaw error [ephi,etheta,eyaw]")
    nengo.Connection(desired_attitude[1],attitude_error[0],synapse=0); nengo.Connection(plant[6],attitude_error[0],transform=-1,synapse=0)
    nengo.Connection(desired_attitude[0],attitude_error[1],synapse=0); nengo.Connection(plant[7],attitude_error[1],transform=-1,synapse=0)
    nengo.Connection(tracking_error[3],attitude_error[2],synapse=0)
    attitude_feedback=nengo.Node(lambda t,v:[KP_PHI*v[0]-KD_PHI*v[1],KP_THETA*v[2]-KD_THETA*v[3],KP_PSI*v[4]-KD_PSI*v[5]],
                                 size_in=6,size_out=3,label="attitude feedback [tau_x,tau_y,tau_z]")
    nengo.Connection(attitude_error[0],attitude_feedback[0],synapse=0); nengo.Connection(plant[9],attitude_feedback[1],synapse=0)
    nengo.Connection(attitude_error[1],attitude_feedback[2],synapse=0); nengo.Connection(plant[10],attitude_feedback[3],synapse=0)
    nengo.Connection(attitude_error[2],attitude_feedback[4],synapse=0); nengo.Connection(plant[11],attitude_feedback[5],synapse=0)
    final_command=nengo.Node(size_in=4,label="final virtual command [T,tx,ty,tz]")
    nengo.Connection(total_thrust,final_command[0],synapse=0); nengo.Connection(attitude_feedback,final_command[1:4],synapse=0)
    rotor_forces=nengo.Node(lambda t,v:_allocate(v),size_in=4,size_out=6,label="Y6 allocator F1..F6")
    rotor_command=nengo.Node(_to_omega,size_in=6,size_out=6,label="final rotor command omega1..omega6")
    nengo.Connection(final_command,rotor_forces,synapse=0); nengo.Connection(rotor_forces,rotor_command,synapse=0); nengo.Connection(rotor_command,plant,synapse=0)
    tracking=nengo.Node(size_in=8,label="tracking [x,y,z,yaw,xr,yr,zr,yawr]")
    attitude_tracking=nengo.Node(size_in=6,label="attitude [phi,theta,psi,phi_d,theta_d,psi_d]")
    nengo.Connection(plant[[0,1,2,8]],tracking[0:4],synapse=TAU); nengo.Connection(reference,tracking[4:8],synapse=TAU)
    nengo.Connection(plant[[6,7,8]],attitude_tracking[0:3],synapse=TAU)
    nengo.Connection(desired_attitude[1],attitude_tracking[3],synapse=TAU); nengo.Connection(desired_attitude[0],attitude_tracking[4],synapse=TAU); nengo.Connection(reference[3],attitude_tracking[5],synapse=TAU)
