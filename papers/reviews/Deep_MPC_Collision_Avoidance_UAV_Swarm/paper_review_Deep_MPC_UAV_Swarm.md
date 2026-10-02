# Title | Deep Model Predictive Collision Avoidance for UAV Swarm in Dynamic Communication-Denied Environments

## Key words

Deep Model Predictive 
Deep Model Predictive Active Phased (DMAPA)
local optimality-free collision cone algorithm
Deepp Model Predictive Control Algorithm integrating the Transformer

Collision Avoidance

UAV Swarm
multirotor

Dynamic environments

Communication-Denied
Save 

## Abstract

central issue the paper claims: sudden communication interruptions faced by multirotor UAV swarms in dynamic communication-denied environments

contribution: Deep Model Predictive Active Phased (DMAPA) algorithm 

goal: achieve safe and reliable formation obstacle avoidance flight control. 

Methodology: 1) active phased array algorithm, 2) local optimality-free collision cone algorithm, 3) a deep model predictive control algorithm integrating the Transformer network structure with the MPC framework

notes: online learning mechanism, 

HIDL experiment, but in which platform?

## Introduction

APF | Artificial Potential Field algorithm
This algorithm drives the agent to move toward the target while avoiding obstacles by constructing a potential field model. 
However, in complex scenarios, the APF algorithm is prone to oscillation and local optima entrapment. 

Collision cone theory has been proposed for offline obstacle avoidance path planning. 

Improved obstacle avoidance algorithms based on MPC include: integration with APF for agent obstacle avoidance control, combination with deep neural networks for imitation learning-based vehicle collision avoidance control, and utilization of nonlinear MPC for UAV obstacle avoidance. 

obstacle avoidance algorithms based on Hooke's law repulsive forces have effectively resolved the oscillation problems inherent in traditional APG methods. 

Virtual target points, virtual obstacles, offline path planning, and MDP have also achieved significant results in the field of obstacle avoidance control. 

multi-algorithm fusion readily induces force fighting among control commands from constituent algorithms, thereby jeopardizing formation obstacle avoidance flight safety. 

virtual tube algorithm, 

### Contributions

1) An active phase array (APA) algorithm | this algorithm vectorizes obstacle avoidance repulsive forces and integrates a Doppler effect beamforming mechanism induced by flight velocity vectors to achieve main lobe enhancement and sidelobe suppression, thereby improving obstacle avoidance control precision for UAV formations in dynamic obstacle environments.

2) Building upon the active phased array algorithm, a local optimality-free collision cone (LOCC) | this algorithm constructs virtual collision cones in real time and generates dynamic attractive points to guide UAVs in flight along the conical surfaces, thereby effectively circumventing local optimal regions inherent in potential field models

3) A DMPC integrating the transformer encoder with generic model predictive control | this algorithm retains the Transformer encoder for feature extraction and redesigns the generic MPC based on a point-mass model as a differentiable optimization decoder. 
Through an online learning mechanism that dynamically adjusts weight vectors and the model error compensation vector, the algorithm effectively suppressing global model equivalent error, thereby resolving the force fighting problem in multi-algorithm fusion while guaranteeing stable tracking. 

# ChatGPT Research Assistant | Insights