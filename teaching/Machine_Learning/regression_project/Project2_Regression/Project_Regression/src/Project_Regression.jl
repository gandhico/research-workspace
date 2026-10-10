module Project_Regression

    using Weave, Plots, Polynomials
    export weave, plot, plot!, scatter, scatter!, Polynomial

    include("Problem1.jl")
    using .Problem1
    export noisyLinearMultiDim

    include("Problem2.jl")
    using .Problem2
    export noisySin

    include("Problem3.jl")
    using .Problem3
    export bivariate

    include("Problem4.jl")
    using .Problem4
    export multivariate

    include("Problem5.jl")
    using .Problem5
    export polyfitLS

    include("Problem6.jl")
    using .Problem6
    export polyfitRegLS

end # module Project_Regression
