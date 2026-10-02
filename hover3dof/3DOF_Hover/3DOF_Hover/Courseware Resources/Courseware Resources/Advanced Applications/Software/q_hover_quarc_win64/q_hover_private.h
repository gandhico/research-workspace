/*
 * q_hover_private.h
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "q_hover".
 *
 * Model version              : 24.0
 * Simulink Coder version : 24.1 (R2024a) 19-Nov-2023
 * C source code generated on : Fri Aug 15 14:26:51 2025
 *
 * Target selection: quarc_win64.tlc
 * Note: GRT includes extra infrastructure and instrumentation for prototyping
 * Embedded hardware selection: Intel->x86-64 (Windows64)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#ifndef q_hover_private_h_
#define q_hover_private_h_
#include "rtwtypes.h"
#include "multiword_types.h"
#include "zero_crossing_types.h"
#include "q_hover_types.h"

/* A global buffer for storing error messages (defined in quanser_common library) */
EXTERN char _rt_error_message[512];

/* private model entry point functions */
extern void q_hover_derivatives(void);

#endif                                 /* q_hover_private_h_ */
