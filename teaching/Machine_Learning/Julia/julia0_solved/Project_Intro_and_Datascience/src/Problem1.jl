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

# =====================================================================
# Problem 1: Coinage
# Description: In the (tiny) kingdom of Larion, they use an ancient
# and revered system of coinage consisting of Pennings, Roobles, and
# Krowns. Write a function that helps clerks at cash registers compute
# how much change they need to give their customers.
# 19 Pennings make = 1 Rooble
# 13 Roobles make = 1 Krown
# The input to the function will be a 2x3 matrix where The first row
# given will be the price the customer needs to pay. The second row
# wil be what the customer paid with (They might pay with any mix of
# coins). The first column in the matrix is the integer krown value and
# the last row containing the integer Pennies value.
# Print out the exact change they should receive, and return a cor-
# responding 1x3 integer vector. Give back as few coins as possible.
# (Giving 1 Krown and 2 Roobles is correct rather than 15 Roobles)
# Example 1:
# Input: [2 12 11; 3 0 0]
# Output: [0 0 8]
# 0 Krown
# 0 Rooble
# 8 Pennnings
# Example 2:
# Input: [13 4 2; 12 41 2]
# Output: [1 11 0]
# 1 Krown
# 11 Rooble
# 0 Pennnings

# =====================================================================

# 1. Part A: Write the Given function (and only the function) in src/Problem1.jl
# 2. Part B: Display the results of the function using the input from the
# two examples in the prompt in doc/Problem1Response.jmd.


# =====================================================================


module Problem1

    # Hand calculateChange out of THIS module. This is only the first of two
    # steps -- Project_Intro_and_Datascience.jl must also export it, or the
    # name will stop here and never reach the REPL or the doc/ chapters.
    export calculateChange

    function calculateChange(transaction::Matrix{<:Integer})
        size(transaction) == (2, 3) || throw(ArgumentError("Input must be a 2x3 matrix."))

        coin_values = [13 * 19, 19, 1]
        price = sum(transaction[1, :] .* coin_values)
        paid = sum(transaction[2, :] .* coin_values)
        paid >= price || throw(ArgumentError("The amount paid is less than the price."))

        remaining = paid - price
        krowns, remaining = divrem(remaining, coin_values[1])
        roobles, pennings = divrem(remaining, coin_values[2])
        change = [krowns, roobles, pennings]

        println(change)
        println(krowns, " Krown", krowns == 1 ? "" : "s")
        println(roobles, " Rooble", roobles == 1 ? "" : "s")
        println(pennings, " Penning", pennings == 1 ? "" : "s")
        return change

    end

end # module Problem1
