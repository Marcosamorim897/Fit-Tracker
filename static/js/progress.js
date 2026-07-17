const COLOR = "#e8590c";
const COLOR_SOFT = "rgba(232, 89, 12, 0.15)";

const charts = {};

function lineChart(canvasId, labels, data, label) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  if (charts[canvasId]) charts[canvasId].destroy();
  charts[canvasId] = new Chart(el, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: COLOR,
        backgroundColor: COLOR_SOFT,
        fill: true,
        tension: 0.25,
        spanGaps: true,
        pointRadius: 4,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: false } },
    },
  });
}

async function loadMeasurementCharts() {
  const res = await fetch("/api/progresso/medidas");
  const data = await res.json();
  lineChart("chart-weight", data.labels, data.weight, "Peso (kg)");
  lineChart("chart-bmi", data.labels, data.bmi, "IMC");
  lineChart("chart-waist", data.labels, data.waist, "Cintura (cm)");
  lineChart("chart-fat", data.labels, data.body_fat, "Gordura (%)");
}

async function loadExerciseCharts(name) {
  const res = await fetch(`/api/progresso/exercicio?nome=${encodeURIComponent(name)}`);
  const data = await res.json();
  lineChart("chart-max-weight", data.labels, data.max_weight, "Carga máxima (kg)");
  lineChart("chart-volume", data.labels, data.volume, "Volume (kg)");
}

loadMeasurementCharts();

const select = document.getElementById("exercise-select");
if (select) {
  select.addEventListener("change", () => {
    if (select.value) loadExerciseCharts(select.value);
  });
  const first = select.querySelector("option[value]:not([value=''])");
  if (first) {
    select.value = first.value;
    loadExerciseCharts(first.value);
  }
}
