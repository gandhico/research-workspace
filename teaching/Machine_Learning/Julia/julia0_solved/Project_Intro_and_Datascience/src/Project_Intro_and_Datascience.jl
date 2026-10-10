# =====================================================================
# Project_Intro_and_Datascience.jl
#
# This is the top-level module for the package. Its name must match both
# the folder name and the "name" field in Project.toml, and the file must
# live in src/.
#
# A module is a namespace: a container that holds its own set of names
# (variables, functions, types) so they cannot collide with names defined
# somewhere else.
#
# There are two separate ideas at work below, and it is worth keeping them
# straight:
#
#   using   -> brings names INTO this module so the code in here can use them
#   export  -> hands names OUT to code that says
#              "using .Project_Intro_and_Datascience" from somewhere else
#
# =====================================================================

module Project_Intro_and_Datascience

    # Bring in the packages this project depends on. Every package named here
    # must also be listed under [deps] in Project.toml, or this line fails.
    #
    #   Plots          -> plotting (plot, scatter, ...)
    #   DelimitedFiles -> reading the text data files in data/ (readdlm)
    #   Weave          -> turning the .jmd files in doc/ into the report
    using Plots, DelimitedFiles, Weave

    # Re-export the handful of functions from those packages that you will
    # actually use. This is a convenience: because they are exported here,
    # you can call plot(...) or readdlm(...) from the REPL or from a script
    # after a single "using .Project_Intro_and_Datascience", instead of
    # having to write "using Plots" in every file.
    #
    # Note that the chapters in doc/ do not depend on this line. The report
    # is woven with mod=Project_Intro_and_Datascience, which evaluates the
    # chapter code INSIDE this module, where the "using" above is already in
    # effect. The export is what makes these names work OUTSIDE the module --
    # in the REPL, and in report/makeReport.jl, which calls weave().
    export plot, plot!, scatter, scatter!, readdlm, weave

    # Each problem lives in its own file and its own submodule. include()
    # pastes the contents of that file in right here, which defines the
    # submodule; the "using .Problem1" that follows then brings that
    # submodule's exported names into this module.
    #
    # The leading dot in ".Problem1" means "a module defined locally, inside
    # this one" as opposed to a registered package downloaded by Pkg.
    #
    # Exporting calculateChange a second time here is what passes it the rest
    # of the way out, to anyone using this package. A name has to be exported
    # at every level it travels through: Problem1 exports it to here, and
    # here exports it to the outside.
    include("Problem1.jl")
    using .Problem1
    export calculateChange

    include("Problem4.jl")
    using .Problem4
    export lostCows

end # module Project_Intro_and_Datascience
