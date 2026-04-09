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

    if (!alertBanner || !alertsList) return;

    if (!events || events.length === 0) {
        alertBanner.classList.add("hidden");
        alertsList.innerHTML = `<p class="muted">No alerts yet.</p>`;
        return;
    }

    const latest = events[events.length - 1];
    alertBanner.classList.remove("hidden");
    alertBanner.textContent = `${latest.severity?.toUpperCase() || "ALERT"}: ${latest.message}`;

    alertsList.innerHTML = "";

    [...events].reverse().slice(0, 8).forEach(event => {
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
        if (statusEl) {
            statusEl.textContent = "Online";
            statusEl.className = "status-good";
        }
    } catch (err) {
        const statusEl = document.getElementById("system-status");
        if (statusEl) {
            statusEl.textContent = "Disconnected";
            statusEl.className = "status-bad";
        }
        console.error("Failed to fetch latest data:", err);
    }
}

async function refreshDashboard() {
    await fetchLatest();
}

window.addEventListener("DOMContentLoaded", () => {
    refreshDashboard();
    setInterval(refreshDashboard, 3000);
});
