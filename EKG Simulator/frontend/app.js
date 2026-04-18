const controls = {
  magnitude: document.getElementById("magnitude-range"),
  stGain: document.getElementById("st-gain-range"),
};

const pads = {
  frontal: document.getElementById("frontal-pad"),
  horizontal: document.getElementById("horizontal-pad"),
};

const handles = {
  frontal: document.getElementById("frontal-handle"),
  horizontal: document.getElementById("horizontal-handle"),
};

const labels = {
  frontalAngle: document.getElementById("frontal-angle-value"),
  horizontalAngle: document.getElementById("horizontal-angle-value"),
  frontalVector: document.getElementById("frontal-vector-value"),
  horizontalVector: document.getElementById("horizontal-vector-value"),
  magnitude: document.getElementById("magnitude-value"),
  stGain: document.getElementById("st-gain-value"),
  vectorMagnitude: document.getElementById("vector-magnitude"),
  cartesianVector: document.getElementById("cartesian-vector"),
  topLead: document.getElementById("top-lead"),
  topSegment: document.getElementById("top-segment"),
  status: document.getElementById("server-status"),
  hiddenSpaceStatus: document.getElementById("hidden-space-status"),
};

const modelControls = {
  list: document.getElementById("omi-model-list"),
};

const presets = {
  anterior: { frontalAngle: 18, horizontalAngle: 78, magnitude: 1.05, stGain: 0.28 },
  inferior: { frontalAngle: -72, horizontalAngle: 166, magnitude: 1.03, stGain: 0.32 },
  lateral: { frontalAngle: -6, horizontalAngle: 180, magnitude: 1.02, stGain: 0.22 },
  neutral: { frontalAngle: 0, horizontalAngle: 0, magnitude: 0.0, stGain: 0.0 },
};

const omiModels = [
  {
    id: "de-winter",
    name: "de Winter",
    context: "OMI anterior por LAD proximal/media",
    description: "Padrão antero-septal com T hiperagudas e J-point deprimido ascendente em V2-V4.",
    vector: [0.25, 0.95, 0.20],
    stGain: 0.14,
  },
  {
    id: "wellens",
    name: "Wellens residual",
    context: "Reperfusão/lesão crítica de LAD",
    description: "Vetor residual pequeno, mais útil com pouco ST e maior ênfase em repolarização anterior.",
    vector: [0.10, 0.35, 0.05],
    stGain: 0.06,
  },
  {
    id: "posterior",
    name: "OMI posterior",
    context: "LCx ou RCA dominante, parede posterior",
    description: "Direção posterior e lateral esquerda, favorecendo imagem-espelho em V1-V3.",
    vector: [-0.45, -0.90, 0.00],
    stGain: 0.18,
  },
  {
    id: "aslanger",
    name: "Aslanger",
    context: "OMI inferior mascarado por isquemia difusa",
    description: "Direção infero-direita, focal, compatível com destaque em DIII e V1.",
    vector: [0.55, 0.20, -0.80],
    stGain: 0.16,
  },
  {
    id: "northern-omi",
    name: "Northern OMI",
    context: "Padrão superior esquerdo de alto risco",
    description: "Direção superior e esquerda com pouca anterioridade, experimental no simulador.",
    vector: [-0.70, -0.20, 0.85],
    stGain: 0.16,
  },
  {
    id: "precordial-swirl",
    name: "Precordial swirl",
    context: "LAD proximal, padrão septal-anterior",
    description: "Direção antero-direita superior, mais voltada a V1-V2 do que a V4-V6.",
    vector: [0.55, 0.85, 0.35],
    stGain: 0.15,
  },
  {
    id: "anterior-sutil",
    name: "OMI anterior sutil",
    context: "Oclusão anterior precoce com T hiperaguda",
    description: "Vetor anterior de menor amplitude, mais discreto do que de Winter.",
    vector: [0.10, 0.75, 0.05],
    stGain: 0.10,
  },
  {
    id: "inferolateral-sutil",
    name: "OMI inferolateral sutil",
    context: "LCx ou marginal obtusa",
    description: "Componente lateral esquerdo com discreta inclinação inferior.",
    vector: [-0.80, 0.05, -0.40],
    stGain: 0.12,
  },
  {
    id: "inferior-rca-like",
    name: "OMI inferior RCA-like",
    context: "RCA com padrão inferior sutil",
    description: "Direção inferior com leve componente direito/anterior, útil para variantes de Aslanger.",
    vector: [0.35, 0.10, -0.95],
    stGain: 0.14,
  },
];

const state = {
  meta: null,
  frontalAngle: -35,
  horizontalAngle: 70,
  activeModelId: "",
  hiddenSpaceMesh: null,
};

const standardCoverageGroups = [
  ["II", "III", "aVF"],
  ["I", "aVL"],
  ["V5", "V6"],
  ["V1", "V2"],
  ["V2", "V3", "V4"],
];

const plotTheme = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: {
    family: "IBM Plex Sans, sans-serif",
    color: "#11262d",
  },
};

const BULLSEYE_ROTATION_OFFSET = 0;

function formatNumber(value) {
  return Number(value).toFixed(2);
}

function degreesToRadians(value) {
  return (value * Math.PI) / 180;
}

function normalizeAngle(value) {
  let normalized = value;
  while (normalized > 180) normalized -= 360;
  while (normalized <= -180) normalized += 360;
  return normalized;
}

function computeVectorFromAngles() {
  const magnitude = Number(controls.magnitude.value);
  const frontalRad = degreesToRadians(state.frontalAngle);
  const horizontalRad = degreesToRadians(state.horizontalAngle);
  const xComponent = Math.cos(frontalRad) * Math.cos(horizontalRad);
  const yComponent = Math.cos(frontalRad) * Math.sin(horizontalRad);
  const zComponent = Math.sin(frontalRad);

  if (magnitude <= 1e-12) {
    return { x: 0, y: 0, z: 0, magnitude };
  }

  return {
    x: xComponent * magnitude,
    y: yComponent * magnitude,
    z: zComponent * magnitude,
    magnitude,
  };
}

function cartesianToControlState(vector) {
  const [x, y, z] = vector;
  const magnitude = Math.sqrt(x ** 2 + y ** 2 + z ** 2);
  if (magnitude <= 1e-12) {
    return { frontalAngle: 0, horizontalAngle: 0, magnitude: 0 };
  }

  const horizontalAngle = normalizeAngle((Math.atan2(y, x) * 180) / Math.PI);
  const frontalAngle = normalizeAngle((Math.atan2(z, Math.sqrt(x ** 2 + y ** 2)) * 180) / Math.PI);
  return { frontalAngle, horizontalAngle, magnitude };
}

function getPayload() {
  const vector = computeVectorFromAngles();
  return {
    x: Number(vector.x.toFixed(6)),
    y: Number(vector.y.toFixed(6)),
    z: Number(vector.z.toFixed(6)),
    st_gain: Number(controls.stGain.value),
  };
}

function setHandlePosition(handle, angleDeg) {
  const radiusPercent = 38;
  const angleRad = degreesToRadians(angleDeg);
  const xPercent = 50 + radiusPercent * Math.cos(angleRad);
  const yPercent = 50 - radiusPercent * Math.sin(angleRad);
  handle.style.left = `${xPercent}%`;
  handle.style.top = `${yPercent}%`;
}

function updateControlLabels() {
  const vector = computeVectorFromAngles();
  labels.frontalAngle.textContent = `${Math.round(state.frontalAngle)}°`;
  labels.horizontalAngle.textContent = `${Math.round(state.horizontalAngle)}°`;
  labels.frontalVector.textContent = `[${formatNumber(vector.x)}, ${formatNumber(vector.z)}]`;
  labels.horizontalVector.textContent = `[${formatNumber(vector.x)}, ${formatNumber(vector.y)}]`;
  labels.magnitude.textContent = formatNumber(controls.magnitude.value);
  labels.stGain.textContent = formatNumber(controls.stGain.value);
  setHandlePosition(handles.frontal, state.frontalAngle);
  setHandlePosition(handles.horizontal, state.horizontalAngle);
}

function renderModelButtons() {
  modelControls.list.innerHTML = omiModels
    .map(
      (model) => `
        <button
          type="button"
          class="model-button${state.activeModelId === model.id ? " is-active" : ""}"
          data-model-id="${model.id}"
        >
          ${model.name}
        </button>
      `,
    )
    .join("");
}

function computeMagnitude(vector) {
  return Math.sqrt(vector.reduce((sum, item) => sum + item ** 2, 0));
}

function makeSphereTrace() {
  const phi = [];
  const theta = [];
  for (let index = 0; index < 28; index += 1) {
    phi.push((Math.PI * index) / 27);
    theta.push((2 * Math.PI * index) / 27);
  }

  const x = [];
  const y = [];
  const z = [];

  theta.forEach((thetaValue) => {
    const rowX = [];
    const rowY = [];
    const rowZ = [];
    phi.forEach((phiValue) => {
      rowX.push(Math.sin(phiValue) * Math.cos(thetaValue));
      rowY.push(Math.sin(phiValue) * Math.sin(thetaValue));
      rowZ.push(Math.cos(phiValue));
    });
    x.push(rowX);
    y.push(rowY);
    z.push(rowZ);
  });

  return {
    type: "surface",
    x,
    y,
    z,
    opacity: 0.08,
    showscale: false,
    colorscale: [
      [0, "#f5dcc9"],
      [1, "#f5dcc9"],
    ],
    hoverinfo: "skip",
  };
}

function bullseyeZ(radius) {
  const zBasal = 0.25;
  const zMid = -0.25;
  const zApical = -0.9;
  const slope1 = (zMid - zApical) / 0.4;
  const slope2 = (zBasal - zMid) / 0.3;
  if (radius < 0.4) return zApical + slope1 * radius;
  if (radius < 0.7) return zMid + slope2 * (radius - 0.4);
  return zBasal + slope2 * (radius - 0.7);
}

function bullseyePolarPoint(radius, angleDeg) {
  const angle = degreesToRadians(angleDeg) + BULLSEYE_ROTATION_OFFSET;
  return {
    x: radius * Math.cos(angle),
    y: radius * Math.sin(angle),
    z: bullseyeZ(radius),
  };
}

function buildBullseyeMesh() {
  const segmentColors = [
    "#8FAADC", "#F6BD60", "#F28482", "#84A59D", "#90BE6D", "#F7EDE2",
    "#CDB4DB", "#FFC8DD", "#B5838D", "#A0C4FF", "#BDB2FF", "#FFD6A5",
    "#CAFFBF", "#FFADAD", "#D0F4DE", "#FDFFB6", "#9BF6FF",
  ];
  const anglesBasal = [0, 60, 120, 180, 240, 300];
  const anglesMid = [0, 60, 120, 180, 240, 300];
  const anglesApical = [45, 135, 225, 315];
  const segments = [];
  let colorIndex = 0;

  function addRing(innerRadius, outerRadius, angles) {
    for (let index = 0; index < angles.length; index += 1) {
      const startDeg = angles[index];
      const endDeg = angles[(index + 1) % angles.length];
      const angleEnd = endDeg <= startDeg ? endDeg + 360 : endDeg;
      const rows = [];

      for (let angleStep = 0; angleStep <= 28; angleStep += 1) {
        const angleDeg = startDeg + ((angleEnd - startDeg) * angleStep) / 28;
        const row = [];
        for (let radiusStep = 0; radiusStep <= 12; radiusStep += 1) {
          const radius = innerRadius + ((outerRadius - innerRadius) * radiusStep) / 12;
          row.push(bullseyePolarPoint(radius, angleDeg));
        }
        rows.push(row);
      }

      segments.push({
        rows,
        color: segmentColors[colorIndex],
      });
      colorIndex += 1;
    }
  }

  addRing(0.70, 1.00, anglesBasal);
  addRing(0.40, 0.70, anglesMid);
  addRing(0.18, 0.40, anglesApical);

  const apexRows = [];
  for (let angleStep = 0; angleStep <= 28; angleStep += 1) {
    const angleDeg = (360 * angleStep) / 28;
    const row = [];
    for (let radiusStep = 0; radiusStep <= 12; radiusStep += 1) {
      const radius = (0.18 * radiusStep) / 12;
      row.push(bullseyePolarPoint(radius, angleDeg));
    }
    apexRows.push(row);
  }
  segments.push({
    rows: apexRows,
    color: segmentColors[16],
  });

  return {
    segments,
    radialLines: [
      ...anglesBasal.map((angle) => ({ startRadius: 0.70, endRadius: 1.00, angleDeg: angle })),
      ...anglesMid.map((angle) => ({ startRadius: 0.40, endRadius: 0.70, angleDeg: angle })),
      ...anglesApical.map((angle) => ({ startRadius: 0.18, endRadius: 0.40, angleDeg: angle })),
    ],
  };
}

function buildBullseye3DTraces() {
  const geometry = buildBullseyeMesh();
  const traces = [];

  geometry.segments.forEach((segment) => {
    const x = segment.rows.map((row) => row.map((point) => point.x));
    const y = segment.rows.map((row) => row.map((point) => point.y));
    const z = segment.rows.map((row) => row.map((point) => point.z));
    const surfacecolor = segment.rows.map((row) => row.map(() => 1));

    traces.push({
      type: "surface",
      x,
      y,
      z,
      surfacecolor,
      colorscale: [[0, segment.color], [1, segment.color]],
      opacity: 0.72,
      showscale: false,
      showlegend: false,
      hoverinfo: "skip",
      contours: {
        x: { show: false },
        y: { show: false },
        z: { show: false },
      },
    });
  });

  const thetaLine = Array.from({ length: 241 }, (_, index) => (2 * Math.PI * index) / 240);
  [[0.18, 5], [0.4, 5], [0.7, 5], [1.0, 6]].forEach(([radius, width]) => {
    traces.push({
      type: "scatter3d",
      mode: "lines",
      x: thetaLine.map((theta) => radius * Math.cos(theta + BULLSEYE_ROTATION_OFFSET)),
      y: thetaLine.map((theta) => radius * Math.sin(theta + BULLSEYE_ROTATION_OFFSET)),
      z: thetaLine.map(() => bullseyeZ(radius)),
      line: { color: "black", width },
      hoverinfo: "skip",
      showlegend: false,
    });
  });

  geometry.radialLines.forEach(({ startRadius, endRadius, angleDeg }) => {
    const angle = degreesToRadians(angleDeg) + BULLSEYE_ROTATION_OFFSET;
    traces.push({
      type: "scatter3d",
      mode: "lines",
      x: [startRadius * Math.cos(angle), endRadius * Math.cos(angle)],
      y: [startRadius * Math.sin(angle), endRadius * Math.sin(angle)],
      z: [bullseyeZ(startRadius), bullseyeZ(endRadius)],
      line: { color: "black", width: 3 },
      hoverinfo: "skip",
      showlegend: false,
    });
  });

  return traces;
}

function buildLeadTraces() {
  const allLeads = Object.entries(state.meta.lead_vectors);
  const limbLeads = allLeads.filter(([name]) => !name.startsWith("V"));
  const chestLeads = allLeads.filter(([name]) => name.startsWith("V"));

  const toTrace = (entries, color, name) => ({
    type: "scatter3d",
    mode: "markers+text",
    x: entries.map(([, vector]) => vector[0]),
    y: entries.map(([, vector]) => vector[1]),
    z: entries.map(([, vector]) => vector[2]),
    text: entries.map(([lead]) => lead),
    textposition: "top center",
    marker: {
      size: 5,
      color,
      line: { width: 1, color: "rgba(255,255,255,0.7)" },
    },
    name,
    hovertemplate: "%{text}<extra></extra>",
  });

  return [
    toTrace(limbLeads, "#c84c36", "Limb leads"),
    toTrace(chestLeads, "#0d6b73", "Precordial leads"),
  ];
}

function dot(vectorA, vectorB) {
  return vectorA[0] * vectorB[0] + vectorA[1] * vectorB[1] + vectorA[2] * vectorB[2];
}

function projectVectorToLeads(vector) {
  return Object.fromEntries(
    Object.entries(state.meta.lead_vectors).map(([lead, axis]) => [lead, dot(vector, axis)]),
  );
}

function isCoveredByGroups(vector, groups, threshold = 0.25) {
  const projection = projectVectorToLeads(vector);
  return groups.some((group) => group.filter((lead) => projection[lead] > threshold).length >= 2);
}

function generateHiddenSpaceMesh(resolution = 16, maxRadius = 1.0, threshold = 0.25) {
  const xs = [];
  const ys = [];
  const zs = [];

  for (let ix = 0; ix < resolution; ix += 1) {
    const x = -maxRadius + (2 * maxRadius * ix) / (resolution - 1);
    for (let iy = 0; iy < resolution; iy += 1) {
      const y = -maxRadius + (2 * maxRadius * iy) / (resolution - 1);
      for (let iz = 0; iz < resolution; iz += 1) {
        const z = -maxRadius + (2 * maxRadius * iz) / (resolution - 1);
        const vector = [x, y, z];
        const radius = Math.sqrt(x ** 2 + y ** 2 + z ** 2);
        if (radius <= 1e-8 || radius > maxRadius) {
          continue;
        }

        const detectedByStandard = isCoveredByGroups(vector, standardCoverageGroups, threshold);
        if (!detectedByStandard) {
          xs.push(x);
          ys.push(y);
          zs.push(z);
        }
      }
    }
  }

  return { x: xs, y: ys, z: zs };
}

function isVectorHidden(vector, threshold = 0.25) {
  const detectedByStandard = isCoveredByGroups(vector, standardCoverageGroups, threshold);
  return !detectedByStandard;
}

function renderVectorPlot(simulation) {
  const inputVector = simulation.input_vector;
  const data = [
    ...buildBullseye3DTraces(inputVector),
    ...buildLeadTraces(),
    {
      type: "scatter3d",
      mode: "lines+markers",
      x: [0, inputVector[0]],
      y: [0, inputVector[1]],
      z: [0, inputVector[2]],
      line: { width: 10, color: "#0f2e36" },
      marker: { size: 5, color: "#0f2e36" },
      name: "Injury vector",
      hovertemplate: "x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}<extra></extra>",
    },
  ];

  Plotly.react(
    "vector-plot",
    data,
    {
      ...plotTheme,
      margin: { l: 0, r: 0, t: 0, b: 0 },
      scene: {
        xaxis: { title: "X", range: [-1.2, 1.2], backgroundcolor: "rgba(255,255,255,0)" },
        yaxis: { title: "Y", range: [-1.2, 1.2], backgroundcolor: "rgba(255,255,255,0)" },
        zaxis: { title: "Z", range: [-1.2, 1.2], backgroundcolor: "rgba(255,255,255,0)" },
        aspectmode: "cube",
        camera: { eye: { x: 1.55, y: 1.45, z: 1.05 } },
      },
      showlegend: true,
      legend: {
        orientation: "h",
        y: 1.02,
        x: 0,
        bgcolor: "rgba(255,255,255,0.55)",
      },
    },
    { displayModeBar: false, responsive: true },
  );
}

function renderHiddenSpacePlot(simulation) {
  if (!state.hiddenSpaceMesh) {
    state.hiddenSpaceMesh = generateHiddenSpaceMesh();
  }

  const inputVector = simulation.input_vector;
  const hidden = isVectorHidden(inputVector);
  labels.hiddenSpaceStatus.textContent = hidden ? "Oculto no ECG padrão" : "Visível no ECG padrão";

  Plotly.react(
    "hidden-space-plot",
    [
      {
        type: "scatter3d",
        mode: "markers",
        x: state.hiddenSpaceMesh.x,
        y: state.hiddenSpaceMesh.y,
        z: state.hiddenSpaceMesh.z,
        marker: {
          size: 3,
          color: "rgba(200,76,54,0.42)",
        },
        name: "Zona cega",
        hoverinfo: "skip",
      },
      {
        type: "scatter3d",
        mode: "lines+markers",
        x: [0, inputVector[0]],
        y: [0, inputVector[1]],
        z: [0, inputVector[2]],
        line: { width: 10, color: hidden ? "#c84c36" : "#0d6b73" },
        marker: { size: 5, color: hidden ? "#c84c36" : "#0d6b73" },
        name: hidden ? "Vetor oculto" : "Vetor captado",
        hovertemplate: "x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}<extra></extra>",
      },
    ],
    {
      ...plotTheme,
      margin: { l: 0, r: 0, t: 0, b: 0 },
      scene: {
        xaxis: { title: "X", range: [-1.1, 1.1], backgroundcolor: "rgba(255,255,255,0)" },
        yaxis: { title: "Y", range: [-1.1, 1.1], backgroundcolor: "rgba(255,255,255,0)" },
        zaxis: { title: "Z", range: [-1.1, 1.1], backgroundcolor: "rgba(255,255,255,0)" },
        aspectmode: "cube",
        camera: { eye: { x: 1.48, y: 1.48, z: 1.18 } },
      },
      showlegend: true,
      legend: {
        orientation: "h",
        y: 1.02,
        x: 0,
        bgcolor: "rgba(255,255,255,0.55)",
      },
    },
    { displayModeBar: false, responsive: true },
  );
}

function renderDamagePlot(simulation) {
  const segments = simulation.damage_segments;
  const ringDefinitions = [
    { ids: [1, 2, 3, 4, 5, 6], inner: 0.68, outer: 1.0, start: -120, step: 60 },
    { ids: [7, 8, 9, 10, 11, 12], inner: 0.38, outer: 0.68, start: -120, step: 60 },
    { ids: [13, 14, 15, 16], inner: 0.16, outer: 0.38, start: -135, step: 90 },
  ];
  const segmentMap = new Map(segments.map((segment) => [segment.id, segment]));
  const shapes = [];
  const hoverPoints = [];
  const annotations = [];

  function polarToCartesian(radius, angleDeg) {
    const angleRad = degreesToRadians(angleDeg);
    return { x: radius * Math.cos(angleRad), y: radius * Math.sin(angleRad) };
  }

  function buildSectorPath(innerRadius, outerRadius, startDeg, endDeg) {
    const resolution = 28;
    const outerPoints = [];
    const innerPoints = [];
    for (let index = 0; index <= resolution; index += 1) {
      const angle = startDeg + ((endDeg - startDeg) * index) / resolution;
      outerPoints.push(polarToCartesian(outerRadius, angle));
    }
    for (let index = resolution; index >= 0; index -= 1) {
      const angle = startDeg + ((endDeg - startDeg) * index) / resolution;
      innerPoints.push(polarToCartesian(innerRadius, angle));
    }
    const allPoints = [...outerPoints, ...innerPoints];
    return `M ${allPoints.map((point) => `${point.x.toFixed(4)},${point.y.toFixed(4)}`).join(" L ")} Z`;
  }

  function segmentColor(score) {
    if (score >= 0.8) return "#8f1d14";
    if (score >= 0.6) return "#c84c36";
    if (score >= 0.4) return "#e58f64";
    if (score >= 0.2) return "#efc095";
    return "#f3e6d8";
  }

  ringDefinitions.forEach((ring) => {
    ring.ids.forEach((id, index) => {
      const segment = segmentMap.get(id);
      const startDeg = ring.start + index * ring.step;
      const endDeg = startDeg + ring.step;
      const middleDeg = (startDeg + endDeg) / 2;
      const centroid = polarToCartesian((ring.inner + ring.outer) / 2, middleDeg);
      shapes.push({
        type: "path",
        path: buildSectorPath(ring.inner, ring.outer, startDeg, endDeg),
        fillcolor: segmentColor(segment.score),
        line: { color: "rgba(17,38,45,0.28)", width: 1.2 },
      });
      hoverPoints.push({
        x: centroid.x,
        y: centroid.y,
        text: `${segment.name}<br>Segmento ${segment.id}<br>Dano=${segment.score.toFixed(3)}`,
      });
      annotations.push({
        x: centroid.x,
        y: centroid.y,
        text: `<b>${segment.id}</b>`,
        showarrow: false,
        font: { family: "Space Grotesk, sans-serif", size: 12, color: "#11262d" },
      });
    });
  });

  const apex = segmentMap.get(17);
  shapes.push({
    type: "circle",
    x0: -0.16,
    x1: 0.16,
    y0: -0.16,
    y1: 0.16,
    fillcolor: segmentColor(apex.score),
    line: { color: "rgba(17,38,45,0.28)", width: 1.2 },
  });
  hoverPoints.push({ x: 0, y: 0, text: `${apex.name}<br>Segmento 17<br>Dano=${apex.score.toFixed(3)}` });
  annotations.push({
    x: 0,
    y: 0,
    text: "<b>17</b>",
    showarrow: false,
    font: { family: "Space Grotesk, sans-serif", size: 12, color: "#11262d" },
  });

  Plotly.react(
    "bullseye-plot",
    [
      {
        type: "scatter",
        mode: "markers",
        x: hoverPoints.map((point) => point.x),
        y: hoverPoints.map((point) => point.y),
        text: hoverPoints.map((point) => point.text),
        hovertemplate: "%{text}<extra></extra>",
        marker: { size: 18, opacity: 0 },
      },
    ],
    {
      ...plotTheme,
      margin: { l: 8, r: 8, t: 8, b: 8 },
      xaxis: { range: [-1.05, 1.05], visible: false, scaleanchor: "y" },
      yaxis: { range: [-1.05, 1.05], visible: false },
      shapes,
      annotations,
    },
    { displayModeBar: false, responsive: true },
  );
}

function renderLeadBarPlot(simulation) {
  const entries = Object.entries(simulation.lead_projection).sort((a, b) => b[1] - a[1]);
  Plotly.react(
    "lead-bar-plot",
    [
      {
        type: "bar",
        x: entries.map(([lead]) => lead),
        y: entries.map(([, value]) => value),
        text: entries.map(([, value]) => value.toFixed(3)),
        textposition: "outside",
        marker: {
          color: entries.map(([, value]) => (value >= 0 ? "#c84c36" : "#0d6b73")),
          line: { color: "rgba(17,38,45,0.08)", width: 1 },
        },
        hovertemplate: "Derivação %{x}<br>Projeção=%{y:.3f}<extra></extra>",
      },
    ],
    {
      ...plotTheme,
      margin: { l: 42, r: 12, t: 8, b: 64 },
      xaxis: {
        title: "Derivações",
        tickangle: -25,
        fixedrange: true,
      },
      yaxis: {
        title: "Projeção do vetor",
        zeroline: true,
        zerolinecolor: "rgba(17,38,45,0.28)",
        gridcolor: "rgba(17,38,45,0.08)",
        fixedrange: true,
      },
    },
    { displayModeBar: false, responsive: true, staticPlot: true },
  );
}

function renderDamageBarPlot(simulation) {
  const segments = [...simulation.damage_segments].sort((a, b) => b.score - a.score);
  Plotly.react(
    "damage-bar-plot",
    [
      {
        type: "bar",
        x: segments.map((segment) => `S${segment.id}`),
        y: segments.map((segment) => segment.score),
        text: segments.map((segment) => segment.score.toFixed(2)),
        textposition: "outside",
        marker: {
          color: segments.map((segment) => segment.score),
          colorscale: [
            [0, "#f3e6d8"],
            [0.45, "#e58f64"],
            [1, "#8f1d14"],
          ],
          line: { color: "rgba(17,38,45,0.08)", width: 1 },
        },
        hovertemplate: "%{x}<br>%{y:.3f}<extra></extra>",
      },
    ],
    {
      ...plotTheme,
      margin: { l: 32, r: 12, t: 8, b: 40 },
      xaxis: { tickangle: -30 },
      yaxis: { title: "Lesão", range: [0, 1] },
    },
    { displayModeBar: false, responsive: true },
  );
}

function renderECGPlot(simulation) {
  const container = document.getElementById("ecg-grid");
  const leads = state.meta.display_leads;
  if (!container.dataset.ready) {
    container.innerHTML = leads
      .map(
        (lead) => `
          <article class="ecg-card">
            <h3>${lead}</h3>
            <div id="ecg-${lead}" class="ecg-mini-plot"></div>
          </article>
        `,
      )
      .join("");
    container.dataset.ready = "true";
  }

  leads.forEach((lead, index) => {
    Plotly.react(
      `ecg-${lead}`,
      [
        {
          type: "scatter",
          mode: "lines",
          x: simulation.time_ms,
          y: simulation.ecg[lead],
          line: { width: 2.2, color: index % 2 === 0 ? "#0d6b73" : "#c84c36" },
          hovertemplate: `${lead}<br>t=%{x:.0f} ms<br>mV=%{y:.3f}<extra></extra>`,
        },
      ],
      {
        ...plotTheme,
        margin: { l: 36, r: 10, t: 4, b: 28 },
        xaxis: {
          title: index >= leads.length - 2 ? "Tempo (ms)" : "",
          showgrid: true,
          gridcolor: "rgba(17,38,45,0.08)",
        },
        yaxis: {
          title: lead === "I" || lead === "V1" ? "mV" : "",
          range: [-1.15, 1.15],
          showgrid: true,
          gridcolor: "rgba(17,38,45,0.08)",
        },
        showlegend: false,
      },
      { displayModeBar: false, responsive: true },
    );
  });
}

function updateSummary(simulation) {
  const magnitude = computeMagnitude(simulation.input_vector);
  const [topLead, topLeadValue] = Object.entries(simulation.lead_projection).sort(
    (a, b) => Math.abs(b[1]) - Math.abs(a[1]),
  )[0];
  const topSegment = [...simulation.damage_segments].sort((a, b) => b.score - a.score)[0];

  labels.vectorMagnitude.textContent = formatNumber(magnitude);
  labels.cartesianVector.textContent = `[${simulation.input_vector.map((value) => Number(value).toFixed(2)).join(", ")}]`;
  labels.topLead.textContent = `${topLead} (${topLeadValue.toFixed(2)})`;
  labels.topSegment.textContent = `${topSegment.name} (${topSegment.score.toFixed(2)})`;
}

async function fetchSimulation() {
  const payload = getPayload();
  labels.status.textContent = "Simulando…";
  const response = await fetch("/simulation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.status}`);
  }
  const simulation = await response.json();
  renderVectorPlot(simulation);
  renderHiddenSpacePlot(simulation);
  renderDamagePlot(simulation);
  renderDamageBarPlot(simulation);
  renderLeadBarPlot(simulation);
  renderECGPlot(simulation);
  updateSummary(simulation);
  labels.status.textContent = "API conectada";
}

let debounceTimer = null;
function requestSimulation() {
  updateControlLabels();
  window.clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(() => {
    fetchSimulation().catch((error) => {
      labels.status.textContent = "Falha na API";
      console.error(error);
    });
  }, 120);
}

function angleFromPointer(pad, clientX, clientY) {
  const rect = pad.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  const dx = clientX - centerX;
  const dy = centerY - clientY;
  return normalizeAngle((Math.atan2(dy, dx) * 180) / Math.PI);
}

function bindAnglePad(kind) {
  const pad = pads[kind];
  const updateAngle = (clientX, clientY) => {
    state[`${kind}Angle`] = angleFromPointer(pad, clientX, clientY);
    requestSimulation();
  };

  pad.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    pad.setPointerCapture(event.pointerId);
    updateAngle(event.clientX, event.clientY);
  });

  pad.addEventListener("pointermove", (event) => {
    if ((event.buttons & 1) !== 1 && event.pointerType !== "touch") {
      return;
    }
    updateAngle(event.clientX, event.clientY);
  });
}

function applyPreset(preset) {
  state.activeModelId = "";
  state.frontalAngle = preset.frontalAngle;
  state.horizontalAngle = preset.horizontalAngle;
  controls.magnitude.value = preset.magnitude;
  controls.stGain.value = preset.stGain;
  renderModelButtons();
  requestSimulation();
}

function applyOmiModel(modelId) {
  const model = omiModels.find((item) => item.id === modelId);
  if (!model) {
    return;
  }

  const controlState = cartesianToControlState(model.vector);
  state.activeModelId = model.id;
  state.frontalAngle = controlState.frontalAngle;
  state.horizontalAngle = controlState.horizontalAngle;
  controls.magnitude.value = controlState.magnitude.toFixed(2);
  controls.stGain.value = model.stGain.toFixed(2);
  renderModelButtons();
  updateControlLabels();
  requestSimulation();
}

function attachEvents() {
  controls.magnitude.addEventListener("input", requestSimulation);
  controls.stGain.addEventListener("input", requestSimulation);
  bindAnglePad("frontal");
  bindAnglePad("horizontal");

  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", () => applyPreset(presets[button.dataset.preset]));
  });

  modelControls.list.addEventListener("click", (event) => {
    const button = event.target.closest("[data-model-id]");
    if (!button) {
      return;
    }
    applyOmiModel(button.dataset.modelId);
  });
}

async function bootstrap() {
  const [healthResponse, metaResponse] = await Promise.all([
    fetch("/simulation/health"),
    fetch("/simulation/meta"),
  ]);

  if (!healthResponse.ok || !metaResponse.ok) {
    throw new Error("Failed to load metadata");
  }

  state.meta = await metaResponse.json();
  renderModelButtons();
  labels.status.textContent = "Pronta";
  attachEvents();
  updateControlLabels();
  await fetchSimulation();
}

bootstrap().catch((error) => {
  labels.status.textContent = "Erro ao iniciar";
  console.error(error);
});
