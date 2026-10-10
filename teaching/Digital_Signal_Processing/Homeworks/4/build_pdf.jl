# build_pdf.jl -- weave DSP_hk4.jmd to LaTeX and compile it to PDF.
#
#   Canvas wants a PDF, and pandoc is not installed on this machine, so the
#   route is  Weave (md2tex)  ->  pdflatex  (MiKTeX).
#
#   Weave emits bare \includegraphics with no width, so wide figures overflow
#   the text block.  We inject the standard "shrink only if too wide" trick
#   into the preamble before compiling.
#
#   Run from this directory:   julia build_pdf.jl
using Weave

const SRC = "DSP_hk4.jmd"
const OUT = joinpath(@__DIR__, "solutions")

tex = weave(SRC; doctype = "md2tex", out_path = OUT, mod = Main)
println("weaved -> ", tex)

# --- preamble additions: cap figure width, and pin figures in place --------
maxwidth = raw"""
\makeatletter
\def\maxwidth{\ifdim\Gin@nat@width>\linewidth\linewidth\else\Gin@nat@width\fi}
\makeatother
\setkeys{Gin}{width=\maxwidth,keepaspectratio}
\usepackage{float}
"""

s = read(tex, String)
anchor = raw"\usepackage{graphicx}"
if !occursin(raw"\maxwidth", s)
    s = replace(s, anchor => anchor * "\n" * maxwidth; count = 1)
    write(tex, s)
    println("injected maxwidth + float preamble")
end

# Weave emits a bare \begin{figure}, which LaTeX floats to the top or
# bottom of a page.  [H] (from the float package) pins each figure at the point
# in the text where it was written, next to the problem it belongs to.
nfig = length(collect(eachmatch(r"\\begin\{figure\}(?!\[)", s)))
if nfig > 0
    s = replace(s, r"\\begin\{figure\}(?!\[)" => raw"\begin{figure}[H]")
    write(tex, s)
    println("pinned ", nfig, " figures with [H]")
end

# --- compile (twice, so the table of contents / refs settle) --------------
cd(OUT) do
    for pass in 1:2
        run(pipeline(`pdflatex -interaction=nonstopmode $(basename(tex))`,
                     stdout = devnull, stderr = devnull))
        println("pdflatex pass $pass done")
    end
    # tidy the auxiliary files pdflatex leaves behind
    for ext in (".aux", ".log", ".out", ".toc")
        f = replace(basename(tex), ".tex" => ext)
        isfile(f) && rm(f)
    end
end

pdf = replace(tex, ".tex" => ".pdf")
println("PDF -> ", pdf, "  (", filesize(pdf), " bytes)")
