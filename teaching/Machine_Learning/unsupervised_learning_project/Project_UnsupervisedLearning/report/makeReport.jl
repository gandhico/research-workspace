if !isdefined(Main, :Project_UnsupervisedLearning)
    using Pkg 
    root_dir = normpath(joinpath(@__DIR__, ".."))
    Pkg.activate(root_dir)
    include(normpath(root_dir, "src", "Project_UnsupervisedLearning.jl"))
    using .Project_UnsupervisedLearning
end

function MakeResponse(doc::Vector{String}, src::Vector{String})

    lines = []

    # Report
    for i =  eachindex(doc)
        f = open(normpath(@__DIR__, "..","doc", doc[i]))
        lines = cat(lines,readlines(f); dims=1)
        close(f)
    end 

    # Source Code 
    lines = cat(lines,"## Appendix: Source Code Listings"; dims=1)

    for i =  eachindex(src)
        lines = cat(lines,"##### "*src[i]; dims=1)
        lines = cat(lines,"```julia; eval = false"; dims=1)
        f = open(normpath(@__DIR__, "..","src", src[i]))
        lines = cat(lines,readlines(f); dims=1)
        close(f)
        lines = cat(lines,"```"; dims=1)

    end 
    return lines
end


#--------------------------------------------------

# PROBLEM RESPONSES
ProblemResponse = [ "Problem1Response.jmd", 
                    "Problem2Response.jmd", 
                    "Problem3Response.jmd", 
                    "Problem4Response.jmd", 
                    "Problem5Response.jmd", 
                    "Problem6Response.jmd"]

#--------------------------------------------------

# PROBLEMs
Problem = [ "Problem1.jl", 
            "Problem2.jl", 
            "Problem3.jl", 
            "Problem4.jl", 
            "Problem5.jl"]

lines = MakeResponse(ProblemResponse, Problem)

#-------------------------------------------------

# WRITE REPORT FILE
fout = open(normpath(@__DIR__, "..", "report", "ProjectReport.jmd"),"w")
for x in lines
    println(fout, x)
end
close(fout)
report_path = normpath(@__DIR__, "..", "report", "ProjectReport.jmd")
weave(report_path, mod=Project_UnsupervisedLearning)

# Keep long source lines printable instead of clipping them behind a horizontal
# scrollbar in the HTML-to-PDF workflow.
html_path = splitext(report_path)[1] * ".html"
print_css = """
<style>
@media print {
  pre { white-space: pre-wrap !important; overflow-wrap: anywhere; word-break: break-word; overflow-x: visible !important; }
}
</style>
"""
html = read(html_path, String)
html = replace(html, "</HEAD>" => print_css * "\n</HEAD>"; count=1)
write(html_path, html)
