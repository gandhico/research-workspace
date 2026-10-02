"""Build the inline D3 comparison visual from mission output CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    architectures: dict[str, list[dict[str, float]]] = {}
    with (args.results / "mission_timeseries.csv").open(encoding="utf-8", newline="") as stream:
        for row_index, row in enumerate(csv.DictReader(stream)):
            if row_index % 5 != 0:
                continue
            name = row["architecture"]
            architectures.setdefault(name, []).append({
                "time": round(float(row["time_s"]), 3),
                "rollRef": round(float(row["roll_reference_deg"]), 4),
                "pitchRef": round(float(row["pitch_reference_deg"]), 4),
                "yawRef": round(float(row["yaw_reference_deg"]), 4),
                "roll": round(float(row["roll_deg"]), 4),
                "pitch": round(float(row["pitch_deg"]), 4),
                "yaw": round(float(row["yaw_deg"]), 4),
                "residual": round(float(row["allocation_residual_norm_deg_s2"]), 5),
            })

    summary = json.loads((args.results / "mission_monte_carlo_summary.json").read_text(encoding="utf-8"))
    reductions = {item["metric"]: item for item in summary}
    payload = {
        "standard": architectures["thesis_grouped_acs"],
        "allocated": architectures["distributed_elevon_qp"],
        "stats": {
            "allocation": reductions["allocation_rmse_deg_s2"]["mean_reduction_percent"],
            "postFault": reductions["post_fault_rmse_deg"]["mean_reduction_percent"],
            "effort": reductions["surface_rms_command"]["mean_reduction_percent"],
            "trials": reductions["attitude_rmse_deg"]["trials"],
        },
    }

    template = r'''
<div id="ehekatl-mission-comparison">
  <h2>Grouped ACS versus independent elevon allocation</h2>
  <div class="viz-grid ehekatl-stats" aria-label="Paired numerical comparison summary">
    <div class="card viz-stat"><span class="text-muted">Paired mission trials</span><span class="viz-stat-value tabular-nums" data-stat="trials"></span><span class="text-small text-muted">Same plant draw and disturbance per pair</span></div>
    <div class="card viz-stat"><span class="text-muted">Allocation RMSE reduction</span><span class="viz-stat-value tabular-nums" data-stat="allocation"></span><span class="text-small text-muted">After independent redistribution</span></div>
    <div class="card viz-stat"><span class="text-muted">Post-fault attitude RMSE reduction</span><span class="viz-stat-value tabular-nums" data-stat="postFault"></span><span class="text-small text-muted">Left outer elevon jam at 32 s</span></div>
  </div>
  <div class="viz-row ehekatl-legend" aria-label="Visible series">
    <span><span class="ehekatl-swatch ref"></span>Mission reference</span>
    <button type="button" data-series="standard" aria-pressed="true"><span class="ehekatl-swatch standard"></span>Thesis grouped ACS</button>
    <button type="button" data-series="allocated" aria-pressed="true"><span class="ehekatl-swatch allocated"></span>Distributed elevon QP</button>
    <span class="text-small text-muted">Dotted guide: jam declaration</span>
  </div>
  <div class="ehekatl-panels" aria-label="Mission attitude and allocation comparison"></div>
  <div class="tooltip" role="tooltip" hidden></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script>
(() => {
  const root = document.getElementById("ehekatl-mission-comparison");
  const payload = __DATA__;
  const visible = {standard: true, allocated: true};
  root.querySelector('[data-stat="trials"]').textContent = payload.stats.trials;
  root.querySelector('[data-stat="allocation"]').textContent = payload.stats.allocation.toFixed(1) + "%";
  root.querySelector('[data-stat="postFault"]').textContent = payload.stats.postFault.toFixed(1) + "%";
  const panels = [
    {key:"roll", ref:"rollRef", title:"Roll attitude", unit:"deg"},
    {key:"pitch", ref:"pitchRef", title:"Pitch attitude", unit:"deg"},
    {key:"yaw", ref:"yawRef", title:"Yaw attitude", unit:"deg"},
    {key:"residual", title:"Allocation residual norm", unit:"deg/s²"}
  ];
  const host = d3.select(root.querySelector(".ehekatl-panels"));
  panels.forEach((panel, index) => {
    const section = host.append("section").attr("class", "ehekatl-panel");
    section.append("h3").text(panel.title);
    section.append("svg").attr("data-panel", panel.key).attr("role", "img")
      .attr("aria-label", panel.title + " over the 70 second mission")
      .append("title").text(panel.title + " comparison");
  });
  const tooltip = d3.select(root.querySelector(".tooltip"));
  const color = {standard:"var(--viz-series-2)", allocated:"var(--viz-series-1)", reference:"var(--foreground)", fault:"var(--destructive)"};

  function draw() {
    panels.forEach(panel => {
      const svg = d3.select(root.querySelector(`svg[data-panel="${panel.key}"]`));
      svg.selectAll("*:not(title)").remove();
      const width = Math.max(320, svg.node().parentElement.getBoundingClientRect().width);
      const height = panel.key === "residual" ? 245 : 230;
      const margin = {top: 10, right: 20, bottom: 42, left: 66};
      svg.attr("viewBox", `0 0 ${width} ${height}`);
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;
      const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
      const x = d3.scaleLinear().domain([0,70]).range([0,innerW]);
      const values = [];
      ["standard","allocated"].forEach(series => payload[series].forEach(d => values.push(d[panel.key])));
      if (panel.ref) payload.standard.forEach(d => values.push(d[panel.ref]));
      let [lo, hi] = d3.extent(values);
      const pad = Math.max((hi-lo)*0.10, panel.key === "residual" ? 0.08 : 1.0);
      const y = d3.scaleLinear().domain([lo-pad, hi+pad]).nice().range([innerH,0]);
      g.append("rect").attr("data-chart-frame", "").attr("width", innerW).attr("height", innerH).attr("fill", "none").attr("stroke", "var(--border)");
      g.append("g").attr("transform", `translate(0,${innerH})`).call(d3.axisBottom(x).ticks(width < 520 ? 4 : 8));
      g.append("g").call(d3.axisLeft(y).ticks(5));
      g.append("text").attr("class","axis-title").attr("data-axis","x").attr("x",innerW/2).attr("y",innerH+36).attr("text-anchor","middle").text("mission time [s]");
      g.append("text").attr("class","axis-title").attr("data-axis","y").attr("transform","rotate(-90)").attr("x",-innerH/2).attr("y",-50).attr("text-anchor","middle").text(`${panel.title} [${panel.unit}]`);
      const line = key => d3.line().x(d => x(d.time)).y(d => y(d[key]));
      if (panel.ref) g.append("path").datum(payload.standard).attr("class","series reference").attr("d",line(panel.ref)).attr("fill","none").attr("stroke",color.reference).attr("stroke-dasharray","6 4").attr("stroke-width",1.5);
      ["standard","allocated"].forEach(series => {
        g.append("path").datum(payload[series]).attr("class",`series ${series}`).attr("d",line(panel.key)).attr("fill","none").attr("stroke",color[series]).attr("stroke-width",2).style("display",visible[series]?null:"none");
      });
      g.append("line").attr("x1",x(32)).attr("x2",x(32)).attr("y1",0).attr("y2",innerH).attr("stroke",color.fault).attr("stroke-dasharray","3 3").attr("stroke-width",1.5);
      const guide = g.append("line").attr("data-chart-hover-guide","").attr("y1",0).attr("y2",innerH).attr("stroke","var(--muted-foreground)").attr("stroke-width",1).style("display","none");
      const markers = {};
      ["standard","allocated"].forEach(series => markers[series] = g.append("circle").attr("data-chart-hover-marker","").attr("r",4).attr("fill",color[series]).style("display","none"));
      g.append("rect").attr("data-chart-hit","").attr("data-chart-hover-overlay","cross-series").attr("width",innerW).attr("height",innerH).attr("fill","transparent")
        .on("pointermove", event => {
          const [mx] = d3.pointer(event);
          const tx = Math.max(0,Math.min(70,x.invert(mx)));
          guide.attr("x1",x(tx)).attr("x2",x(tx)).style("display",null);
          const rows = [];
          ["standard","allocated"].forEach(series => {
            if (!visible[series]) return;
            const arr=payload[series]; const i=d3.bisector(d=>d.time).center(arr,tx); const d=arr[i];
            markers[series].attr("cx",x(d.time)).attr("cy",y(d[panel.key])).style("display",null);
            rows.push(`${series === "standard" ? "Grouped ACS" : "Elevon QP"}: ${d[panel.key].toFixed(2)} ${panel.unit}`);
          });
          tooltip.html(`<strong>${tx.toFixed(1)} s</strong><br>${rows.join("<br>")}`).style("left",`${event.offsetX+14}px`).style("top",`${event.offsetY+8}px`).attr("hidden",null);
        }).on("pointerleave",()=>{guide.style("display","none");Object.values(markers).forEach(m=>m.style("display","none"));tooltip.attr("hidden",true);});
    });
  }
  root.querySelectorAll("button[data-series]").forEach(button => button.addEventListener("click", () => {
    const series=button.dataset.series; visible[series]=!visible[series]; button.setAttribute("aria-pressed",String(visible[series])); draw();
  }));
  new ResizeObserver(draw).observe(root.querySelector(".ehekatl-panels"));
  draw();
})();
</script>
<style>
#ehekatl-mission-comparison { position: relative; color: var(--foreground); }
#ehekatl-mission-comparison h2 { margin-bottom: 12px; }
#ehekatl-mission-comparison .ehekatl-stats { margin-bottom: 12px; }
#ehekatl-mission-comparison .ehekatl-legend { margin: 6px 0 10px; gap: 14px; }
#ehekatl-mission-comparison .ehekatl-legend button { background: transparent; border: 0; color: var(--foreground); padding: 4px; }
#ehekatl-mission-comparison .ehekatl-legend button[aria-pressed="false"] { opacity: 0.45; }
#ehekatl-mission-comparison .ehekatl-swatch { display:inline-block; width:18px; height:3px; margin-right:6px; vertical-align:middle; background:var(--foreground); }
#ehekatl-mission-comparison .ehekatl-swatch.standard { background:var(--viz-series-2); }
#ehekatl-mission-comparison .ehekatl-swatch.allocated { background:var(--viz-series-1); }
#ehekatl-mission-comparison .ehekatl-swatch.ref { background:var(--foreground); }
#ehekatl-mission-comparison .ehekatl-panels { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px 20px; }
#ehekatl-mission-comparison .ehekatl-panel { min-width:0; }
#ehekatl-mission-comparison .ehekatl-panel h3 { margin:0 0 4px; }
#ehekatl-mission-comparison svg { display:block; width:100%; }
#ehekatl-mission-comparison svg text { fill:var(--foreground); font-size:12px; }
#ehekatl-mission-comparison svg .domain, #ehekatl-mission-comparison svg .tick line { stroke:var(--border); }
#ehekatl-mission-comparison .tooltip { position:absolute; pointer-events:none; background:var(--popover); color:var(--popover-foreground); border:1px solid var(--border); padding:8px; z-index:3; }
@media (max-width:700px) { #ehekatl-mission-comparison .ehekatl-panels { grid-template-columns:1fr; } }
</style>
'''
    rendered = template.replace("__DATA__", json.dumps(payload, separators=(",", ":")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "bytes": args.output.stat().st_size}))


if __name__ == "__main__":
    main()
