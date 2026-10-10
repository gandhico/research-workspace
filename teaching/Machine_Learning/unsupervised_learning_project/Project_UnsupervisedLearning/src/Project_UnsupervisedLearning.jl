module Project_UnsupervisedLearning

    using Images, LinearAlgebra, Plots, Random, SafeTestsets, Statistics, Test, Weave
    export weave, plot, bar, randn, randperm, load

    include("Problem1.jl")
    using .Problem1
    export histo, test

    include("Problem2.jl")
    using .Problem2
    export circGauss

    include("Problem3.jl")
    using .Problem3
    export compDistInd

    include("Problem4.jl")
    using .Problem4
    export myKmeansBatch

    include("Problem5.jl")
    using .Problem5
    export myKmeansOnline 

end # module Project_UnsupervisedLearning
