# build_pdf.jl -- compile the proposal from its LaTeX master source.
#
#   DSP_project_proposal.tex is the MASTER.  Edit that file directly.
#   This script only runs pdflatex; it never regenerates the .tex, so your
#   edits are safe.
#
#   Run from this directory:   julia build_pdf.jl
#
#   (The old Weave pipeline is kept as build_pdf_from_jmd.jl.legacy.  Do not
#    run it unless you intend to regenerate the .tex from the .jmd, which
#    would overwrite any hand edits.)

const TEX = "DSP_project_proposal.tex"
const PDF = replace(TEX, ".tex" => ".pdf")

isfile(TEX) || error("$TEX not found; run this from the project directory.")
isfile(joinpath("figures", "architecture.png")) ||
    @warn "figures/architecture.png is missing; the figure will render as a placeholder."

for pass in 1:2
    run(pipeline(`pdflatex -interaction=nonstopmode $TEX`,
                 stdout = devnull, stderr = devnull))
    println("pdflatex pass $pass done")
end

# report any real LaTeX errors before tidying the log away
logfile = replace(TEX, ".tex" => ".log")
if isfile(logfile)
    errs = filter(l -> startswith(l, "! "), readlines(logfile))
    isempty(errs) ? println("no LaTeX errors") :
                    (println("LaTeX ERRORS:"); foreach(e -> println("  ", e), errs))
end

for ext in (".aux", ".log", ".out", ".toc")
    f = replace(TEX, ".tex" => ext)
    isfile(f) && rm(f)
end

println("PDF -> ", abspath(PDF), "  (", filesize(PDF), " bytes)")
