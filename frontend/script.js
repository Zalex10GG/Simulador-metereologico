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
}

function showError(msg) {
    const el = $("#error");
    el.textContent = msg;
    el.classList.remove("hidden");
}

function clearError() {
    $("#error").classList.add("hidden");
    $("#error").textContent = "";
}

function showImage(containerId, titleId, imgId, base64, title) {
    $(`#${containerId}`).classList.remove("hidden");
    $(`#${titleId}`).textContent = title;
    $(`#${imgId}`).src = base64;
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
        
        // Single DOM write optimization instead of loop innerHTML +=
        const optionsHtml = state.cities.map(city => `<option value="${city.name}">${city.name}</option>`).join("");
        originSel.innerHTML = optionsHtml;
        destSel.innerHTML = optionsHtml;
        
        // Default select second city for destination to be helpful
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
        
        // Single DOM write optimization
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
        
        // Single DOM write optimization
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
    showLoading(true);

    try {
        const field = $("#field").value;
        const timeIndex = parseInt($("#timeIndex").value, 10);
        const data = await postJSON("/api/map", { field, time_index: timeIndex });
        showImage("mapContainer", "mapTitle", "mapImage", data.image_base64, data.title);
    } catch (e) {
        showError(e.message);
    } finally {
        showLoading(false);
    }
}

async function simulateRoute() {
    clearError();
    const origin = $("#origin").value;
    const destination = $("#destination").value;
    
    // Early frontend validation
    if (origin === destination) {
        showError("La ciudad de origen y destino deben ser diferentes.");
        return;
    }

    hideImage("mapContainer");
    showLoading(true);

    try {
        const data = await postJSON("/api/route", { origin, destination });

        showImage("routeContainer", "routeTitle", "routeImage", data.image_base64, data.route.origin + " -> " + data.route.destination);

        const summary = $("#routeSummary");
        summary.classList.remove("hidden");
        summary.innerHTML = `
            <p><strong>Distancia:</strong> ${data.route.distance_km} km</p>
            <p><strong>Tiempo de vuelo:</strong> ${data.route.flight_time_minutes} min</p>
            <p><strong>Nivel de crucero:</strong> ${data.route.cruise_level}</p>
            <p><strong>Riesgos detectados:</strong></p>
            <ul>
                <li style="color: ${data.risks.icing ? '#00d2ff' : 'inherit'}">Engelamiento: ${data.risks.icing ? "Sí" : "No"}</li>
                <li style="color: ${data.risks.wind_shear ? '#ffaa00' : 'inherit'}">Cizalladura: ${data.risks.wind_shear ? "Sí" : "No"}</li>
                <li style="color: ${data.risks.convection_visibility ? '#ff3333' : 'inherit'}">Convección/Visibilidad: ${data.risks.convection_visibility ? "Sí" : "No"}</li>
            </ul>
        `;
    } catch (e) {
        showError(e.message);
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
