/*
 * s_hover.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "s_hover".
 *
 * Model version              : 1.20
 * Simulink Coder version : 24.1 (R2024a) 19-Nov-2023
 * C source code generated on : Mon Jul 14 13:28:55 2025
 *
 * Target selection: quarc_windows.tlc
 * Note: GRT includes extra infrastructure and instrumentation for prototyping
 * Embedded hardware selection: Intel->x86-32 (Windows32)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "s_hover.h"
#include <math.h>
#include "rtwtypes.h"
#include "s_hover_private.h"
#include <string.h>
#include "rt_nonfinite.h"
#include "s_hover_dt.h"

/* Block signals (default storage) */
B_s_hover_T s_hover_B;

/* Continuous states */
X_s_hover_T s_hover_X;

/* Disabled State Vector */
XDis_s_hover_T s_hover_XDis;

/* Block states (default storage) */
DW_s_hover_T s_hover_DW;

/* Real-time model */
static RT_MODEL_s_hover_T s_hover_M_;
RT_MODEL_s_hover_T *const s_hover_M = &s_hover_M_;

/*
 * This function updates continuous states using the ODE1 fixed-step
 * solver algorithm
 */
static void rt_ertODEUpdateContinuousStates(RTWSolverInfo *si )
{
  time_T tnew = rtsiGetSolverStopTime(si);
  time_T h = rtsiGetStepSize(si);
  real_T *x = rtsiGetContStates(si);
  ODE1_IntgData *id = (ODE1_IntgData *)rtsiGetSolverData(si);
  real_T *f0 = id->f[0];
  int_T i;
  int_T nXc = 12;
  rtsiSetSimTimeStep(si,MINOR_TIME_STEP);
  rtsiSetdX(si, f0);
  s_hover_derivatives();
  rtsiSetT(si, tnew);
  for (i = 0; i < nXc; ++i) {
    x[i] += h * f0[i];
  }

  rtsiSetSimTimeStep(si,MAJOR_TIME_STEP);
}

/* Model output function */
void s_hover_output(void)
{
  real_T rtb_ConverttoStatewith6Elemen_0[6];
  real_T rtb_ConverttoStatewith6Elements[6];
  real_T LimitRateofDesiredAngle;
  real_T bufferedInput_idx_1;
  real_T fallValLimit;
  real_T rtb_DerivativeFilterPitch;
  real_T rtb_DerivativeFilterRoll;
  real_T rtb_DerivativeFilterYaw;
  real_T temp;
  int32_T i;
  int32_T i_0;
  boolean_T limitedCache_idx_0;
  boolean_T limitedCache_idx_1;
  boolean_T limitedCache_idx_2;
  if (rtmIsMajorTimeStep(s_hover_M)) {
    /* set solver stop time */
    if (!(s_hover_M->Timing.clockTick0+1)) {
      rtsiSetSolverStopTime(&s_hover_M->solverInfo,
                            ((s_hover_M->Timing.clockTickH0 + 1) *
        s_hover_M->Timing.stepSize0 * 4294967296.0));
    } else {
      rtsiSetSolverStopTime(&s_hover_M->solverInfo,
                            ((s_hover_M->Timing.clockTick0 + 1) *
        s_hover_M->Timing.stepSize0 + s_hover_M->Timing.clockTickH0 *
        s_hover_M->Timing.stepSize0 * 4294967296.0));
    }
  }                                    /* end MajorTimeStep */

  /* Update absolute time of base rate at minor time step */
  if (rtmIsMinorTimeStep(s_hover_M)) {
    s_hover_M->Timing.t[0] = rtsiGetT(&s_hover_M->solverInfo);
  }

  /* SignalGenerator: '<S2>/Signal Generator: Yaw' incorporates:
   *  SignalGenerator: '<S2>/Signal Generator: Pitch'
   *  SignalGenerator: '<S2>/Signal Generator: Roll'
   */
  rtb_DerivativeFilterYaw = s_hover_M->Timing.t[0];
  temp = s_hover_P.SignalGeneratorYaw_Frequency * rtb_DerivativeFilterYaw;

  /* SignalGenerator: '<S2>/Signal Generator: Pitch' */
  rtb_DerivativeFilterPitch = s_hover_P.SignalGeneratorPitch_Frequency *
    rtb_DerivativeFilterYaw;

  /* SignalGenerator: '<S2>/Signal Generator: Roll' */
  rtb_DerivativeFilterYaw *= s_hover_P.SignalGeneratorRoll_Frequency;

  /* SignalGenerator: '<S2>/Signal Generator: Yaw' */
  if (temp - floor(temp) >= 0.5) {
    LimitRateofDesiredAngle = s_hover_P.SignalGeneratorYaw_Amplitude;
  } else {
    LimitRateofDesiredAngle = -s_hover_P.SignalGeneratorYaw_Amplitude;
  }

  /* RateLimiter: '<S2>/Limit Rate of Desired Angle' incorporates:
   *  Constant: '<S2>/Constant: Yaw (deg)'
   *  Gain: '<S2>/Amplitude: Yaw (deg)'
   *  Gain: '<S6>/Gain1'
   *  SignalGenerator: '<S2>/Signal Generator: Yaw'
   *  Sum: '<S2>/Sum1'
   */
  rtb_DerivativeFilterRoll = (s_hover_P.AmplitudeYawdeg_Gain *
    LimitRateofDesiredAngle + s_hover_P.ConstantYawdeg_Value) *
    s_hover_P.Gain1_Gain;

  /* SignalGenerator: '<S2>/Signal Generator: Pitch' */
  if (rtb_DerivativeFilterPitch - floor(rtb_DerivativeFilterPitch) >= 0.5) {
    LimitRateofDesiredAngle = s_hover_P.SignalGeneratorPitch_Amplitude;
  } else {
    LimitRateofDesiredAngle = -s_hover_P.SignalGeneratorPitch_Amplitude;
  }

  /* RateLimiter: '<S2>/Limit Rate of Desired Angle' incorporates:
   *  Constant: '<S2>/Constant: Pitch (deg)'
   *  Gain: '<S2>/Amplitude: Pitch (deg)'
   *  Gain: '<S4>/Gain1'
   *  SignalGenerator: '<S2>/Signal Generator: Pitch'
   *  Sum: '<S2>/Sum'
   */
  bufferedInput_idx_1 = (s_hover_P.AmplitudePitchdeg_Gain *
    LimitRateofDesiredAngle + s_hover_P.ConstantPitchdeg_Value) *
    s_hover_P.Gain1_Gain_d;

  /* SignalGenerator: '<S2>/Signal Generator: Roll' */
  if (rtb_DerivativeFilterYaw - floor(rtb_DerivativeFilterYaw) >= 0.5) {
    LimitRateofDesiredAngle = s_hover_P.SignalGeneratorRoll_Amplitude;
  } else {
    LimitRateofDesiredAngle = -s_hover_P.SignalGeneratorRoll_Amplitude;
  }

  /* RateLimiter: '<S2>/Limit Rate of Desired Angle' incorporates:
   *  Constant: '<S2>/Constant: Roll (deg)'
   *  Gain: '<S2>/Amplitude: Roll (deg)'
   *  Gain: '<S5>/Gain1'
   *  SignalGenerator: '<S2>/Signal Generator: Roll'
   *  Sum: '<S2>/Sum2'
   */
  rtb_DerivativeFilterYaw = (s_hover_P.AmplitudeRolldeg_Gain *
    LimitRateofDesiredAngle + s_hover_P.ConstantRolldeg_Value) *
    s_hover_P.Gain1_Gain_a;
  if (s_hover_DW.LastMajorTime == (rtInf)) {
    /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
    s_hover_B.LimitRateofDesiredAngle[0] = rtb_DerivativeFilterRoll;
    s_hover_B.LimitRateofDesiredAngle[1] = bufferedInput_idx_1;
    s_hover_B.LimitRateofDesiredAngle[2] = rtb_DerivativeFilterYaw;
  } else {
    temp = s_hover_M->Timing.t[0];
    rtb_DerivativeFilterPitch = temp - s_hover_DW.LastMajorTime;
    if (s_hover_DW.LastMajorTime == temp) {
      if (s_hover_DW.PrevLimited[0]) {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        s_hover_B.LimitRateofDesiredAngle[0] = s_hover_DW.PrevY[0];
      } else {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        s_hover_B.LimitRateofDesiredAngle[0] = rtb_DerivativeFilterRoll;
      }

      if (s_hover_DW.PrevLimited[1]) {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        s_hover_B.LimitRateofDesiredAngle[1] = s_hover_DW.PrevY[1];
      } else {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        s_hover_B.LimitRateofDesiredAngle[1] = bufferedInput_idx_1;
      }

      if (s_hover_DW.PrevLimited[2]) {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        s_hover_B.LimitRateofDesiredAngle[2] = s_hover_DW.PrevY[2];
      } else {
        /* RateLimiter: '<S2>/Limit Rate of Desired Angle' */
        s_hover_B.LimitRateofDesiredAngle[2] = rtb_DerivativeFilterYaw;
      }
    } else {
      temp = rtb_DerivativeFilterRoll - s_hover_DW.PrevY[0];
      LimitRateofDesiredAngle = rtb_DerivativeFilterPitch *
        s_hover_P.CMD_RATE_LIMIT;
      if (temp > LimitRateofDesiredAngle) {
        s_hover_B.LimitRateofDesiredAngle[0] = LimitRateofDesiredAngle +
          s_hover_DW.PrevY[0];
        limitedCache_idx_0 = true;
      } else {
        fallValLimit = rtb_DerivativeFilterPitch * -s_hover_P.CMD_RATE_LIMIT;
        if (temp < fallValLimit) {
          s_hover_B.LimitRateofDesiredAngle[0] = s_hover_DW.PrevY[0] +
            fallValLimit;
          limitedCache_idx_0 = true;
        } else {
          s_hover_B.LimitRateofDesiredAngle[0] = rtb_DerivativeFilterRoll;
          limitedCache_idx_0 = false;
        }
      }

      temp = bufferedInput_idx_1 - s_hover_DW.PrevY[1];
      if (temp > LimitRateofDesiredAngle) {
        s_hover_B.LimitRateofDesiredAngle[1] = LimitRateofDesiredAngle +
          s_hover_DW.PrevY[1];
        limitedCache_idx_1 = true;
      } else {
        fallValLimit = rtb_DerivativeFilterPitch * -s_hover_P.CMD_RATE_LIMIT;
        if (temp < fallValLimit) {
          s_hover_B.LimitRateofDesiredAngle[1] = s_hover_DW.PrevY[1] +
            fallValLimit;
          limitedCache_idx_1 = true;
        } else {
          s_hover_B.LimitRateofDesiredAngle[1] = bufferedInput_idx_1;
          limitedCache_idx_1 = false;
        }
      }

      temp = rtb_DerivativeFilterYaw - s_hover_DW.PrevY[2];
      if (temp > LimitRateofDesiredAngle) {
        s_hover_B.LimitRateofDesiredAngle[2] = LimitRateofDesiredAngle +
          s_hover_DW.PrevY[2];
        limitedCache_idx_2 = true;
      } else {
        fallValLimit = rtb_DerivativeFilterPitch * -s_hover_P.CMD_RATE_LIMIT;
        if (temp < fallValLimit) {
          s_hover_B.LimitRateofDesiredAngle[2] = s_hover_DW.PrevY[2] +
            fallValLimit;
          limitedCache_idx_2 = true;
        } else {
          s_hover_B.LimitRateofDesiredAngle[2] = rtb_DerivativeFilterYaw;
          limitedCache_idx_2 = false;
        }
      }

      if (rtsiIsModeUpdateTimeStep(&s_hover_M->solverInfo)) {
        s_hover_DW.PrevLimited[0] = limitedCache_idx_0;
        s_hover_DW.PrevLimited[1] = limitedCache_idx_1;
        s_hover_DW.PrevLimited[2] = limitedCache_idx_2;
      }
    }
  }

  /* Gain: '<S2>/Convert to State with 6 Elements' */
  LimitRateofDesiredAngle = s_hover_B.LimitRateofDesiredAngle[1];
  temp = s_hover_B.LimitRateofDesiredAngle[0];
  rtb_DerivativeFilterYaw = s_hover_B.LimitRateofDesiredAngle[2];

  /* StateSpace: '<S1>/State-Space' */
  rtb_DerivativeFilterPitch = 0.0;
  rtb_DerivativeFilterRoll = 0.0;
  bufferedInput_idx_1 = 0.0;
  for (i = 0; i < 6; i++) {
    /* Gain: '<S2>/Convert to State with 6 Elements' */
    rtb_ConverttoStatewith6Elements[i] =
      (s_hover_P.ConverttoStatewith6Elements_Gai[i + 6] *
       LimitRateofDesiredAngle + s_hover_P.ConverttoStatewith6Elements_Gai[i] *
       temp) + s_hover_P.ConverttoStatewith6Elements_Gai[i + 12] *
      rtb_DerivativeFilterYaw;

    /* StateSpace: '<S1>/State-Space' */
    fallValLimit = s_hover_X.StateSpace_CSTATE[i];
    rtb_DerivativeFilterPitch += s_hover_P.C[i * 3] * fallValLimit;
    rtb_DerivativeFilterRoll += s_hover_P.C[i * 3 + 1] * fallValLimit;
    bufferedInput_idx_1 += s_hover_P.C[i * 3 + 2] * fallValLimit;
  }

  /* StateSpace: '<S1>/State-Space' */
  s_hover_B.StateSpace[2] = bufferedInput_idx_1;
  s_hover_B.StateSpace[1] = rtb_DerivativeFilterRoll;
  s_hover_B.StateSpace[0] = rtb_DerivativeFilterPitch;

  /* TransferFcn: '<S1>/Derivative Filter: Yaw' */
  rtb_DerivativeFilterYaw = s_hover_P.DerivativeFilterYaw_C[0] *
    s_hover_X.DerivativeFilterYaw_CSTATE[0] + s_hover_P.DerivativeFilterYaw_C[1]
    * s_hover_X.DerivativeFilterYaw_CSTATE[1];

  /* TransferFcn: '<S1>/Derivative Filter: Pitch' */
  rtb_DerivativeFilterPitch = s_hover_P.DerivativeFilterPitch_C[0] *
    s_hover_X.DerivativeFilterPitch_CSTATE[0] +
    s_hover_P.DerivativeFilterPitch_C[1] *
    s_hover_X.DerivativeFilterPitch_CSTATE[1];

  /* TransferFcn: '<S1>/Derivative Filter: Roll' */
  rtb_DerivativeFilterRoll = s_hover_P.DerivativeFilterRoll_C[0] *
    s_hover_X.DerivativeFilterRoll_CSTATE[0] + s_hover_P.DerivativeFilterRoll_C
    [1] * s_hover_X.DerivativeFilterRoll_CSTATE[1];

  /* Gain: '<S1>/Cable Gain Pre-Compensation' */
  temp = 1.0 / s_hover_P.K_AMP;

  /* Sum: '<Root>/Sum' */
  rtb_ConverttoStatewith6Elemen_0[0] = rtb_ConverttoStatewith6Elements[0] -
    s_hover_B.StateSpace[0];
  rtb_ConverttoStatewith6Elemen_0[1] = rtb_ConverttoStatewith6Elements[1] -
    s_hover_B.StateSpace[1];
  rtb_ConverttoStatewith6Elemen_0[2] = rtb_ConverttoStatewith6Elements[2] -
    s_hover_B.StateSpace[2];
  rtb_ConverttoStatewith6Elemen_0[3] = rtb_ConverttoStatewith6Elements[3] -
    rtb_DerivativeFilterYaw;
  rtb_ConverttoStatewith6Elemen_0[4] = rtb_ConverttoStatewith6Elements[4] -
    rtb_DerivativeFilterPitch;
  rtb_ConverttoStatewith6Elemen_0[5] = rtb_ConverttoStatewith6Elements[5] -
    rtb_DerivativeFilterRoll;
  for (i = 0; i < 4; i++) {
    /* Sum: '<Root>/Sum1' incorporates:
     *  Constant: '<Root>/Bias Voltage'
     *  Gain: '<Root>/Gain'
     */
    LimitRateofDesiredAngle = 0.0;
    for (i_0 = 0; i_0 < 6; i_0++) {
      LimitRateofDesiredAngle += s_hover_P.K[(i_0 << 2) + i] *
        rtb_ConverttoStatewith6Elemen_0[i_0];
    }

    LimitRateofDesiredAngle += s_hover_P.V_bias;

    /* End of Sum: '<Root>/Sum1' */

    /* Saturate: '<Root>/Voltage Limit: 0 to VMAX_AMP' */
    if (LimitRateofDesiredAngle > s_hover_P.VMAX_AMP) {
      LimitRateofDesiredAngle = s_hover_P.VMAX_AMP;
    } else if (LimitRateofDesiredAngle <
               s_hover_P.VoltageLimit0toVMAX_AMP_LowerSa) {
      LimitRateofDesiredAngle = s_hover_P.VoltageLimit0toVMAX_AMP_LowerSa;
    }

    /* Saturate: '<S1>/DACB Limit' incorporates:
     *  Gain: '<S1>/Cable Gain Pre-Compensation'
     *  Saturate: '<Root>/Voltage Limit: 0 to VMAX_AMP'
     */
    LimitRateofDesiredAngle *= temp;
    if (LimitRateofDesiredAngle > s_hover_P.VMAX_DAC) {
      LimitRateofDesiredAngle = s_hover_P.VMAX_DAC;
    } else if (LimitRateofDesiredAngle < -s_hover_P.VMAX_DAC) {
      LimitRateofDesiredAngle = -s_hover_P.VMAX_DAC;
    }

    /* Gain: '<S1>/Cable Gain' incorporates:
     *  Saturate: '<Root>/Voltage Limit: 0 to VMAX_AMP'
     *  Saturate: '<S1>/DACB Limit'
     */
    s_hover_B.CableGain[i] = s_hover_P.K_AMP * LimitRateofDesiredAngle;
  }

  if (rtmIsMajorTimeStep(s_hover_M)) {
  }

  for (i = 0; i < 6; i++) {
    /* Gain: '<S7>/Gain' */
    s_hover_B.Gain[i] = s_hover_P.Gain_Gain * rtb_ConverttoStatewith6Elements[i];
  }

  /* Gain: '<S8>/Gain' */
  s_hover_B.Gain_k[0] = s_hover_P.Gain_Gain_i * s_hover_B.StateSpace[0];
  s_hover_B.Gain_k[1] = s_hover_P.Gain_Gain_i * s_hover_B.StateSpace[1];
  s_hover_B.Gain_k[2] = s_hover_P.Gain_Gain_i * s_hover_B.StateSpace[2];
  s_hover_B.Gain_k[3] = s_hover_P.Gain_Gain_i * rtb_DerivativeFilterYaw;
  s_hover_B.Gain_k[4] = s_hover_P.Gain_Gain_i * rtb_DerivativeFilterPitch;
  s_hover_B.Gain_k[5] = s_hover_P.Gain_Gain_i * rtb_DerivativeFilterRoll;
  if (rtmIsMajorTimeStep(s_hover_M)) {
  }
}

/* Model update function */
void s_hover_update(void)
{
  /* Update for RateLimiter: '<S2>/Limit Rate of Desired Angle' */
  s_hover_DW.PrevY[0] = s_hover_B.LimitRateofDesiredAngle[0];
  s_hover_DW.PrevY[1] = s_hover_B.LimitRateofDesiredAngle[1];
  s_hover_DW.PrevY[2] = s_hover_B.LimitRateofDesiredAngle[2];
  s_hover_DW.LastMajorTime = s_hover_M->Timing.t[0];
  if (rtmIsMajorTimeStep(s_hover_M)) {
    rt_ertODEUpdateContinuousStates(&s_hover_M->solverInfo);
  }

  /* Update absolute time for base rate */
  /* The "clockTick0" counts the number of times the code of this task has
   * been executed. The absolute time is the multiplication of "clockTick0"
   * and "Timing.stepSize0". Size of "clockTick0" ensures timer will not
   * overflow during the application lifespan selected.
   * Timer of this task consists of two 32 bit unsigned integers.
   * The two integers represent the low bits Timing.clockTick0 and the high bits
   * Timing.clockTickH0. When the low bit overflows to 0, the high bits increment.
   */
  if (!(++s_hover_M->Timing.clockTick0)) {
    ++s_hover_M->Timing.clockTickH0;
  }

  s_hover_M->Timing.t[0] = rtsiGetSolverStopTime(&s_hover_M->solverInfo);

  {
    /* Update absolute timer for sample time: [0.002s, 0.0s] */
    /* The "clockTick1" counts the number of times the code of this task has
     * been executed. The absolute time is the multiplication of "clockTick1"
     * and "Timing.stepSize1". Size of "clockTick1" ensures timer will not
     * overflow during the application lifespan selected.
     * Timer of this task consists of two 32 bit unsigned integers.
     * The two integers represent the low bits Timing.clockTick1 and the high bits
     * Timing.clockTickH1. When the low bit overflows to 0, the high bits increment.
     */
    if (!(++s_hover_M->Timing.clockTick1)) {
      ++s_hover_M->Timing.clockTickH1;
    }

    s_hover_M->Timing.t[1] = s_hover_M->Timing.clockTick1 *
      s_hover_M->Timing.stepSize1 + s_hover_M->Timing.clockTickH1 *
      s_hover_M->Timing.stepSize1 * 4294967296.0;
  }
}

/* Derivatives for root system: '<Root>' */
void s_hover_derivatives(void)
{
  XDot_s_hover_T *_rtXdot;
  real_T CableGain;
  real_T CableGain_0;
  real_T CableGain_1;
  real_T CableGain_2;
  int_T ci;
  int_T is;
  _rtXdot = ((XDot_s_hover_T *) s_hover_M->derivs);

  /* Derivatives for StateSpace: '<S1>/State-Space' */
  for (is = 0; is < 6; is++) {
    _rtXdot->StateSpace_CSTATE[is] = 0.0;
  }

  for (ci = 0; ci < 6; ci++) {
    for (is = 0; is < 6; is++) {
      _rtXdot->StateSpace_CSTATE[is] += s_hover_P.A[ci * 6 + is] *
        s_hover_X.StateSpace_CSTATE[ci];
    }
  }

  CableGain = s_hover_B.CableGain[0];
  CableGain_0 = s_hover_B.CableGain[1];
  CableGain_1 = s_hover_B.CableGain[2];
  CableGain_2 = s_hover_B.CableGain[3];
  for (is = 0; is < 6; is++) {
    _rtXdot->StateSpace_CSTATE[is] = (((s_hover_P.B[is] * CableGain +
      _rtXdot->StateSpace_CSTATE[is]) + s_hover_P.B[is + 6] * CableGain_0) +
      s_hover_P.B[is + 12] * CableGain_1) + s_hover_P.B[is + 18] * CableGain_2;
  }

  /* End of Derivatives for StateSpace: '<S1>/State-Space' */

  /* Derivatives for TransferFcn: '<S1>/Derivative Filter: Yaw' */
  _rtXdot->DerivativeFilterYaw_CSTATE[0] = s_hover_P.DerivativeFilterYaw_A[0] *
    s_hover_X.DerivativeFilterYaw_CSTATE[0];
  _rtXdot->DerivativeFilterYaw_CSTATE[0] += s_hover_P.DerivativeFilterYaw_A[1] *
    s_hover_X.DerivativeFilterYaw_CSTATE[1];
  _rtXdot->DerivativeFilterYaw_CSTATE[1] = s_hover_X.DerivativeFilterYaw_CSTATE
    [0];
  _rtXdot->DerivativeFilterYaw_CSTATE[0] += s_hover_B.StateSpace[0];

  /* Derivatives for TransferFcn: '<S1>/Derivative Filter: Pitch' */
  _rtXdot->DerivativeFilterPitch_CSTATE[0] = s_hover_P.DerivativeFilterPitch_A[0]
    * s_hover_X.DerivativeFilterPitch_CSTATE[0];
  _rtXdot->DerivativeFilterPitch_CSTATE[0] += s_hover_P.DerivativeFilterPitch_A
    [1] * s_hover_X.DerivativeFilterPitch_CSTATE[1];
  _rtXdot->DerivativeFilterPitch_CSTATE[1] =
    s_hover_X.DerivativeFilterPitch_CSTATE[0];
  _rtXdot->DerivativeFilterPitch_CSTATE[0] += s_hover_B.StateSpace[1];

  /* Derivatives for TransferFcn: '<S1>/Derivative Filter: Roll' */
  _rtXdot->DerivativeFilterRoll_CSTATE[0] = s_hover_P.DerivativeFilterRoll_A[0] *
    s_hover_X.DerivativeFilterRoll_CSTATE[0];
  _rtXdot->DerivativeFilterRoll_CSTATE[0] += s_hover_P.DerivativeFilterRoll_A[1]
    * s_hover_X.DerivativeFilterRoll_CSTATE[1];
  _rtXdot->DerivativeFilterRoll_CSTATE[1] =
    s_hover_X.DerivativeFilterRoll_CSTATE[0];
  _rtXdot->DerivativeFilterRoll_CSTATE[0] += s_hover_B.StateSpace[2];
}

/* Model initialize function */
void s_hover_initialize(void)
{
  {
    int_T is;

    /* InitializeConditions for RateLimiter: '<S2>/Limit Rate of Desired Angle' */
    s_hover_DW.LastMajorTime = (rtInf);

    /* InitializeConditions for StateSpace: '<S1>/State-Space' */
    for (is = 0; is < 6; is++) {
      s_hover_X.StateSpace_CSTATE[is] = s_hover_P.StateSpace_InitialCondition;
    }

    /* End of InitializeConditions for StateSpace: '<S1>/State-Space' */

    /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Yaw' */
    s_hover_X.DerivativeFilterYaw_CSTATE[0] = 0.0;

    /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Pitch' */
    s_hover_X.DerivativeFilterPitch_CSTATE[0] = 0.0;

    /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Roll' */
    s_hover_X.DerivativeFilterRoll_CSTATE[0] = 0.0;

    /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Yaw' */
    s_hover_X.DerivativeFilterYaw_CSTATE[1] = 0.0;

    /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Pitch' */
    s_hover_X.DerivativeFilterPitch_CSTATE[1] = 0.0;

    /* InitializeConditions for TransferFcn: '<S1>/Derivative Filter: Roll' */
    s_hover_X.DerivativeFilterRoll_CSTATE[1] = 0.0;
  }
}

/* Model terminate function */
void s_hover_terminate(void)
{
  /* (no terminate code required) */
}

/*========================================================================*
 * Start of Classic call interface                                        *
 *========================================================================*/

/* Solver interface called by GRT_Main */
#ifndef USE_GENERATED_SOLVER

void rt_ODECreateIntegrationData(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

void rt_ODEDestroyIntegrationData(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

void rt_ODEUpdateContinuousStates(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

#endif

void MdlOutputs(int_T tid)
{
  s_hover_output();
  UNUSED_PARAMETER(tid);
}

void MdlUpdate(int_T tid)
{
  s_hover_update();
  UNUSED_PARAMETER(tid);
}

void MdlInitializeSizes(void)
{
}

void MdlInitializeSampleTimes(void)
{
}

void MdlInitialize(void)
{
}

void MdlStart(void)
{
  s_hover_initialize();
}

void MdlTerminate(void)
{
  s_hover_terminate();
}

/* Registration function */
RT_MODEL_s_hover_T *s_hover(void)
{
  /* Registration code */

  /* initialize non-finites */
  rt_InitInfAndNaN(sizeof(real_T));

  /* initialize real-time model */
  (void) memset((void *)s_hover_M, 0,
                sizeof(RT_MODEL_s_hover_T));

  {
    /* Setup solver object */
    rtsiSetSimTimeStepPtr(&s_hover_M->solverInfo, &s_hover_M->Timing.simTimeStep);
    rtsiSetTPtr(&s_hover_M->solverInfo, &rtmGetTPtr(s_hover_M));
    rtsiSetStepSizePtr(&s_hover_M->solverInfo, &s_hover_M->Timing.stepSize0);
    rtsiSetdXPtr(&s_hover_M->solverInfo, &s_hover_M->derivs);
    rtsiSetContStatesPtr(&s_hover_M->solverInfo, (real_T **)
                         &s_hover_M->contStates);
    rtsiSetNumContStatesPtr(&s_hover_M->solverInfo,
      &s_hover_M->Sizes.numContStates);
    rtsiSetNumPeriodicContStatesPtr(&s_hover_M->solverInfo,
      &s_hover_M->Sizes.numPeriodicContStates);
    rtsiSetPeriodicContStateIndicesPtr(&s_hover_M->solverInfo,
      &s_hover_M->periodicContStateIndices);
    rtsiSetPeriodicContStateRangesPtr(&s_hover_M->solverInfo,
      &s_hover_M->periodicContStateRanges);
    rtsiSetContStateDisabledPtr(&s_hover_M->solverInfo, (boolean_T**)
      &s_hover_M->contStateDisabled);
    rtsiSetErrorStatusPtr(&s_hover_M->solverInfo, (&rtmGetErrorStatus(s_hover_M)));
    rtsiSetRTModelPtr(&s_hover_M->solverInfo, s_hover_M);
  }

  rtsiSetSimTimeStep(&s_hover_M->solverInfo, MAJOR_TIME_STEP);
  rtsiSetIsMinorTimeStepWithModeChange(&s_hover_M->solverInfo, false);
  rtsiSetIsContModeFrozen(&s_hover_M->solverInfo, false);
  s_hover_M->intgData.f[0] = s_hover_M->odeF[0];
  s_hover_M->contStates = ((real_T *) &s_hover_X);
  s_hover_M->contStateDisabled = ((boolean_T *) &s_hover_XDis);
  s_hover_M->Timing.tStart = (0.0);
  rtsiSetSolverData(&s_hover_M->solverInfo, (void *)&s_hover_M->intgData);
  rtsiSetSolverName(&s_hover_M->solverInfo,"ode1");

  /* Initialize timing info */
  {
    int_T *mdlTsMap = s_hover_M->Timing.sampleTimeTaskIDArray;
    mdlTsMap[0] = 0;
    mdlTsMap[1] = 1;

    /* polyspace +2 MISRA2012:D4.1 [Justified:Low] "s_hover_M points to
       static memory which is guaranteed to be non-NULL" */
    s_hover_M->Timing.sampleTimeTaskIDPtr = (&mdlTsMap[0]);
    s_hover_M->Timing.sampleTimes = (&s_hover_M->Timing.sampleTimesArray[0]);
    s_hover_M->Timing.offsetTimes = (&s_hover_M->Timing.offsetTimesArray[0]);

    /* task periods */
    s_hover_M->Timing.sampleTimes[0] = (0.0);
    s_hover_M->Timing.sampleTimes[1] = (0.002);

    /* task offsets */
    s_hover_M->Timing.offsetTimes[0] = (0.0);
    s_hover_M->Timing.offsetTimes[1] = (0.0);
  }

  rtmSetTPtr(s_hover_M, &s_hover_M->Timing.tArray[0]);

  {
    int_T *mdlSampleHits = s_hover_M->Timing.sampleHitArray;
    mdlSampleHits[0] = 1;
    mdlSampleHits[1] = 1;
    s_hover_M->Timing.sampleHits = (&mdlSampleHits[0]);
  }

  rtmSetTFinal(s_hover_M, 20.0);
  s_hover_M->Timing.stepSize0 = 0.002;
  s_hover_M->Timing.stepSize1 = 0.002;

  /* External mode info */
  s_hover_M->Sizes.checksums[0] = (1521855159U);
  s_hover_M->Sizes.checksums[1] = (755050259U);
  s_hover_M->Sizes.checksums[2] = (4243003309U);
  s_hover_M->Sizes.checksums[3] = (3599964890U);

  {
    static const sysRanDType rtAlwaysEnabled = SUBSYS_RAN_BC_ENABLE;
    static RTWExtModeInfo rt_ExtModeInfo;
    static const sysRanDType *systemRan[1];
    s_hover_M->extModeInfo = (&rt_ExtModeInfo);
    rteiSetSubSystemActiveVectorAddresses(&rt_ExtModeInfo, systemRan);
    systemRan[0] = &rtAlwaysEnabled;
    rteiSetModelMappingInfoPtr(s_hover_M->extModeInfo,
      &s_hover_M->SpecialInfo.mappingInfo);
    rteiSetChecksumsPtr(s_hover_M->extModeInfo, s_hover_M->Sizes.checksums);
    rteiSetTPtr(s_hover_M->extModeInfo, rtmGetTPtr(s_hover_M));
  }

  s_hover_M->solverInfoPtr = (&s_hover_M->solverInfo);
  s_hover_M->Timing.stepSize = (0.002);
  rtsiSetFixedStepSize(&s_hover_M->solverInfo, 0.002);
  rtsiSetSolverMode(&s_hover_M->solverInfo, SOLVER_MODE_SINGLETASKING);

  /* block I/O */
  s_hover_M->blockIO = ((void *) &s_hover_B);

  {
    int32_T i;
    for (i = 0; i < 6; i++) {
      s_hover_B.Gain[i] = 0.0;
    }

    for (i = 0; i < 6; i++) {
      s_hover_B.Gain_k[i] = 0.0;
    }

    s_hover_B.LimitRateofDesiredAngle[0] = 0.0;
    s_hover_B.LimitRateofDesiredAngle[1] = 0.0;
    s_hover_B.LimitRateofDesiredAngle[2] = 0.0;
    s_hover_B.StateSpace[0] = 0.0;
    s_hover_B.StateSpace[1] = 0.0;
    s_hover_B.StateSpace[2] = 0.0;
    s_hover_B.CableGain[0] = 0.0;
    s_hover_B.CableGain[1] = 0.0;
    s_hover_B.CableGain[2] = 0.0;
    s_hover_B.CableGain[3] = 0.0;
  }

  /* parameters */
  s_hover_M->defaultParam = ((real_T *)&s_hover_P);

  /* states (continuous) */
  {
    real_T *x = (real_T *) &s_hover_X;
    s_hover_M->contStates = (x);
    (void) memset((void *)&s_hover_X, 0,
                  sizeof(X_s_hover_T));
  }

  /* disabled states */
  {
    boolean_T *xdis = (boolean_T *) &s_hover_XDis;
    s_hover_M->contStateDisabled = (xdis);
    (void) memset((void *)&s_hover_XDis, 0,
                  sizeof(XDis_s_hover_T));
  }

  /* states (dwork) */
  s_hover_M->dwork = ((void *) &s_hover_DW);
  (void) memset((void *)&s_hover_DW, 0,
                sizeof(DW_s_hover_T));
  s_hover_DW.PrevY[0] = 0.0;
  s_hover_DW.PrevY[1] = 0.0;
  s_hover_DW.PrevY[2] = 0.0;
  s_hover_DW.LastMajorTime = 0.0;

  /* data type transition information */
  {
    static DataTypeTransInfo dtInfo;
    (void) memset((char_T *) &dtInfo, 0,
                  sizeof(dtInfo));
    s_hover_M->SpecialInfo.mappingInfo = (&dtInfo);
    dtInfo.numDataTypes = 19;
    dtInfo.dataTypeSizes = &rtDataTypeSizes[0];
    dtInfo.dataTypeNames = &rtDataTypeNames[0];

    /* Block I/O transition table */
    dtInfo.BTransTable = &rtBTransTable;

    /* Parameters transition table */
    dtInfo.PTransTable = &rtPTransTable;
  }

  /* Initialize Sizes */
  s_hover_M->Sizes.numContStates = (12);/* Number of continuous states */
  s_hover_M->Sizes.numPeriodicContStates = (0);
                                      /* Number of periodic continuous states */
  s_hover_M->Sizes.numY = (0);         /* Number of model outputs */
  s_hover_M->Sizes.numU = (0);         /* Number of model inputs */
  s_hover_M->Sizes.sysDirFeedThru = (0);/* The model is not direct feedthrough */
  s_hover_M->Sizes.numSampTimes = (2); /* Number of sample times */
  s_hover_M->Sizes.numBlocks = (38);   /* Number of blocks */
  s_hover_M->Sizes.numBlockIO = (8);   /* Number of block outputs */
  s_hover_M->Sizes.numBlockPrms = (156);/* Sum of parameter "widths" */
  return s_hover_M;
}

/*========================================================================*
 * End of Classic call interface                                          *
 *========================================================================*/
