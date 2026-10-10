# Causal memory task: recover delayed input waveform from tiny cell readouts.
include("acc_multisignal_readout.jl")
println("delay_s,gamma,window,readout,active_features,effective_rank,centered_gram_ratio,train_rmse,test_phase077_rmse,test_phase191_rmse,test_mean_rmse,total_test_upcrossings,total_test_occupancies")
for delay in (.02,.05), gamma in (0.,.5,2.)
    train,_,_=simulate(gamma,0.;delay=delay)
    test1,z1,o1=simulate(gamma,.77;delay=delay)
    test2,z2,o2=simulate(gamma,1.91;delay=delay)
    for window in (:cold,:settled), readout in ORDER
        na,nr,ratio,tr,errs=fit_eval(train,(test1,test2),COLS[readout],window)
        @printf("%.3f,%.3f,%s,%s,%d,%d,%.9g,%.9g,%.9g,%.9g,%.9g,%d,%d\n",
                delay,gamma,String(window),String(readout),na,nr,ratio,tr,
                errs[1],errs[2],sqrt((errs[1]^2+errs[2]^2)/2),z1+z2,o1+o2)
    end
end
