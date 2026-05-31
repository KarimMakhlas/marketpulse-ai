/* Charts — pure SVG sparkline + line/area/bar charts (no dependencies).
   Exported to window for cross-Babel-file access. */

/* -------------------- Sparkline (KPI inline) -------------------- */
const Spark = ({ points, color = "#00E08F", height = 24 }) => {
  // points = [n1, n2, ...] 0..1 floats
  const W = 240, H = height;
  const step = W / (points.length - 1);
  const path = points.map((v, i) => `${i === 0 ? "M" : "L"}${i * step},${H - v * H}`).join(" ");
  const area = `M0,${H} L${path.replace(/^M/, "")} L${W},${H} Z`;
  const id = `spk-${color.replace("#","")}`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.28"/>
          <stop offset="1" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`}/>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5"/>
    </svg>
  );
};

/* -------------------- Chart: area + line -------------------- */
const AreaChart = ({ data, color = "#00E08F", height = 160, yMin = 0, yMax = 1, threshold }) => {
  const W = 600, H = height;
  const padTop = 12, padBot = 22, padL = 38, padR = 12;
  const innerW = W - padL - padR;
  const innerH = H - padTop - padBot;
  const step = innerW / (data.length - 1);
  const norm = (v) => padTop + innerH - ((v - yMin) / (yMax - yMin)) * innerH;
  const path = data.map((v, i) => `${i === 0 ? "M" : "L"}${padL + i * step},${norm(v)}`).join(" ");
  const area = `${path} L${padL + (data.length - 1) * step},${H - padBot} L${padL},${H - padBot} Z`;
  const id = `area-${color.replace("#","")}`;
  const yTicks = [yMin, yMin + (yMax - yMin) / 2, yMax];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height }}>
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.22"/>
          <stop offset="1" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      {/* y-axis ticks */}
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={norm(t)} x2={W - padR} y2={norm(t)} stroke="rgba(255,255,255,0.04)" strokeDasharray="2 4"/>
          <text x={padL - 6} y={norm(t) + 3} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">{t.toFixed(2)}</text>
        </g>
      ))}
      {/* threshold line */}
      {threshold !== undefined && (
        <line x1={padL} y1={norm(threshold)} x2={W - padR} y2={norm(threshold)} stroke="#FFB020" strokeDasharray="4 4" strokeWidth="1"/>
      )}
      <path d={area} fill={`url(#${id})`}/>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5"/>
      {/* last point dot */}
      <circle cx={padL + (data.length - 1) * step} cy={norm(data[data.length - 1])} r="3" fill={color}/>
      {/* x-axis labels (sparse) */}
      <text x={padL} y={H - 6} fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">−24h</text>
      <text x={W - padR} y={H - 6} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">now</text>
    </svg>
  );
};

const MultiLineChart = ({ series, height = 160, yMin = 0, yMax = 1 }) => {
  // series = [{ label, color, data: [...] }]
  const W = 600, H = height;
  const padTop = 12, padBot = 22, padL = 38, padR = 12;
  const innerW = W - padL - padR;
  const innerH = H - padTop - padBot;
  const len = series[0].data.length;
  const step = innerW / (len - 1);
  const norm = (v) => padTop + innerH - ((v - yMin) / (yMax - yMin)) * innerH;
  const yTicks = [yMin, yMin + (yMax - yMin) / 2, yMax];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height }}>
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={norm(t)} x2={W - padR} y2={norm(t)} stroke="rgba(255,255,255,0.04)" strokeDasharray="2 4"/>
          <text x={padL - 6} y={norm(t) + 3} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">{t.toFixed(2)}</text>
        </g>
      ))}
      {series.map((s, idx) => {
        const path = s.data.map((v, i) => `${i === 0 ? "M" : "L"}${padL + i * step},${norm(v)}`).join(" ");
        return <path key={idx} d={path} fill="none" stroke={s.color} strokeWidth="1.5"/>;
      })}
      <text x={padL} y={H - 6} fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">−24h</text>
      <text x={W - padR} y={H - 6} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">now</text>
    </svg>
  );
};

const BarChart = ({ data, color = "#FFB020", height = 160, yMax }) => {
  const W = 600, H = height;
  const padTop = 12, padBot = 22, padL = 38, padR = 12;
  const innerW = W - padL - padR;
  const innerH = H - padTop - padBot;
  const max = yMax || Math.max(...data) * 1.2;
  const barW = innerW / data.length - 2;
  const yTicks = [0, max / 2, max];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height }}>
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={padTop + innerH - (t / max) * innerH} x2={W - padR} y2={padTop + innerH - (t / max) * innerH} stroke="rgba(255,255,255,0.04)" strokeDasharray="2 4"/>
          <text x={padL - 6} y={padTop + innerH - (t / max) * innerH + 3} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">{t.toFixed(1)}%</text>
        </g>
      ))}
      {data.map((v, i) => {
        const h = (v / max) * innerH;
        return <rect key={i} x={padL + i * (innerW / data.length) + 1} y={padTop + innerH - h} width={barW} height={h} fill={color} rx="1"/>;
      })}
      <text x={padL} y={H - 6} fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">−24h</text>
      <text x={W - padR} y={H - 6} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">now</text>
    </svg>
  );
};

Object.assign(window, { Spark, AreaChart, MultiLineChart, BarChart });
