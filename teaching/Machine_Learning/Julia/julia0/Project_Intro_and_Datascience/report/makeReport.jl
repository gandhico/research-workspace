if !isdefined(Main, :Project_Intro_and_Datascience)
    using Pkg
    Pkg.activate(normpath(joinpath(@__DIR__, "..")))
    using Revise
    using Project_Intro_and_Datascience
end

function MakeResponse(doc::Vector{String}, src::Vector{String})

    lines = []

    # Report
    for i =  eachindex(doc)
        f = open(joinpath(@__DIR__, "..","doc", doc[i]))
        lines = cat(lines,readlines(f); dims=1)
        close(f)
    end 

    # Source Code 
    lines = cat(lines,"## Appendix: Source Code Listings"; dims=1)

    for i =  eachindex(src)
        lines = cat(lines,"##### "*src[i]; dims=1)
        lines = cat(lines,"```julia; eval = false"; dims=1)
        f = open(joinpath(@__DIR__, "..","src", src[i]))
        lines = cat(lines,readlines(f); dims=1)
        close(f)
        lines = cat(lines,"```"; dims=1)

    end 
    return lines
end


#--------------------------------------------------

# PROBLEM RESPONSES
ProblemResponse = [ "Chapter1.jmd",
                    "Chapter2.jmd",
                    "Chapter3.jmd",
                    "Chapter4.jmd",
                    "Chapter5.jmd",
                    "Chapter6.jmd",
                    "Chapter7.jmd",
                    "Chapter8.jmd",
                    "Chapter9.jmd",
                    "Chapter10.jmd",
                    "Chapter11.jmd",
                    "Chapter12.jmd",
                    "Chapter13.jmd",
                    "Problem1Response.jmd", 
                    "Problem2Response.jmd", 
                    "Problem3Response.jmd", 
                    "Problem4Response.jmd"]

#--------------------------------------------------

# PROBLEMs
Problem = [ "Problem1.jl", 
            "Problem4.jl"]

lines = MakeResponse(ProblemResponse, Problem)

#-------------------------------------------------

# WRITE REPORT FILE
fout = open(joinpath(@__DIR__, "..", "report", "ProjectReport.jmd"),"w")
for x in lines
    println(fout, x)
end
close(fout)
weave(joinpath(@__DIR__, "..", "report", "ProjectReport.jmd"), mod=Project_Intro_and_Datascience)