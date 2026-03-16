const metricMap = {
    temperature: "metric-temperature",
    humidity: "metric-humidity",
    pressure: "metric-pressure",
    pm25: "metric-pm25",
    wind_speed: "metric-wind_speed",
    noise_dba: "metric-noise_dba",
    motion: "metric-motion",
    heat_index: "metric-heat_index"
};

const charts = {};

function formatMetricValue(sensor, value, unit) {
    if (value === undefined || value === null) return "--";

    if (sensor === "motion") {
        return Number(value) > 0 ? "Detected" : "None";
    }

    const rounded = Number(value).toFixed(2);
    return unit ? `${rounded} ${unit}` : rounded;
}

function setMetric(sensor, value, unit) {
    const elementId = metricMap[sensor];
    if (!elementId) return;

    const el = document.getElementById(elementId);
    if (!el) return;

    el.textContent = formatMetricValue(sensor, value, unit);
}

function getSeverityClass(severity) {
    if (!severity) return "alert-item";
    return `alert-item ${severity.toLowerCase()}`;
}

function renderAlerts(events) {
    const alertBanner = document.getElementById("alert-banner");
    const alertsList = document.getElementById("alerts-list");

    if (!events || events.length === 0) {
        alertBanner.classList.add("hidden");
        alertsList.innerHTML = `<p class="muted">No alerts yet.</p>`;
        return;
    }

    const latest = events[events.length - 1];
    alertBanner.classList.remove("hidden");
    alertBanner.textContent = `${latest.severity?.toUpperCase() || "ALERT"}: ${latest.message}`;

    alertsList.innerHTML = "";

    [...events].reverse().slice(0, 10).forEach(event => {
        const div = document.createElement("div");
        div.className = getSeverityClass(event.severity);
        div.innerHTML = `
            <strong>${event.severity?.toUpperCase() || "ALERT"}</strong>
            <span>${event.message}</span>
            <small>${event.ts || ""}</small>
        `;
        alertsList.appendChild(div);
    });
}

function buildChart(canvasId, label) {
    const ctx = document.getElementById(canvasId).getContext("2d");
    return new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label,
                    data: [],
                    tension: 0.2,
                    borderWidth: 2,
                    pointRadius: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 6
                    }
                },
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function updateChart(chart, points) {
    if (!chart || !points) return;

    chart.data.labels = points.map(p => {
        if (!p.ts) return "";
        const parts = p.ts.split("T");
        if (parts.length < 2) return p.ts;
        return parts[1].slice(0, 8);
    });

    chart.data.datasets[0].data = points.map(p => p.value);
    chart.update();
}

async function fetchLatest() {
    try {
        const res = await fetch("/api/latest");
        const data = await res.json();

        const latest = data.latest || {};
        const events = data.events || [];

        Object.entries(latest).forEach(([sensor, payload]) => {
            setMetric(sensor, payload.value, payload.unit);
        });

        renderAlerts(events);

        const statusEl = document.getElementById("system-status");
        statusEl.textContent = "Online";
        statusEl.className = "status-good";
    } catch (err) {
        const statusEl = document.getElementById("system-status");
        statusEl.textContent = "Disconnected";
        statusEl.className = "status-bad";
        console.error("Failed to fetch latest data:", err);
    }
}

async function fetchHistory(sensor, chart) {
    try {
        const res = await fetch(`/api/history?sensor=${encodeURIComponent(sensor)}&limit=30`);
        const data = await res.json();
        updateChart(chart, data.points || []);
    } catch (err) {
        console.error(`Failed to fetch history for ${sensor}:`, err);
    }
}

async function refreshDashboard() {
    await fetchLatest();

    await Promise.all([
        fetchHistory("temperature", charts.temperature),
        fetchHistory("humidity", charts.humidity),
        fetchHistory("pm25", charts.pm25),
        fetchHistory("noise_dba", charts.noise)
    ]);
}

window.addEventListener("DOMContentLoaded", () => {
    charts.temperature = buildChart("temperatureChart", "Temperature");
    charts.humidity = buildChart("humidityChart", "Humidity");
    charts.pm25 = buildChart("pm25Chart", "PM2.5");
    charts.noise = buildChart("noiseChart", "Noise dBA");

    refreshDashboard();
    setInterval(refreshDashboard, 3000);
});