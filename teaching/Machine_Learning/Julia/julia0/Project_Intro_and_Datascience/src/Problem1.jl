# =====================================================================
# Problem1.jl
#
# Each problem gets its own submodule. Two reasons:
#
#   1) Namespacing. A helper you name "total" in Problem1 cannot clash with
#      a different "total" in Problem4, because each lives in its own module.
#   2) Structure. The file you edit to solve a problem is separate from the
#      file that assembles the package.
#
# This file is not loaded on its own. The top-level module pulls it in with
# include("Problem1.jl"), which is what actually defines module Problem1.
# =====================================================================

module Problem1

    # Hand calculateChange out of THIS module. This is only the first of two
    # steps -- Project_Intro_and_Datascience.jl must also export it, or the
    # name will stop here and never reach the REPL or the doc/ chapters.
    export calculateChange

    function calculateChange()

        
        # "nothing" in this context is a placeholder. "nothing" must be
        # replaced with the variable that contains the change you are
        # trying to return.
        return nothing

    end

end # module Problem1
