const AXIS_LIMIT = 1.2;
const CANVAS_SIZE = 420;
const CANVAS_PADDING = 32;
const POINT_RADIUS = 8;
const BULLSEYE_SCALE = 1;
const BULLSEYE_ROTATION_OFFSET = 0;
const BULLSEYE_SEGMENT_COLORS = [
  "#8FAADC", "#F6BD60", "#F28482", "#84A59D", "#90BE6D", "#F7EDE2",
  "#CDB4DB", "#FFC8DD", "#B5838D", "#A0C4FF", "#BDB2FF", "#FFD6A5",
  "#CAFFBF", "#FFADAD", "#D0F4DE", "#FDFFB6", "#9BF6FF",
];

const planeDefinitions = [
  { id: "plane-xy", title: "Plano XY", axisX: "x", axisY: "y", subtitle: "Largura x anterioridade" },
  { id: "plane-xz", title: "Plano XZ", axisX: "x", axisY: "z", subtitle: "Largura x altura" },
];

const leadColors = {
  V1: "#c84c36",
  V2: "#dd6e42",
  V3: "#e58f64",
  V4: "#0d6b73",
  V5: "#147d64",
  V6: "#40916c",
  V3R: "#7b2cbf",
  V4R: "#9d4edd",
  V7: "#1d3557",
  V8: "#457b9d",
  V9: "#5fa8d3",
};

const editorState = {
  leadOrder: [],
  leads: {},
  selectedLead: null,
  dirty: false,
  drag: null,
};

const plotTheme = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: {
    family: "IBM Plex Sans, sans-serif",
    color: "#11262d",
  },
};

function cloneLeads(leads) {
  return Object.fromEntries(
    Object.entries(leads).map(([lead, coords]) => [lead, { ...coords }]),
  );
}

function formatNumber(value) {
  return Number(value).toFixed(2);
}

function setStatus(message) {
  document.getElementById("editor-status").textContent = message;
}

function axisToCanvas(canvas, valueX, valueY) {
  const drawableSize = canvas.width - 2 * CANVAS_PADDING;
  const px = CANVAS_PADDING + ((valueX + AXIS_LIMIT) / (2 * AXIS_LIMIT)) * drawableSize;
  const py = CANVAS_PADDING + ((AXIS_LIMIT - valueY) / (2 * AXIS_LIMIT)) * drawableSize;
  return { x: px, y: py };
}

function canvasToAxis(canvas, px, py) {
  const drawableSize = canvas.width - 2 * CANVAS_PADDING;
  const x = ((px - CANVAS_PADDING) / drawableSize) * (2 * AXIS_LIMIT) - AXIS_LIMIT;
  const y = AXIS_LIMIT - ((py - CANVAS_PADDING) / drawableSize) * (2 * AXIS_LIMIT);
  return {
    x: Math.max(-AXIS_LIMIT, Math.min(AXIS_LIMIT, x)),
    y: Math.max(-AXIS_LIMIT, Math.min(AXIS_LIMIT, y)),
  };
}

function renderLeadList() {
  const container = document.getElementById("lead-list");
  container.innerHTML = editorState.leadOrder
    .map((lead) => {
      const coords = editorState.leads[lead];
      const activeClass = lead === editorState.selectedLead ? " is-active" : "";
      return `
        <button class="editor-lead-button${activeClass}" data-lead="${lead}">
          <span class="editor-lead-swatch" style="background:${leadColors[lead] || "#0d6b73"}"></span>
          <span>${lead}</span>
          <span class="editor-lead-coords">${formatNumber(coords.x)}, ${formatNumber(coords.y)}, ${formatNumber(coords.z)}</span>
        </button>
      `;
    })
    .join("");
}

function renderLeadDetail() {
  const lead = editorState.selectedLead;
  if (!lead) {
    document.getElementById("lead-detail").textContent = "-";
    return;
  }
  const coords = editorState.leads[lead];
  document.getElementById("lead-detail").innerHTML = `
    <strong>${lead}</strong><br />
    x = ${formatNumber(coords.x)}<br />
    y = ${formatNumber(coords.y)}<br />
    z = ${formatNumber(coords.z)}<br />
    <br />
    estado = ${editorState.dirty ? "não salvo" : "salvo"}<br />
    edição = drag and drop em XY e XZ<br />
    3D = gerado sob demanda
  `;
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
  const angle = (angleDeg * Math.PI) / 180 + BULLSEYE_ROTATION_OFFSET;
  return {
    x: BULLSEYE_SCALE * radius * Math.cos(angle),
    y: BULLSEYE_SCALE * radius * Math.sin(angle),
    z: bullseyeZ(radius),
  };
}

function buildBullseyeMesh() {
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
        color: BULLSEYE_SEGMENT_COLORS[colorIndex],
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
    color: BULLSEYE_SEGMENT_COLORS[16],
  });

  return {
    segments,
    rings: [0.18, 0.40, 0.70, 1.00],
    radialLines: [
      ...anglesBasal.map((angle) => ({ startRadius: 0.70, endRadius: 1.00, angleDeg: angle })),
      ...anglesMid.map((angle) => ({ startRadius: 0.40, endRadius: 0.70, angleDeg: angle })),
      ...anglesApical.map((angle) => ({ startRadius: 0.18, endRadius: 0.40, angleDeg: angle })),
    ],
  };
}

function canvasPointFromXY(canvas, x, y) {
  return axisToCanvas(canvas, x, y);
}

function canvasPointFromXZ(canvas, x, z) {
  return axisToCanvas(canvas, x, z);
}

function drawProjectedPolygon(ctx, canvas, points, project, color) {
  const projected = points.map((point) => project(canvas, point));
  ctx.beginPath();
  ctx.moveTo(projected[0].x, projected[0].y);
  projected.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.globalAlpha = 0.42;
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.strokeStyle = "rgba(17,38,45,0.3)";
  ctx.lineWidth = 1;
  ctx.stroke();
}

function buildMeshBoundary(rows) {
  const boundary = [];
  const lastRowIndex = rows.length - 1;
  const lastColIndex = rows[0].length - 1;

  rows[0].forEach((point) => boundary.push(point));
  for (let rowIndex = 1; rowIndex <= lastRowIndex; rowIndex += 1) {
    boundary.push(rows[rowIndex][lastColIndex]);
  }
  for (let colIndex = lastColIndex - 1; colIndex >= 0; colIndex -= 1) {
    boundary.push(rows[lastRowIndex][colIndex]);
  }
  for (let rowIndex = lastRowIndex - 1; rowIndex > 0; rowIndex -= 1) {
    boundary.push(rows[rowIndex][0]);
  }

  return boundary;
}

function drawBullseyeGuidesXY(ctx, canvas) {
  const geometry = buildBullseyeMesh();

  geometry.segments.forEach((segment) => {
    drawProjectedPolygon(
      ctx,
      canvas,
      buildMeshBoundary(segment.rows),
      (targetCanvas, point) => canvasPointFromXY(targetCanvas, point.x, point.y),
      segment.color,
    );
  });
}

function drawBullseyeGuidesXZ(ctx, canvas) {
  const geometry = buildBullseyeMesh();

  geometry.segments.forEach((segment) => {
    drawProjectedPolygon(
      ctx,
      canvas,
      buildMeshBoundary(segment.rows),
      (targetCanvas, point) => canvasPointFromXZ(targetCanvas, point.x, point.z),
      segment.color,
    );
  });
}

function drawPlane(plane) {
  const canvas = document.getElementById(plane.id);
  const ctx = canvas.getContext("2d");
  const left = CANVAS_PADDING;
  const top = CANVAS_PADDING;
  const right = canvas.width - CANVAS_PADDING;
  const bottom = canvas.height - CANVAS_PADDING;
  const midX = (left + right) / 2;
  const midY = (top + bottom) / 2;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#fffdf9";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "#d9d2c7";
  ctx.lineWidth = 1;
  ctx.strokeRect(left, top, right - left, bottom - top);

  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(left, midY);
  ctx.lineTo(right, midY);
  ctx.moveTo(midX, top);
  ctx.lineTo(midX, bottom);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = "#5c6b73";
  ctx.font = "bold 11px Helvetica";
  ctx.textAlign = "center";
  ctx.fillText(plane.axisY.toUpperCase(), midX, top - 12);
  ctx.fillText(plane.axisX.toUpperCase(), right + 16, midY + 4);

  if (plane.id === "plane-xy") {
    drawBullseyeGuidesXY(ctx, canvas);
  } else if (plane.id === "plane-xz") {
    drawBullseyeGuidesXZ(ctx, canvas);
  }

  editorState.leadOrder.forEach((lead) => {
    const coords = editorState.leads[lead];
    const point = axisToCanvas(canvas, coords[plane.axisX], coords[plane.axisY]);
    ctx.beginPath();
    ctx.fillStyle = leadColors[lead] || "#0d6b73";
    ctx.strokeStyle = "#11262d";
    ctx.lineWidth = lead === editorState.selectedLead ? 3 : 1;
    ctx.arc(point.x, point.y, POINT_RADIUS, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#11262d";
    ctx.font = "bold 10px Helvetica";
    ctx.fillText(lead, point.x, point.y - 14);
  });
}

function renderPlanes() {
  planeDefinitions.forEach(drawPlane);
}

function buildBullseye3DTraces() {
  const scale = BULLSEYE_SCALE;
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
      contours: { x: { show: false }, y: { show: false }, z: { show: false } },
    });
  });

  const thetaLine = Array.from({ length: 241 }, (_, index) => (2 * Math.PI * index) / 240);
  [[0.18, 5], [0.4, 5], [0.7, 5], [1.0, 6]].forEach(([radius, width]) => {
    traces.push({
      type: "scatter3d",
      mode: "lines",
      x: thetaLine.map((theta) => scale * radius * Math.cos(theta + BULLSEYE_ROTATION_OFFSET)),
      y: thetaLine.map((theta) => scale * radius * Math.sin(theta + BULLSEYE_ROTATION_OFFSET)),
      z: thetaLine.map(() => bullseyeZ(radius)),
      line: { color: "black", width },
      hoverinfo: "skip",
      showlegend: false,
    });
  });

  geometry.radialLines.forEach(({ startRadius, endRadius, angleDeg }) => {
      const angle = (angleDeg * Math.PI) / 180 + BULLSEYE_ROTATION_OFFSET;
      traces.push({
        type: "scatter3d",
        mode: "lines",
        x: [scale * startRadius * Math.cos(angle), scale * endRadius * Math.cos(angle)],
        y: [scale * startRadius * Math.sin(angle), scale * endRadius * Math.sin(angle)],
        z: [bullseyeZ(startRadius), bullseyeZ(endRadius)],
        line: { color: "black", width: 3 },
        hoverinfo: "skip",
        showlegend: false,
      });
    });

  traces.push({
    type: "scatter3d",
    mode: "markers+text",
    x: editorState.leadOrder.map((lead) => editorState.leads[lead].x),
    y: editorState.leadOrder.map((lead) => editorState.leads[lead].y),
    z: editorState.leadOrder.map((lead) => editorState.leads[lead].z),
    text: editorState.leadOrder,
    textposition: "top center",
    marker: {
      size: editorState.leadOrder.map((lead) => (lead === editorState.selectedLead ? 7 : 5)),
      color: editorState.leadOrder.map((lead) => leadColors[lead] || "#0d6b73"),
      line: { color: "#11262d", width: 1 },
    },
    hovertemplate: "%{text}<extra></extra>",
    name: "Leads",
  });

  return traces;
}

function generate3DImage() {
  setStatus(editorState.dirty ? "Imagem 3D gerada; alterações pendentes" : "Imagem 3D gerada");
  Plotly.react(
    "editor-3d-plot",
    buildBullseye3DTraces(),
    {
      ...plotTheme,
      margin: { l: 0, r: 0, t: 0, b: 0 },
      scene: {
        xaxis: { title: "X", range: [-1, 1], backgroundcolor: "rgba(255,255,255,0)" },
        yaxis: { title: "Y", range: [-1, 1], backgroundcolor: "rgba(255,255,255,0)" },
        zaxis: { title: "Z", range: [-1.2, 1.2], backgroundcolor: "rgba(255,255,255,0)" },
        aspectmode: "cube",
        camera: { eye: { x: 1.55, y: 1.45, z: 1.05 } },
      },
      showlegend: false,
    },
    { displayModeBar: false, responsive: true },
  );
}

function renderAll() {
  renderLeadList();
  renderLeadDetail();
  renderPlanes();
}

function selectLead(lead) {
  editorState.selectedLead = lead;
  renderAll();
}

function updateLead(lead, axisA, valueA, axisB, valueB) {
  editorState.leads[lead][axisA] = Number(valueA.toFixed(2));
  editorState.leads[lead][axisB] = Number(valueB.toFixed(2));
  editorState.selectedLead = lead;
  editorState.dirty = true;
  setStatus("Alterações pendentes");
  renderAll();
}

function hitTestLead(canvas, plane, event) {
  const rect = canvas.getBoundingClientRect();
  const px = event.clientX - rect.left;
  const py = event.clientY - rect.top;

  for (const lead of [...editorState.leadOrder].reverse()) {
    const coords = editorState.leads[lead];
    const point = axisToCanvas(canvas, coords[plane.axisX], coords[plane.axisY]);
    if (Math.hypot(point.x - px, point.y - py) <= POINT_RADIUS + 4) {
      return lead;
    }
  }
  return null;
}

function attachPlaneInteractions() {
  planeDefinitions.forEach((plane) => {
    const canvas = document.getElementById(plane.id);

    canvas.addEventListener("pointerdown", (event) => {
      const lead = hitTestLead(canvas, plane, event);
      if (!lead) return;
      editorState.drag = { lead, planeId: plane.id };
      selectLead(lead);
      canvas.setPointerCapture(event.pointerId);
    });

    canvas.addEventListener("pointermove", (event) => {
      if (!editorState.drag || editorState.drag.planeId !== plane.id) return;
      const rect = canvas.getBoundingClientRect();
      const px = Math.max(CANVAS_PADDING, Math.min(canvas.width - CANVAS_PADDING, event.clientX - rect.left));
      const py = Math.max(CANVAS_PADDING, Math.min(canvas.height - CANVAS_PADDING, event.clientY - rect.top));
      const axisPoint = canvasToAxis(canvas, px, py);
      updateLead(editorState.drag.lead, plane.axisX, axisPoint.x, plane.axisY, axisPoint.y);
    });

    canvas.addEventListener("pointerup", () => {
      editorState.drag = null;
    });

    canvas.addEventListener("pointerleave", () => {
      editorState.drag = null;
    });
  });
}

async function loadEditorState() {
  setStatus("Carregando…");
  const response = await fetch("/simulation/lead-editor");
  if (!response.ok) throw new Error("Falha ao carregar leads");
  const payload = await response.json();
  editorState.leadOrder = payload.lead_order;
  editorState.leads = cloneLeads(payload.leads);
  editorState.selectedLead = editorState.selectedLead || editorState.leadOrder[0];
  editorState.dirty = false;
  setStatus("Pronto");
  renderAll();
}

async function saveEditorState() {
  setStatus("Salvando…");
  const response = await fetch("/simulation/lead-editor", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ leads: editorState.leads }),
  });
  if (!response.ok) throw new Error("Falha ao salvar leads");
  const payload = await response.json();
  editorState.leadOrder = payload.lead_order;
  editorState.leads = cloneLeads(payload.leads);
  editorState.dirty = false;
  setStatus("Salvo");
  renderAll();
}

function attachUI() {
  document.getElementById("lead-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-lead]");
    if (!button) return;
    selectLead(button.dataset.lead);
  });

  document.getElementById("save-leads-button").addEventListener("click", () => {
    saveEditorState().catch((error) => {
      setStatus("Erro ao salvar");
      console.error(error);
    });
  });

  document.getElementById("reload-leads-button").addEventListener("click", () => {
    loadEditorState().catch((error) => {
      setStatus("Erro ao recarregar");
      console.error(error);
    });
  });

  document.getElementById("generate-3d-button").addEventListener("click", () => {
    generate3DImage();
  });

  attachPlaneInteractions();
}

attachUI();
loadEditorState().catch((error) => {
  setStatus("Erro ao iniciar");
  console.error(error);
});
