"use strict";

const fs = require("fs");
const path = require("path");
const sharp = require("sharp");
const { mathjax } = require("mathjax-full/js/mathjax.js");
const { TeX } = require("mathjax-full/js/input/tex.js");
const { SVG } = require("mathjax-full/js/output/svg.js");
const { liteAdaptor } = require("mathjax-full/js/adaptors/liteAdaptor.js");
const { RegisterHTMLHandler } = require("mathjax-full/js/handlers/html.js");
const { AllPackages } = require("mathjax-full/js/input/tex/AllPackages.js");

const equations = [
  String.raw`u_{y,k} \rightarrow u_{t,k} \rightarrow \delta_{a,k} \rightarrow P_k`,
  String.raw`x_k = [\Delta P_k,\;\Delta u_{t,k},\;\Delta u_{y,k-1}]^T`,
  String.raw`x_{k+1}=Ax_k+Bu_k`,
  String.raw`A=\begin{bmatrix}0.40856&3.55738&37.94551\\0&0.05609&0.59835\\0&0&0\end{bmatrix},\quad B=\begin{bmatrix}23.90120\\0.37689\\1\end{bmatrix}`,
  String.raw`J=\sum_{k=0}^{\infty}(x_k^TQx_k+u_k^TRu_k)`,
  String.raw`K=[0.0002944,\;0.0027424,\;0.0292528]`,
  String.raw`\min_g\;\lVert y_f\rVert_{Q_y}^2+\lVert u_f\rVert_{R_u}^2+\lVert\Delta u_f\rVert_{R_{\Delta u}}^2+\lambda_g\lVert g\rVert_2^2`,
];

const outputDir = path.join(__dirname, "equations");
fs.mkdirSync(outputDir, { recursive: true });
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({ packages: AllPackages });
const svgOutput = new SVG({ fontCache: "local" });
const document = mathjax.document("", { InputJax: tex, OutputJax: svgOutput });

function toSvg(latex) {
  const html = adaptor.outerHTML(document.convert(latex, { display: true }));
  const start = html.indexOf("<svg");
  const end = html.indexOf("</svg>");
  let svg = html.slice(start, end + 6);
  if (!/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/.test(svg)) {
    svg = svg.replace(/<svg /, '<svg xmlns="http://www.w3.org/2000/svg" ');
  }
  svg = svg.replace(/(width|height)="([0-9.]+)(ex|em)"/g, (_m, attr, number) => {
    return `${attr}="${Math.round(parseFloat(number) * 9)}px"`;
  });
  return svg.replace(/currentColor/g, "#000000");
}

Promise.all(equations.map(async (equation, index) => {
  const svg = Buffer.from(toSvg(equation));
  await sharp(svg, { density: 320 })
    .png()
    .toFile(path.join(outputDir, `equation_${index + 1}.png`));
})).catch((error) => {
  console.error(error);
  process.exit(1);
});
