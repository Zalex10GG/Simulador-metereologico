const $ = (sel) => document.querySelector(sel);

const state = {
    cities: [],
    fields: [],
    timeCount: 0,
    loading: false,
    initialized: false,
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

function showInitLoading(show) {
    $("#initLoading").classList.toggle("hidden", !show);
    $("#welcomeContainer").classList.toggle("hidden", show);
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
    const cruiseLevel = $("#cruiseLevel").value;
    
    if (origin === destination) {
        showError("La ciudad de origen y destino deben ser diferentes.");
        return;
    }

    hideImage("mapContainer");
    hideImage("routeContainer");
    showLoading(true);

    try {
        const data = await postJSON("/api/route", { origin, destination, cruise_level: cruiseLevel });

        showImage("routeContainer", "routeTitle", "routeImage", data.image_base64, `Ruta Simulación: ${data.route.origin} a ${data.route.destination}`);
        if (data.route_map_base64) {
            $("#routeMapImage").src = data.route_map_base64;
        }

        const summary = $("#routeSummary");
        summary.classList.remove("hidden");
        
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
                <span class="summary-label">Nivel Crucero</span>
                <span class="summary-value">${data.route.cruise_level}</span>
            </div>
            
            <div class="risks-list">
                <span class="risks-list-title">Reporte de Seguridad Aeronáutica</span>
                <div class="risks-grid">
                    <div class="risk-card">
                        <span class="risk-name">Engelamiento</span>
                        <span class="risk-status ${data.risks.icing ? 'risk-active' : 'risk-safe'}" style="color: #06b6d4; background-color: ${data.risks.icing ? '#06b6d4' : '#475569'};"></span>
                    </div>
                    <div class="risk-card">
                        <span class="risk-name">Cizalladura</span>
                        <span class="risk-status ${data.risks.wind_shear ? 'risk-active' : 'risk-safe'}" style="color: #f59e0b; background-color: ${data.risks.wind_shear ? '#f59e0b' : '#475569'};"></span>
                    </div>
                    <div class="risk-card">
                        <span class="risk-name">Turbulencia</span>
                        <span class="risk-status ${data.risks.turbulence ? 'risk-active' : 'risk-safe'}" style="color: #a855f7; background-color: ${data.risks.turbulence ? '#a855f7' : '#475569'};"></span>
                    </div>
                    <div class="risk-card">
                        <span class="risk-name">Convección</span>
                        <span class="risk-status ${data.risks.convection ? 'risk-active' : 'risk-safe'}" style="color: #ef4444; background-color: ${data.risks.convection ? '#ef4444' : '#475569'};"></span>
                    </div>
                    <div class="risk-card">
                        <span class="risk-name">Baja Visibilidad</span>
                        <span class="risk-status ${data.risks.visibility ? 'risk-active' : 'risk-safe'}" style="color: #eab308; background-color: ${data.risks.visibility ? '#eab308' : '#475569'};"></span>
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

let animating = false;
let animTimer = null;

async function animateTimesteps() {
    if (animating) {
        animating = false;
        $("#btnAnimate").innerHTML = '<span class="btn-icon">▶</span> Animar Timesteps';
        clearInterval(animTimer);
        return;
    }

    const field = $("#field").value;
    const options = $("#timeIndex").options;
    if (options.length < 2) return;

    animating = true;
    $("#btnAnimate").innerHTML = '<span class="btn-icon">⏹</span> Detener';

    const tick = async () => {
        if (!animating) return;
        const idx = parseInt($("#timeIndex").value, 10);
        const nextIdx = (idx + 1) % options.length;
        $("#timeIndex").selectedIndex = nextIdx;
        try {
            const data = await postJSON("/api/map", { field, time_index: nextIdx });
            $("#mapContainer").classList.remove("hidden");
            $("#mapTitle").textContent = data.title;
            $("#mapImage").src = data.image_base64;
            $("#welcomeContainer").classList.add("hidden");
        } catch (e) {
            showError(e.message);
            animating = false;
            $("#btnAnimate").innerHTML = '<span class="btn-icon">▶</span> Animar Timesteps';
            clearInterval(animTimer);
            return;
        }
    };

    tick();
    animTimer = setInterval(tick, 2000);
}

async function openSounding(e) {
    const rect = e.target.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const x_pct = x / rect.width;
    const y_pct = y / rect.height;

    const timeIndex = parseInt($("#timeIndex").value, 10);

    const modal = $("#soundingModal");
    const imgWrapper = $("#soundingImgWrapper");
    const loading = $("#soundingLoading");
    const titleEl = $("#soundingTitle");
    const imgEl = $("#soundingImage");
    const coordsEl = $("#soundingCoords");

    modal.classList.remove("hidden");
    loading.classList.remove("hidden");
    imgWrapper.classList.add("hidden");
    coordsEl.textContent = "";

    try {
        const data = await postJSON("/api/sounding", {
            x_pct: x_pct,
            y_pct: y_pct,
            time_index: timeIndex
        });

        loading.classList.add("hidden");
        imgWrapper.classList.remove("hidden");
        imgEl.src = data.image_base64;
        titleEl.textContent = data.title;
        coordsEl.textContent = `Punto Seleccionado — Lat: ${data.lat.toFixed(3)}° | Lon: ${data.lon.toFixed(3)}°`;
    } catch (err) {
        loading.classList.add("hidden");
        modal.classList.add("hidden");
        showError(`Error generando el sondeo: ${err.message}`);
    }
}

async function init() {
    showInitLoading(true);
    try {
        await Promise.all([loadCities(), loadFields(), loadTimeInfo()]);
    } catch (e) {
        showError(`Error inicializando: ${e.message}`);
    } finally {
        showInitLoading(false);
    }

    $("#btnMap").addEventListener("click", generateMap);
    $("#btnRoute").addEventListener("click", simulateRoute);
    $("#btnAnimate").addEventListener("click", animateTimesteps);
    $("#mapImage").addEventListener("click", openSounding);
    
    $("#closeSoundingModal").addEventListener("click", () => {
        $("#soundingModal").classList.add("hidden");
    });
    
    $("#soundingModal").addEventListener("click", (e) => {
        if (e.target === $("#soundingModal")) {
            $("#soundingModal").classList.add("hidden");
        }
    });
}

init();

