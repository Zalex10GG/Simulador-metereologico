const $ = (sel) => document.querySelector(sel);

const state = {
    cities: [],
    fields: [],
    timeCount: 0,
    loading: false,
};

function showLoading(show) {
    state.loading = show;
    $("#loading").classList.toggle("hidden", !show);
    $("#btnMap").disabled = show;
    $("#btnRoute").disabled = show;
    if (show) {
        $("#welcomeContainer").classList.add("hidden");
        clearError();
    }
}

function showError(msg) {
    const el = $("#error");
    el.textContent = msg;
    el.classList.remove("hidden");
    $("#welcomeContainer").classList.add("hidden");
}

function clearError() {
    $("#error").classList.add("hidden");
    $("#error").textContent = "";
}

function showImage(containerId, titleId, imgId, base64, title) {
    $(`#${containerId}`).classList.remove("hidden");
    $(`#${titleId}`).textContent = title;
    $(`#${imgId}`).src = base64;
    $("#welcomeContainer").classList.add("hidden");
}

function hideImage(containerId) {
    $(`#${containerId}`).classList.add("hidden");
}

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(data.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

async function postJSON(url, body) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(data.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

async function loadCities() {
    try {
        state.cities = await fetchJSON("/api/cities");
        const originSel = $("#origin");
        const destSel = $("#destination");
        
        const optionsHtml = state.cities.map(city => `<option value="${city.name}">${city.name}</option>`).join("");
        originSel.innerHTML = optionsHtml;
        destSel.innerHTML = optionsHtml;
        
        // Select second city for destination to make it immediately simulated
        if (destSel.options.length > 1) {
            destSel.selectedIndex = 1;
        }
    } catch (e) {
        showError(`Error cargando ciudades: ${e.message}`);
    }
}

async function loadFields() {
    try {
        state.fields = await fetchJSON("/api/fields");
        const fieldSel = $("#field");
        
        fieldSel.innerHTML = state.fields.map(f => `<option value="${f.id}">${f.name}</option>`).join("");
    } catch (e) {
        showError(`Error cargando campos: ${e.message}`);
    }
}

async function loadTimeInfo() {
    try {
        const times = await fetchJSON("/api/times");
        state.timeCount = times.length;
        const timeSel = $("#timeIndex");
        
        timeSel.innerHTML = times.map(t => `<option value="${t.index}">${t.time}</option>`).join("");
        return;
    } catch {
        state.timeCount = 1;
    }
    const timeSel = $("#timeIndex");
    let optionsHtml = "";
    for (let i = 0; i < state.timeCount; i++) {
        optionsHtml += `<option value="${i}">t=${i}</option>`;
    }
    timeSel.innerHTML = optionsHtml;
}

async function generateMap() {
    clearError();
    hideImage("routeContainer");
    hideImage("mapContainer");
    showLoading(true);

    try {
        const field = $("#field").value;
        const timeIndex = parseInt($("#timeIndex").value, 10);
        const data = await postJSON("/api/map", { field, time_index: timeIndex });
        showImage("mapContainer", "mapTitle", "mapImage", data.image_base64, data.title);
    } catch (e) {
        showError(e.message);
        $("#welcomeContainer").classList.remove("hidden");
    } finally {
        showLoading(false);
    }
}

async function simulateRoute() {
    clearError();
    const origin = $("#origin").value;
    const destination = $("#destination").value;
    
    if (origin === destination) {
        showError("La ciudad de origen y destino deben ser diferentes.");
        return;
    }

    hideImage("mapContainer");
    hideImage("routeContainer");
    showLoading(true);

    try {
        const data = await postJSON("/api/route", { origin, destination });

        showImage("routeContainer", "routeTitle", "routeImage", data.image_base64, `Ruta Simulación: ${data.route.origin} a ${data.route.destination}`);

        const summary = $("#routeSummary");
        summary.classList.remove("hidden");
        
        // Premium structured card injection
        summary.innerHTML = `
            <div class="summary-item">
                <span class="summary-label">Distancia de Vuelo</span>
                <span class="summary-value">${data.route.distance_km} km</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Tiempo Estimado</span>
                <span class="summary-value">${data.route.flight_time_minutes} min</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Altitud Crucero</span>
                <span class="summary-value">${data.route.cruise_level}</span>
            </div>
            
            <div class="risks-list">
                <span class="risks-list-title">Reporte de Seguridad Aeronáutica</span>
                <div class="risks-grid">
                    <div class="risk-card">
                        <span class="risk-name">Engelamiento</span>
                        <span class="risk-status ${data.risks.icing ? 'risk-active' : 'risk-safe'}" style="color: #06b6d4; background-color: #06b6d4;"></span>
                    </div>
                    <div class="risk-card">
                        <span class="risk-name">Cizalladura</span>
                        <span class="risk-status ${data.risks.wind_shear ? 'risk-active' : 'risk-safe'}" style="color: #f59e0b; background-color: #f59e0b;"></span>
                    </div>
                    <div class="risk-card">
                        <span class="risk-name">Convección / Visib.</span>
                        <span class="risk-status ${data.risks.convection_visibility ? 'risk-active' : 'risk-safe'}" style="color: #ef4444; background-color: #ef4444;"></span>
                    </div>
                </div>
            </div>
        `;
    } catch (e) {
        showError(e.message);
        $("#welcomeContainer").classList.remove("hidden");
    } finally {
        showLoading(false);
    }
}

async function init() {
    await Promise.all([loadCities(), loadFields(), loadTimeInfo()]);

    $("#btnMap").addEventListener("click", generateMap);
    $("#btnRoute").addEventListener("click", simulateRoute);
}

init();
