/*
 * s_hover_data.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "s_hover".
 *
 * Model version              : 1.20
 * Simulink Coder version : 24.1 (R2024a) 19-Nov-2023
 * C source code generated on : Mon Jul 14 13:30:44 2025
 *
 * Target selection: quarc_win64.tlc
 * Note: GRT includes extra infrastructure and instrumentation for prototyping
 * Embedded hardware selection: Intel->x86-64 (Windows64)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "s_hover.h"

/* Block parameters (default storage) */
P_s_hover_T s_hover_P = {
  /* Variable: A
   * Referenced by: '<S1>/State-Space'
   */
  { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0, 0.0, 0.0 },

  /* Variable: B
   * Referenced by: '<S1>/State-Space'
   */
  { 0.0, 0.0, 0.0, -0.032595433348324251, 0.42348312960476353, 0.0, 0.0, 0.0,
    0.0, -0.032595433348324251, -0.42348312960476353, 0.0, 0.0, 0.0, 0.0,
    0.032595433348324251, 0.0, 0.42348312960476353, 0.0, 0.0, 0.0,
    0.032595433348324251, 0.0, -0.42348312960476353 },

  /* Variable: C
   * Referenced by: '<S1>/State-Space'
   */
  { 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0 },

  /* Variable: CMD_RATE_LIMIT
   * Referenced by: '<S2>/Limit Rate of Desired Angle'
   */
  1.0471975511965976,

  /* Variable: K
   * Referenced by: '<Root>/Gain'
   */
  { -111.80339887498891, -111.80339887498886, 111.80339887498963,
    111.80339887498951, 132.28756555322951, -132.2875655532296,
    3.9777313617111264E-14, 1.3359172353559403E-13, -9.0050401353987134E-14,
    -6.7537801015490344E-14, 132.28756555322965, -132.28756555322931,
    -41.412755259045184, -41.41275525904517, 41.412755259045262,
    41.412755259045248, 36.226782591268922, -36.226782591268936,
    -5.7188462908587927E-15, 1.0819990308469102E-14, 4.458880494263205E-15,
    -1.1920703800480215E-15, 36.226782591268929, -36.2267825912689 },

  /* Variable: K_AMP
   * Referenced by:
   *   '<S1>/Cable Gain'
   *   '<S1>/Cable Gain Pre-Compensation'
   */
  3.0,

  /* Variable: VMAX_AMP
   * Referenced by: '<Root>/Voltage Limit: 0 to VMAX_AMP'
   */
  24.0,

  /* Variable: VMAX_DAC
   * Referenced by: '<S1>/DACB Limit'
   */
  10.0,

  /* Variable: V_bias
   * Referenced by: '<Root>/Bias Voltage'
   */
  2.0,

  /* Expression: 1
   * Referenced by: '<S2>/Signal Generator: Yaw'
   */
  1.0,

  /* Expression: 0.04
   * Referenced by: '<S2>/Signal Generator: Yaw'
   */
  0.04,

  /* Expression: 5
   * Referenced by: '<S2>/Amplitude: Yaw (deg)'
   */
  5.0,

  /* Expression: 0
   * Referenced by: '<S2>/Constant: Yaw (deg)'
   */
  0.0,

  /* Expression: pi/180
   * Referenced by: '<S6>/Gain1'
   */
  0.017453292519943295,

  /* Expression: 1
   * Referenced by: '<S2>/Signal Generator: Pitch'
   */
  1.0,

  /* Expression: 0.1
   * Referenced by: '<S2>/Signal Generator: Pitch'
   */
  0.1,

  /* Expression: 4
   * Referenced by: '<S2>/Amplitude: Pitch (deg)'
   */
  4.0,

  /* Expression: 0
   * Referenced by: '<S2>/Constant: Pitch (deg)'
   */
  0.0,

  /* Expression: pi/180
   * Referenced by: '<S4>/Gain1'
   */
  0.017453292519943295,

  /* Expression: 1
   * Referenced by: '<S2>/Signal Generator: Roll'
   */
  1.0,

  /* Expression: 0.08
   * Referenced by: '<S2>/Signal Generator: Roll'
   */
  0.08,

  /* Expression: 4
   * Referenced by: '<S2>/Amplitude: Roll (deg)'
   */
  4.0,

  /* Expression: 0
   * Referenced by: '<S2>/Constant: Roll (deg)'
   */
  0.0,

  /* Expression: pi/180
   * Referenced by: '<S5>/Gain1'
   */
  0.017453292519943295,

  /* Expression: [1 0 0; 0 1 0; 0 0 1; 0 0 0; 0 0 0; 0 0 0];
   * Referenced by: '<S2>/Convert to State with 6 Elements'
   */
  { 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
    0.0, 0.0, 0.0 },

  /* Expression: 0
   * Referenced by: '<S1>/State-Space'
   */
  0.0,

  /* Computed Parameter: DerivativeFilterYaw_A
   * Referenced by: '<S1>/Derivative Filter: Yaw'
   */
  { -150.79644737231007, -15791.367041742973 },

  /* Computed Parameter: DerivativeFilterYaw_C
   * Referenced by: '<S1>/Derivative Filter: Yaw'
   */
  { 15791.367041742973, 0.0 },

  /* Computed Parameter: DerivativeFilterPitch_A
   * Referenced by: '<S1>/Derivative Filter: Pitch'
   */
  { -150.79644737231007, -15791.367041742973 },

  /* Computed Parameter: DerivativeFilterPitch_C
   * Referenced by: '<S1>/Derivative Filter: Pitch'
   */
  { 15791.367041742973, 0.0 },

  /* Computed Parameter: DerivativeFilterRoll_A
   * Referenced by: '<S1>/Derivative Filter: Roll'
   */
  { -150.79644737231007, -15791.367041742973 },

  /* Computed Parameter: DerivativeFilterRoll_C
   * Referenced by: '<S1>/Derivative Filter: Roll'
   */
  { 15791.367041742973, 0.0 },

  /* Expression: 0
   * Referenced by: '<Root>/Voltage Limit: 0 to VMAX_AMP'
   */
  0.0,

  /* Expression: 180/pi
   * Referenced by: '<S7>/Gain'
   */
  57.295779513082323,

  /* Expression: 180/pi
   * Referenced by: '<S8>/Gain'
   */
  57.295779513082323
};
