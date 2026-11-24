export function renderFrame(containerId, frame, isDark) {
  const bg = isDark ? "#1b2230" : "#ffffff";
  const fg = isDark ? "#e8edf5" : "#1e2633";
  const grid = isDark ? "#2d3748" : "#e2e8f0";

  const layout = {
    paper_bgcolor: bg,
    plot_bgcolor: bg,
    font: { color: fg, size: 12 },
    margin: { l: 55, r: 25, t: 45, b: 45 },
    ...frame.layout,
  };

  for (const key of Object.keys(layout)) {
    if (key.startsWith("xaxis") || key.startsWith("yaxis")) {
      layout[key] = { gridcolor: grid, zerolinecolor: grid, ...layout[key] };
    }
  }

  Plotly.react(containerId, frame.traces, layout, { responsive: true, displayModeBar: true });
}
