    function targMap = targDataMap(),

    ;%***********************
    ;% Create Parameter Map *
    ;%***********************
    
        nTotData      = 0; %add to this count as we go
        nTotSects     = 1;
        sectIdxOffset = 0;

        ;%
        ;% Define dummy sections & preallocate arrays
        ;%
        dumSection.nData = -1;
        dumSection.data  = [];

        dumData.logicalSrcIdx = -1;
        dumData.dtTransOffset = -1;

        ;%
        ;% Init/prealloc paramMap
        ;%
        paramMap.nSections           = nTotSects;
        paramMap.sectIdxOffset       = sectIdxOffset;
            paramMap.sections(nTotSects) = dumSection; %prealloc
        paramMap.nTotData            = -1;

        ;%
        ;% Auto data (s_hover_P)
        ;%
            section.nData     = 35;
            section.data(35)  = dumData; %prealloc

                    ;% s_hover_P.A
                    section.data(1).logicalSrcIdx = 0;
                    section.data(1).dtTransOffset = 0;

                    ;% s_hover_P.B
                    section.data(2).logicalSrcIdx = 1;
                    section.data(2).dtTransOffset = 36;

                    ;% s_hover_P.C
                    section.data(3).logicalSrcIdx = 2;
                    section.data(3).dtTransOffset = 60;

                    ;% s_hover_P.CMD_RATE_LIMIT
                    section.data(4).logicalSrcIdx = 3;
                    section.data(4).dtTransOffset = 78;

                    ;% s_hover_P.K
                    section.data(5).logicalSrcIdx = 4;
                    section.data(5).dtTransOffset = 79;

                    ;% s_hover_P.K_AMP
                    section.data(6).logicalSrcIdx = 5;
                    section.data(6).dtTransOffset = 103;

                    ;% s_hover_P.VMAX_AMP
                    section.data(7).logicalSrcIdx = 6;
                    section.data(7).dtTransOffset = 104;

                    ;% s_hover_P.VMAX_DAC
                    section.data(8).logicalSrcIdx = 7;
                    section.data(8).dtTransOffset = 105;

                    ;% s_hover_P.V_bias
                    section.data(9).logicalSrcIdx = 8;
                    section.data(9).dtTransOffset = 106;

                    ;% s_hover_P.SignalGeneratorYaw_Amplitude
                    section.data(10).logicalSrcIdx = 9;
                    section.data(10).dtTransOffset = 107;

                    ;% s_hover_P.SignalGeneratorYaw_Frequency
                    section.data(11).logicalSrcIdx = 10;
                    section.data(11).dtTransOffset = 108;

                    ;% s_hover_P.AmplitudeYawdeg_Gain
                    section.data(12).logicalSrcIdx = 11;
                    section.data(12).dtTransOffset = 109;

                    ;% s_hover_P.ConstantYawdeg_Value
                    section.data(13).logicalSrcIdx = 12;
                    section.data(13).dtTransOffset = 110;

                    ;% s_hover_P.Gain1_Gain
                    section.data(14).logicalSrcIdx = 13;
                    section.data(14).dtTransOffset = 111;

                    ;% s_hover_P.SignalGeneratorPitch_Amplitude
                    section.data(15).logicalSrcIdx = 14;
                    section.data(15).dtTransOffset = 112;

                    ;% s_hover_P.SignalGeneratorPitch_Frequency
                    section.data(16).logicalSrcIdx = 15;
                    section.data(16).dtTransOffset = 113;

                    ;% s_hover_P.AmplitudePitchdeg_Gain
                    section.data(17).logicalSrcIdx = 16;
                    section.data(17).dtTransOffset = 114;

                    ;% s_hover_P.ConstantPitchdeg_Value
                    section.data(18).logicalSrcIdx = 17;
                    section.data(18).dtTransOffset = 115;

                    ;% s_hover_P.Gain1_Gain_d
                    section.data(19).logicalSrcIdx = 18;
                    section.data(19).dtTransOffset = 116;

                    ;% s_hover_P.SignalGeneratorRoll_Amplitude
                    section.data(20).logicalSrcIdx = 19;
                    section.data(20).dtTransOffset = 117;

                    ;% s_hover_P.SignalGeneratorRoll_Frequency
                    section.data(21).logicalSrcIdx = 20;
                    section.data(21).dtTransOffset = 118;

                    ;% s_hover_P.AmplitudeRolldeg_Gain
                    section.data(22).logicalSrcIdx = 21;
                    section.data(22).dtTransOffset = 119;

                    ;% s_hover_P.ConstantRolldeg_Value
                    section.data(23).logicalSrcIdx = 22;
                    section.data(23).dtTransOffset = 120;

                    ;% s_hover_P.Gain1_Gain_a
                    section.data(24).logicalSrcIdx = 23;
                    section.data(24).dtTransOffset = 121;

                    ;% s_hover_P.ConverttoStatewith6Elements_Gai
                    section.data(25).logicalSrcIdx = 24;
                    section.data(25).dtTransOffset = 122;

                    ;% s_hover_P.StateSpace_InitialCondition
                    section.data(26).logicalSrcIdx = 25;
                    section.data(26).dtTransOffset = 140;

                    ;% s_hover_P.DerivativeFilterYaw_A
                    section.data(27).logicalSrcIdx = 26;
                    section.data(27).dtTransOffset = 141;

                    ;% s_hover_P.DerivativeFilterYaw_C
                    section.data(28).logicalSrcIdx = 27;
                    section.data(28).dtTransOffset = 143;

                    ;% s_hover_P.DerivativeFilterPitch_A
                    section.data(29).logicalSrcIdx = 28;
                    section.data(29).dtTransOffset = 145;

                    ;% s_hover_P.DerivativeFilterPitch_C
                    section.data(30).logicalSrcIdx = 29;
                    section.data(30).dtTransOffset = 147;

                    ;% s_hover_P.DerivativeFilterRoll_A
                    section.data(31).logicalSrcIdx = 30;
                    section.data(31).dtTransOffset = 149;

                    ;% s_hover_P.DerivativeFilterRoll_C
                    section.data(32).logicalSrcIdx = 31;
                    section.data(32).dtTransOffset = 151;

                    ;% s_hover_P.VoltageLimit0toVMAX_AMP_LowerSa
                    section.data(33).logicalSrcIdx = 32;
                    section.data(33).dtTransOffset = 153;

                    ;% s_hover_P.Gain_Gain
                    section.data(34).logicalSrcIdx = 33;
                    section.data(34).dtTransOffset = 154;

                    ;% s_hover_P.Gain_Gain_i
                    section.data(35).logicalSrcIdx = 34;
                    section.data(35).dtTransOffset = 155;

            nTotData = nTotData + section.nData;
            paramMap.sections(1) = section;
            clear section


            ;%
            ;% Non-auto Data (parameter)
            ;%


        ;%
        ;% Add final counts to struct.
        ;%
        paramMap.nTotData = nTotData;



    ;%**************************
    ;% Create Block Output Map *
    ;%**************************
    
        nTotData      = 0; %add to this count as we go
        nTotSects     = 1;
        sectIdxOffset = 0;

        ;%
        ;% Define dummy sections & preallocate arrays
        ;%
        dumSection.nData = -1;
        dumSection.data  = [];

        dumData.logicalSrcIdx = -1;
        dumData.dtTransOffset = -1;

        ;%
        ;% Init/prealloc sigMap
        ;%
        sigMap.nSections           = nTotSects;
        sigMap.sectIdxOffset       = sectIdxOffset;
            sigMap.sections(nTotSects) = dumSection; %prealloc
        sigMap.nTotData            = -1;

        ;%
        ;% Auto data (s_hover_B)
        ;%
            section.nData     = 5;
            section.data(5)  = dumData; %prealloc

                    ;% s_hover_B.LimitRateofDesiredAngle
                    section.data(1).logicalSrcIdx = 3;
                    section.data(1).dtTransOffset = 0;

                    ;% s_hover_B.StateSpace
                    section.data(2).logicalSrcIdx = 4;
                    section.data(2).dtTransOffset = 3;

                    ;% s_hover_B.CableGain
                    section.data(3).logicalSrcIdx = 5;
                    section.data(3).dtTransOffset = 6;

                    ;% s_hover_B.Gain
                    section.data(4).logicalSrcIdx = 6;
                    section.data(4).dtTransOffset = 10;

                    ;% s_hover_B.Gain_k
                    section.data(5).logicalSrcIdx = 7;
                    section.data(5).dtTransOffset = 16;

            nTotData = nTotData + section.nData;
            sigMap.sections(1) = section;
            clear section


            ;%
            ;% Non-auto Data (signal)
            ;%


        ;%
        ;% Add final counts to struct.
        ;%
        sigMap.nTotData = nTotData;



    ;%*******************
    ;% Create DWork Map *
    ;%*******************
    
        nTotData      = 0; %add to this count as we go
        nTotSects     = 3;
        sectIdxOffset = 1;

        ;%
        ;% Define dummy sections & preallocate arrays
        ;%
        dumSection.nData = -1;
        dumSection.data  = [];

        dumData.logicalSrcIdx = -1;
        dumData.dtTransOffset = -1;

        ;%
        ;% Init/prealloc dworkMap
        ;%
        dworkMap.nSections           = nTotSects;
        dworkMap.sectIdxOffset       = sectIdxOffset;
            dworkMap.sections(nTotSects) = dumSection; %prealloc
        dworkMap.nTotData            = -1;

        ;%
        ;% Auto data (s_hover_DW)
        ;%
            section.nData     = 2;
            section.data(2)  = dumData; %prealloc

                    ;% s_hover_DW.PrevY
                    section.data(1).logicalSrcIdx = 0;
                    section.data(1).dtTransOffset = 0;

                    ;% s_hover_DW.LastMajorTime
                    section.data(2).logicalSrcIdx = 1;
                    section.data(2).dtTransOffset = 3;

            nTotData = nTotData + section.nData;
            dworkMap.sections(1) = section;
            clear section

            section.nData     = 7;
            section.data(7)  = dumData; %prealloc

                    ;% s_hover_DW.BackMotorV_PWORK.LoggedData
                    section.data(1).logicalSrcIdx = 2;
                    section.data(1).dtTransOffset = 0;

                    ;% s_hover_DW.FrontMotorV_PWORK.LoggedData
                    section.data(2).logicalSrcIdx = 3;
                    section.data(2).dtTransOffset = 1;

                    ;% s_hover_DW.LeftMotorV_PWORK.LoggedData
                    section.data(3).logicalSrcIdx = 4;
                    section.data(3).dtTransOffset = 2;

                    ;% s_hover_DW.RightMotorV_PWORK.LoggedData
                    section.data(4).logicalSrcIdx = 5;
                    section.data(4).dtTransOffset = 3;

                    ;% s_hover_DW.PitchAngledeg_PWORK.LoggedData
                    section.data(5).logicalSrcIdx = 6;
                    section.data(5).dtTransOffset = 4;

                    ;% s_hover_DW.RollAngledeg_PWORK.LoggedData
                    section.data(6).logicalSrcIdx = 7;
                    section.data(6).dtTransOffset = 5;

                    ;% s_hover_DW.YawAngledeg_PWORK.LoggedData
                    section.data(7).logicalSrcIdx = 8;
                    section.data(7).dtTransOffset = 6;

            nTotData = nTotData + section.nData;
            dworkMap.sections(2) = section;
            clear section

            section.nData     = 1;
            section.data(1)  = dumData; %prealloc

                    ;% s_hover_DW.PrevLimited
                    section.data(1).logicalSrcIdx = 9;
                    section.data(1).dtTransOffset = 0;

            nTotData = nTotData + section.nData;
            dworkMap.sections(3) = section;
            clear section


            ;%
            ;% Non-auto Data (dwork)
            ;%


        ;%
        ;% Add final counts to struct.
        ;%
        dworkMap.nTotData = nTotData;



    ;%
    ;% Add individual maps to base struct.
    ;%

    targMap.paramMap  = paramMap;
    targMap.signalMap = sigMap;
    targMap.dworkMap  = dworkMap;

    ;%
    ;% Add checksums to base struct.
    ;%


    targMap.checksum0 = 1521855159;
    targMap.checksum1 = 755050259;
    targMap.checksum2 = 4243003309;
    targMap.checksum3 = 3599964890;

