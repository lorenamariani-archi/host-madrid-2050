const state = {
  viewerMap: null,
  viewerEngine: null,
};

const fallbackMadridDistricts = [
  "Centro",
  "Arganzuela",
  "Retiro",
  "Salamanca",
  "Chamartin",
  "Tetuan",
  "Chamberi",
  "Fuencarral-El Pardo",
  "Moncloa-Aravaca",
  "Latina",
  "Carabanchel",
  "Usera",
  "Puente de Vallecas",
  "Moratalaz",
  "Ciudad Lineal",
  "Hortaleza",
  "Villaverde",
  "Villa de Vallecas",
  "Vicalvaro",
  "San Blas-Canillejas",
  "Barajas",
];

const elements = {
  statusText: document.getElementById("status-text"),
  summaryGrid: document.getElementById("summary-grid"),
  districtContent: document.getElementById("district-content"),
  buildingContent: document.getElementById("building-content"),
  programContent: document.getElementById("program-content"),
  climateContent: document.getElementById("climate-content"),
  peopleProgramContent: document.getElementById("people-program-content"),
  narrativeContent: document.getElementById("narrative-content"),
  previewContent: document.getElementById("preview-content"),
  rawJson: document.getElementById("raw-json"),
  realDistrict: document.getElementById("real-district"),
  realStreetType: document.getElementById("real-street-type"),
  realStreetName: document.getElementById("real-street-name"),
  realStreetNumber: document.getElementById("real-street-number"),
  realRefresh: document.getElementById("real-refresh"),
};

const CATEGORY_VISUALS = {
  "Green Infrastructures": {
    short: "GR",
    accent: "#5d8f54",
    soft: "rgba(93, 143, 84, 0.14)",
    strong: "#3e6c37",
    note: "Open-air and climate-positive layer",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 21V12" />
        <path d="M12 12C8 12 6 9.5 6 6.8 6 4.8 7.6 3 9.8 3c1.2 0 2.1.4 2.9 1.3C13.5 3.4 14.4 3 15.6 3 17.8 3 19.4 4.8 19.4 6.8 19.4 9.5 17 12 12 12Z" />
      </svg>
    `,
  },
  Sport: {
    short: "SP",
    accent: "#3f79a6",
    soft: "rgba(63, 121, 166, 0.14)",
    strong: "#245979",
    note: "Active and high-energy spaces",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M3 10v4" />
        <path d="M7 8v8" />
        <path d="M17 8v8" />
        <path d="M21 10v4" />
        <path d="M7 12h10" />
      </svg>
    `,
  },
  Cultural: {
    short: "CU",
    accent: "#9d5d3f",
    soft: "rgba(157, 93, 63, 0.14)",
    strong: "#774226",
    note: "Public culture and exhibition uses",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M4 6h16v12H4z" />
        <path d="M8 10h8" />
        <path d="M8 14h5" />
      </svg>
    `,
  },
  "Learning and Innovation": {
    short: "LI",
    accent: "#7b6eb2",
    soft: "rgba(123, 110, 178, 0.14)",
    strong: "#56488b",
    note: "Learning, work, and experimentation",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M5 5.5h6a3 3 0 0 1 3 3V19H8a3 3 0 0 0-3 3V5.5Z" />
        <path d="M19 5.5h-6a3 3 0 0 0-3 3V19h6a3 3 0 0 1 3 3V5.5Z" />
      </svg>
    `,
  },
  Community: {
    short: "CO",
    accent: "#d07c47",
    soft: "rgba(208, 124, 71, 0.16)",
    strong: "#aa5a27",
    note: "Shared local support and gathering",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M7.5 11a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" />
        <path d="M16.5 11a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" />
        <path d="M3.5 19a4 4 0 0 1 8 0" />
        <path d="M12.5 19a4 4 0 0 1 8 0" />
      </svg>
    `,
  },
  "Care and Social Support": {
    short: "CA",
    accent: "#b85d70",
    soft: "rgba(184, 93, 112, 0.14)",
    strong: "#8f3e51",
    note: "Care-focused and quieter support spaces",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 20s-6-3.8-6-9a3.5 3.5 0 0 1 6-2.5A3.5 3.5 0 0 1 18 11c0 5.2-6 9-6 9Z" />
        <path d="M12 9v6" />
        <path d="M9 12h6" />
      </svg>
    `,
  },
};

const CLIMATE_THEME_VISUALS = [
  {
    key: "heat",
    label: "Heat Protection",
    accent: "#c97d43",
    soft: "rgba(201, 125, 67, 0.15)",
    strong: "#98582a",
    note: "Reduce overheating and improve summer comfort.",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="3.2" />
        <path d="M12 2.5v3" />
        <path d="M12 18.5v3" />
        <path d="M4.5 12h3" />
        <path d="M16.5 12h3" />
        <path d="M6.7 6.7l2.1 2.1" />
        <path d="M15.2 15.2l2.1 2.1" />
      </svg>
    `,
    matches: ["shade", "heat", "cool", "thermal", "pavement", "roof", "facade", "permeable", "ventilation"],
  },
  {
    key: "green",
    label: "Blue-Green Layer",
    accent: "#5d8f54",
    soft: "rgba(93, 143, 84, 0.15)",
    strong: "#3e6c37",
    note: "Trees, planting, and living exterior buffers.",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 21v-4" />
        <path d="M12 17c-3.8 0-6-2.2-6-5 0-2.1 1.4-3.6 3.3-4.2C9.9 5.5 10.8 4 12.7 4c2.8 0 4.8 2 4.8 4.6 1.5.6 2.5 2 2.5 3.8 0 2.8-2.3 4.6-6 4.6H12Z" />
      </svg>
    `,
    matches: ["tree", "planting", "biodiversity", "landscape", "garden"],
  },
  {
    key: "energy",
    label: "Energy Systems",
    accent: "#d2a23a",
    soft: "rgba(210, 162, 58, 0.15)",
    strong: "#9b7517",
    note: "On-site energy generation and efficient operation.",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M13 2 6 13h5l-1 9 8-12h-5l1-8Z" />
      </svg>
    `,
    matches: ["solar", "electricity", "energy", "lighting", "smart building"],
  },
  {
    key: "water",
    label: "Water Cycle",
    accent: "#4d8ea8",
    soft: "rgba(77, 142, 168, 0.15)",
    strong: "#2f677d",
    note: "Capture, reuse, and manage water on site.",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 3s5 5.6 5 9a5 5 0 1 1-10 0c0-3.4 5-9 5-9Z" />
      </svg>
    `,
    matches: ["rainwater", "greywater", "water-sensitive", "water", "drought"],
  },
  {
    key: "future",
    label: "Future Adaptation",
    accent: "#7b6eb2",
    soft: "rgba(123, 110, 178, 0.15)",
    strong: "#56488b",
    note: "Keep spaces flexible for future climate and social change.",
    icon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M8 7h8v8" />
        <path d="M16 7 8 15" />
        <path d="M6 12v6h6" />
      </svg>
    `,
    matches: ["flexible", "reversible", "multi-season", "phased", "refuge", "long-life"],
  },
];

const PEOPLE_VISUALS = {
  "retired couple": {
    short: "RP",
    accent: "#8f6a4b",
    soft: "rgba(143, 106, 75, 0.15)",
    icon: "Quiet",
  },
  businessman: {
    short: "BM",
    accent: "#486d92",
    soft: "rgba(72, 109, 146, 0.15)",
    icon: "Work",
  },
  teenager: {
    short: "TE",
    accent: "#8a5bb6",
    soft: "rgba(138, 91, 182, 0.15)",
    icon: "Youth",
  },
  "international student": {
    short: "IS",
    accent: "#3f8979",
    soft: "rgba(63, 137, 121, 0.15)",
    icon: "Study",
  },
  mom_with_kids: {
    short: "YP",
    accent: "#c67b49",
    soft: "rgba(198, 123, 73, 0.16)",
    icon: "Family",
  },
};

function populateRealDistricts(districts) {
  elements.realDistrict.innerHTML = districts
    .map((district) => `<option value="${district}">${district}</option>`)
    .join("");
}

function setStatus(message) {
  elements.statusText.textContent = message;
}

function clearSections() {
  elements.summaryGrid.innerHTML = "";
  elements.districtContent.innerHTML = '<div class="placeholder">District information will appear here.</div>';
  elements.buildingContent.innerHTML = '<div class="placeholder">Building information will appear here.</div>';
  elements.programContent.innerHTML = '<div class="placeholder">Program categories and spaces will appear here.</div>';
  elements.climateContent.innerHTML = '<div class="placeholder">Climate adaptation strategies will appear here.</div>';
  elements.peopleProgramContent.innerHTML =
    '<div class="placeholder">Profile-specific program matches will appear here after you generate a proposal.</div>';
  elements.narrativeContent.innerHTML = '<div class="placeholder">The architectural narrative will appear here.</div>';
  destroyViewerMap();
  elements.previewContent.innerHTML = '<div class="placeholder">A focused 2D site map will appear here after a real building lookup.</div>';
}

function renderJson(data) {
  elements.rawJson.textContent = JSON.stringify(data, null, 2);
}

async function fetchJson(url, options = {}) {
  const resolvedUrl = url.startsWith("http")
    ? url
    : `${window.location.origin}${url.startsWith("/") ? "" : "/"}${url}`;
  const response = await fetch(resolvedUrl, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }
  return data;
}

async function loadDistrictOptions() {
  try {
    const payload = await fetchJson("/real/districts");
    populateRealDistricts(payload.districts || fallbackMadridDistricts);
  } catch (error) {
    populateRealDistricts(fallbackMadridDistricts);
  }
}

function makeCard(title, value, subtitle) {
  return `
    <article class="summary-card">
      <h3>${title}</h3>
      <div class="metric-value">${value}</div>
      <div class="metric-subtext">${subtitle}</div>
    </article>
  `;
}

function renderSummaryCards(cards) {
  elements.summaryGrid.innerHTML = cards.map((card) => makeCard(card.title, card.value, card.subtitle)).join("");
}

function formatNumber(value) {
  if (typeof value !== "number") {
    return value ?? "n/a";
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function renderTagList(items, className = "") {
  if (!items || items.length === 0) {
    return '<div class="placeholder">No items available.</div>';
  }
  return `<div class="tag-list">${items.map((item) => `<span class="tag ${className}">${item}</span>`).join("")}</div>`;
}

function renderDataRows(rows) {
  return `
    <div class="data-list">
      ${rows
        .map(
          (row) => `
            <div class="data-row">
              <strong>${row.label}</strong>
              <span>${row.value}</span>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderDistrictBlock(title, rows, profiles = []) {
  elements.districtContent.innerHTML = `
    <h3>${title}</h3>
    ${renderDataRows(rows)}
    <div style="height: 14px"></div>
    <p class="panel-label">Main profiles</p>
    ${renderTagList(profiles, "teal-tag")}
  `;
}

function renderBuildingBlock(title, rows, notes = []) {
  elements.buildingContent.innerHTML = `
    <h3>${title}</h3>
    ${renderDataRows(rows)}
    <div style="height: 14px"></div>
    <p class="panel-label">Notes</p>
    ${notes.length ? `<ul>${notes.map((note) => `<li>${note}</li>`).join("")}</ul>` : '<div class="placeholder">No notes available.</div>'}
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatScaleLabel(scale) {
  return scale ? `${scale.charAt(0).toUpperCase()}${scale.slice(1)} scale` : "Program mix";
}

function getCategoryVisual(category) {
  return (
    CATEGORY_VISUALS[category] || {
      short: category.slice(0, 2).toUpperCase(),
      accent: "#6b7c89",
      soft: "rgba(107, 124, 137, 0.14)",
      strong: "#41505a",
      note: "Mixed civic uses",
    }
  );
}

function renderProgramSpaces(spaces, accent) {
  return `
    <div class="program-space-cloud">
      ${spaces
        .map(
          (space) =>
            `<span class="program-space-chip" style="--program-chip:${accent};">${escapeHtml(space)}</span>`,
        )
        .join("")}
    </div>
  `;
}

function renderProgramDrivers(scores, accent) {
  const drivers = [
    ["Urban", scores?.urban_deficit_score ?? 0],
    ["People", scores?.demographic_score ?? 0],
    ["Fit", scores?.building_fit_score ?? 0],
    ["Climate", scores?.climate_bonus ?? 0],
  ];

  return `
    <div class="program-driver-grid">
      ${drivers
        .map(
          ([label, value]) => `
            <div class="program-driver">
              <div class="program-driver-head">
                <span>${label}</span>
                <strong>${formatNumber(value)}</strong>
              </div>
              <div class="program-driver-track">
                <span class="program-driver-fill" style="--program-driver:${accent}; width:${Math.max(
                  8,
                  (Number(value) / 5) * 100,
                )}%"></span>
              </div>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderProgramMiniPlan(spaces, accent, soft) {
  const segments = spaces.slice(0, 4);
  return `
    <div class="program-mini-plan">
      ${segments
        .map(
          (space, index) => `
            <div
              class="program-mini-room"
              style="--program-accent:${accent}; --program-soft:${soft}; flex:${Math.max(1, 4 - index)};">
              <span>${escapeHtml(space)}</span>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function buildHybridZones(entries) {
  const roof = [];
  const ground = [];
  const shared = [];

  entries.forEach((entry, index) => {
    const [category] = entry;
    if (category === "Green Infrastructures") {
      roof.push(entry);
      return;
    }
    if (index === 0 || category === "Community" || category === "Cultural" || category === "Care and Social Support") {
      ground.push(entry);
      return;
    }
    shared.push(entry);
  });

  if (ground.length === 0 && shared.length) {
    ground.push(shared.shift());
  }

  const zones = [];
  if (ground.length) {
    zones.push(["Ground level", "Public access and daily activation", ground]);
  }
  if (shared.length) {
    zones.push(["Shared floors", "Flexible rooms for mixed everyday use", shared]);
  }
  if (roof.length) {
    zones.push(["Roof and exterior", "Climate layer and open-air collective uses", roof]);
  }
  return zones;
}

function renderProgramMix(entries, rankingByCategory, programScale) {
  const weightedEntries = entries.map(([category, spaces]) => ({
    category,
    spaces,
    score: rankingByCategory[category]?.scores?.final_score ?? 1,
    visual: getCategoryVisual(category),
  }));
  const totalScore = weightedEntries.reduce((sum, entry) => sum + entry.score, 0) || 1;
  const zones = buildHybridZones(entries);

  return `
    <section class="program-mix-shell">
      <div class="program-mix-header">
        <div>
          <p class="panel-label">Possible Hybrid Mix</p>
          <h3>${formatScaleLabel(programScale)}</h3>
        </div>
        <p class="metric-subtext">A combined scenario that blends the selected program categories into one adaptive reuse proposal.</p>
      </div>
      <div class="program-mix-ribbon">
        ${weightedEntries
          .map(
            (entry) => `
              <div
                class="program-mix-segment"
                style="--program-accent:${entry.visual.accent}; width:${(entry.score / totalScore) * 100}%;">
                <span>${entry.visual.short}</span>
              </div>
            `,
          )
          .join("")}
      </div>
      <div class="program-mix-legend">
        ${weightedEntries
          .map(
            (entry) => `
              <div class="program-mix-legend-item">
                <span class="program-mix-dot" style="--program-accent:${entry.visual.accent};"></span>
                <strong>${escapeHtml(entry.category)}</strong>
                <span>${formatNumber(entry.score)}</span>
              </div>
            `,
          )
          .join("")}
      </div>
      <div class="program-zone-list">
        ${zones
          .map(
            ([zoneLabel, zoneNote, zoneEntries]) => `
              <div class="program-zone">
                <div class="program-zone-head">
                  <h4>${zoneLabel}</h4>
                  <p>${zoneNote}</p>
                </div>
                <div class="program-zone-items">
                  ${zoneEntries
                    .map(([category, spaces]) => {
                      const visual = getCategoryVisual(category);
                      return `
                        <div class="program-zone-card" style="--program-accent:${visual.accent}; --program-soft:${visual.soft};">
                          <span class="program-zone-badge">${visual.short}</span>
                          <div>
                            <strong>${escapeHtml(category)}</strong>
                            <p>${spaces.slice(0, 2).map((space) => escapeHtml(space)).join(" + ")}</p>
                          </div>
                        </div>
                      `;
                    })
                    .join("")}
                </div>
              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderPeoplePrograms(peoplePrograms = []) {
  if (!peoplePrograms.length) {
    elements.peopleProgramContent.innerHTML =
      '<div class="placeholder">No people-profile program matches are available yet.</div>';
    return;
  }

  elements.peopleProgramContent.innerHTML = `
    <section class="people-program-shell">
      <div class="people-program-header">
        <div>
          <p class="panel-label">People and Program Fit</p>
          <h3>How the proposal serves each group</h3>
        </div>
        <p class="metric-subtext">These cards explain which parts of the program are most useful for each people category and the main activities they support.</p>
      </div>
      <div class="people-program-grid">
        ${peoplePrograms
          .map((person) => {
            const visual = PEOPLE_VISUALS[person.profile_key] || {
              short: "PP",
              accent: "#6b7c89",
              soft: "rgba(107, 124, 137, 0.14)",
              icon: "Use",
            };
            const fitLabel = person.fit_level === "strong" ? "Strong fit" : person.fit_level === "good" ? "Good fit" : "Support fit";
            return `
              <article class="people-program-card" style="--people-accent:${visual.accent}; --people-soft:${visual.soft};">
                <div class="people-program-head">
                  <div class="people-program-badge">
                    <span>${visual.short}</span>
                  </div>
                  <div>
                    <h3>${escapeHtml(person.label)}</h3>
                    <p>${escapeHtml(person.activity_text)}</p>
                  </div>
                </div>
                <div class="people-program-meta">
                  <span class="people-fit-pill">${fitLabel}</span>
                  ${
                    person.is_priority_profile
                      ? '<span class="people-priority-pill">Priority profile in this district</span>'
                      : '<span class="people-priority-pill muted-pill">Secondary profile</span>'
                  }
                </div>
                <div class="people-program-block">
                  <p class="panel-label">Best matching categories</p>
                  <div class="people-chip-row">
                    ${
                      person.matched_categories.length
                        ? person.matched_categories
                            .map((category) => `<span class="people-chip">${escapeHtml(category)}</span>`)
                            .join("")
                        : '<span class="people-chip">General shared spaces</span>'
                    }
                  </div>
                </div>
                <div class="people-program-block">
                  <p class="panel-label">Suggested spaces</p>
                  <div class="people-space-list">
                    ${person.matched_spaces
                      .map((space) => `<span class="people-space-chip">${escapeHtml(space)}</span>`)
                      .join("")}
                  </div>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function getClimateVisual(item) {
  const normalized = String(item).toLowerCase();
  return (
    CLIMATE_THEME_VISUALS.find((theme) => theme.matches.some((match) => normalized.includes(match))) ||
    {
      key: "general",
      label: "Climate Support",
      accent: "#6b7c89",
      soft: "rgba(107, 124, 137, 0.14)",
      strong: "#41505a",
      note: "A general resilience measure for the building and site.",
      icon: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 3 4 7v5c0 5 3.4 8.8 8 10 4.6-1.2 8-5 8-10V7l-8-4Z" />
        </svg>
      `,
    }
  );
}

function summarizeClimateThemes(items) {
  const counts = {};
  items.forEach((item) => {
    const theme = getClimateVisual(item);
    counts[theme.label] = (counts[theme.label] || 0) + 1;
  });
  return Object.entries(counts).sort((left, right) => right[1] - left[1]);
}

function renderProgramBlock(recommendedProgram, categoryRanking = [], programScale = "") {
  const entries = Object.entries(recommendedProgram || {});
  if (!entries.length) {
    elements.programContent.innerHTML = '<div class="placeholder">No recommended program available yet.</div>';
    return;
  }

  const rankingByCategory = Object.fromEntries(categoryRanking.map((item) => [item.category, item]));
  const categoryCards = entries
    .map(([category, spaces]) => {
      const visual = getCategoryVisual(category);
      const rankingItem = rankingByCategory[category];
      const scores = rankingItem?.scores;
      const finalScore = scores?.final_score ?? null;

      return `
        <article class="program-card" style="--program-accent:${visual.accent}; --program-soft:${visual.soft}; --program-strong:${visual.strong};">
          <div class="program-card-head">
            <div class="program-badge">
              <span class="program-badge-icon">${visual.icon}</span>
              <span class="program-badge-code">${visual.short}</span>
            </div>
            <div>
              <h3>${escapeHtml(category)}</h3>
              <p class="program-note">${visual.note}</p>
            </div>
          </div>
          <div class="program-score-row">
            <span>Category strength</span>
            <strong>${finalScore === null ? "n/a" : `${formatNumber(finalScore)} / 5`}</strong>
          </div>
          <div class="program-score-track">
            <span class="program-score-fill" style="width:${Math.max(10, ((Number(finalScore) || 0) / 5) * 100)}%"></span>
          </div>
          ${renderProgramMiniPlan(spaces, visual.accent, visual.soft)}
          <p class="panel-label">Subspaces</p>
          ${renderProgramSpaces(spaces, visual.accent)}
          ${renderProgramDrivers(scores, visual.accent)}
        </article>
      `;
    })
    .join("");

  elements.programContent.innerHTML = `
    <div class="program-dashboard">
      ${renderProgramMix(entries, rankingByCategory, programScale)}
      <div class="program-card-grid">
        ${categoryCards}
      </div>
    </div>
  `;
}

function renderClimateBlock(climatePackage) {
  if (!climatePackage || climatePackage.length === 0) {
    elements.climateContent.innerHTML = '<div class="placeholder">No climate package available yet.</div>';
    return;
  }

  const themeSummary = summarizeClimateThemes(climatePackage);
  elements.climateContent.innerHTML = `
    <div class="climate-dashboard">
      <section class="climate-summary-card">
        <div class="climate-summary-head">
          <div>
            <p class="panel-label">Compact climate package</p>
            <h3>${climatePackage.length} strategies across ${themeSummary.length} themes</h3>
          </div>
          <p class="metric-subtext">A smaller set of visual cards that makes the environmental logic easier to read.</p>
        </div>
        <div class="climate-theme-strip">
          ${themeSummary
            .map(
              ([label, count]) => `
                <span class="climate-theme-chip">
                  <strong>${count}</strong>
                  <span>${escapeHtml(label)}</span>
                </span>
              `,
            )
            .join("")}
        </div>
      </section>
      <div class="climate-card-grid">
        ${climatePackage
          .map((item) => {
            const visual = getClimateVisual(item);
            return `
              <article class="climate-card" style="--climate-accent:${visual.accent}; --climate-soft:${visual.soft}; --climate-strong:${visual.strong};">
                <div class="climate-card-head">
                  <div class="climate-icon">${visual.icon}</div>
                  <div>
                    <h3>${escapeHtml(visual.label)}</h3>
                    <p>${escapeHtml(item)}</p>
                  </div>
                </div>
                <div class="climate-card-meta">
                  <span class="climate-meta-pill">Strategy</span>
                  <span class="climate-meta-note">${escapeHtml(visual.note)}</span>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </div>
  `;
}

function renderNarrative(text) {
  elements.narrativeContent.innerHTML = text
    ? `<p>${text}</p>`
    : '<div class="placeholder">No narrative available yet.</div>';
}

function destroyViewerMap() {
  if (state.viewerMap) {
    if (typeof state.viewerMap.destroy === "function") {
      state.viewerMap.destroy();
    } else if (typeof state.viewerMap.remove === "function") {
      state.viewerMap.remove();
    }
    state.viewerMap = null;
  }
  state.viewerEngine = null;
}

function buildBuildingIcon(label) {
  return window.L.divIcon({
    className: "host-map-marker",
    html: `
      <div class="host-pin-core"></div>
      <div class="host-pin-pulse"></div>
      <div class="host-pin-label">${label || "Building"}</div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

function initializeLeafletMap(preview) {
  if (!window.L) {
    return false;
  }

  const { longitude, latitude } = preview.coordinates;
  const mapContainer = document.getElementById("viewer-map");
  const resetButton = document.getElementById("viewer-reset");

  if (!mapContainer) {
    return false;
  }

  destroyViewerMap();
  mapContainer.innerHTML = "";

  const map = window.L.map("viewer-map", {
    zoomControl: false,
    attributionControl: true,
    scrollWheelZoom: true,
  });
  window.L.control.zoom({ position: "bottomright" }).addTo(map);

  const streetLayer = window.L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
    subdomains: "abcd",
    maxZoom: 20,
  });

  const imageryLayer = window.L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      attribution: "Tiles &copy; Esri",
      maxZoom: 20,
    },
  );

  imageryLayer.addTo(map);

  const focusCircle = window.L.circle([latitude, longitude], {
    radius: 38,
    color: "#ba4a2f",
    weight: 2,
    opacity: 0.95,
    fillColor: "#ba4a2f",
    fillOpacity: 0.08,
  });
  focusCircle.addTo(map);

  const marker = window.L.marker([latitude, longitude], {
    icon: buildBuildingIcon(preview.label),
    title: preview.label || "Selected building",
  }).addTo(map);

  marker.bindPopup(
    `<strong>${preview.label || "Selected building"}</strong><br />${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
    { closeButton: false, offset: [0, -14] },
  ).openPopup();

  const focusBounds = window.L.latLngBounds(
    [latitude - 0.00022, longitude - 0.00028],
    [latitude + 0.00022, longitude + 0.00028],
  );
  map.fitBounds(focusBounds, { padding: [18, 18] });

  const baseMaps = {
    Street: streetLayer,
    Imagery: imageryLayer,
  };
  window.L.control.layers(baseMaps, {}, { position: "topright", collapsed: false }).addTo(map);

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      map.fitBounds(focusBounds, { padding: [18, 18] });
      marker.openPopup();
    });
  }

  state.viewerMap = map;
  state.viewerEngine = "Leaflet";
  return "Leaflet";
}

async function renderLocationPreview(preview) {
  if (!preview || !preview.official_preview) {
    destroyViewerMap();
    elements.previewContent.innerHTML = '<div class="placeholder">No site map is available for this result yet.</div>';
    return;
  }

  const notes = preview.official_preview.notes || [];
  const coordsLabel = `${preview.coordinates.latitude.toFixed(6)}, ${preview.coordinates.longitude.toFixed(6)}`;
  elements.previewContent.innerHTML = `
    <div class="viewer-shell">
      <div class="viewer-toolbar">
        <button id="viewer-reset" class="button button-secondary" type="button">Reset View</button>
      </div>
      <p id="viewer-engine-label" class="viewer-meta">Viewer engine: loading...</p>
      <p class="viewer-hint">This map is centered directly on the looked-up building and now opens in imagery mode by default.</p>
      <p class="viewer-hint">Use the layer switcher to move between imagery and street view, and zoom in to inspect the site closely.</p>
      <div class="viewer-frame">
        <div id="viewer-map" class="viewer-map" aria-label="Focused 2D building map"></div>
      </div>
      <div class="data-list">
        <div class="data-row">
          <strong>Viewer type</strong>
          <span>Interactive 2D site map</span>
        </div>
        <div class="data-row">
          <strong>Map engine</strong>
          <span id="viewer-engine-detail">Loading...</span>
        </div>
        <div class="data-row">
          <strong>Coordinates</strong>
          <span>${coordsLabel}</span>
        </div>
      </div>
      <div class="program-item">
        <h3>Building focus</h3>
        <p class="metric-subtext">
          HOST now gives you a cleaner architectural site map with a strong building marker, tight framing, and imagery as the default reading mode.
        </p>
      </div>
      ${notes.length ? `<ul>${notes.map((note) => `<li>${note}</li>`).join("")}</ul>` : ""}
    </div>
  `;

  const engine = initializeLeafletMap(preview);
  const engineLabel = document.getElementById("viewer-engine-label");
  const engineDetail = document.getElementById("viewer-engine-detail");
  if (engine) {
    if (engineLabel) {
      engineLabel.textContent = `Viewer engine: ${engine}`;
    }
    if (engineDetail) {
      engineDetail.textContent = engine;
    }
  } else {
    if (engineLabel) {
      engineLabel.textContent = "Viewer engine: not available";
    }
    if (engineDetail) {
      engineDetail.textContent = "Not available";
    }
  }
}

async function safeRenderLocationPreview(preview) {
  try {
    await renderLocationPreview(preview);
  } catch (error) {
    destroyViewerMap();

    if (!preview || !preview.coordinates) {
      elements.previewContent.innerHTML =
        '<div class="placeholder">The site map is not available in this browser for the current result.</div>';
      return;
    }

    const coordsLabel = `${preview.coordinates.latitude.toFixed(6)}, ${preview.coordinates.longitude.toFixed(6)}`;
    elements.previewContent.innerHTML = `
      <div class="program-item">
        <h3>Site map fallback</h3>
        <p class="metric-subtext">
          The official location data loaded correctly, but the interactive map could not be rendered in this browser.
        </p>
        <div class="data-list">
          <div class="data-row">
            <strong>Building</strong>
            <span>${escapeHtml(preview.label || "Selected building")}</span>
          </div>
          <div class="data-row">
            <strong>Coordinates</strong>
            <span>${coordsLabel}</span>
          </div>
        </div>
      </div>
    `;
  }
}

function renderDemoDistrict(payload) {
  const district = payload.raw_data;
  renderSummaryCards([
    {
      title: "Urban Deficit Index",
      value: payload.urban_deficit_index.score,
      subtitle: "Higher means more unmet urban facilities.",
    },
    {
      title: "Demographic Pressure Index",
      value: payload.demographic_pressure_index.score,
      subtitle: "Pressure based on local population profiles.",
    },
    {
      title: "Population",
      value: formatNumber(district.population),
      subtitle: "Sample district population.",
    },
    {
      title: "Density",
      value: formatNumber(district.density),
      subtitle: "People per km² in the sample data.",
    },
  ]);

  renderDistrictBlock(
    district.name,
    [
      { label: "Children share", value: `${Math.round(district.children_share * 100)}%` },
      { label: "Young adults share", value: `${Math.round(district.young_adults_share * 100)}%` },
      { label: "Adults share", value: `${Math.round(district.adults_share * 100)}%` },
      { label: "Seniors share", value: `${Math.round(district.seniors_share * 100)}%` },
    ],
    district.main_profiles,
  );
  void safeRenderLocationPreview(null);
}

function renderDemoBuilding(payload) {
  const building = payload.raw_data;
  renderSummaryCards([
    {
      title: "Architectural Capacity",
      value: payload.architectural_capacity_index.score,
      subtitle: `Band: ${payload.architectural_capacity_index.capacity_band}`,
    },
    {
      title: "Total Area",
      value: `${formatNumber(building.total_area)} m²`,
      subtitle: "Sample building gross floor area.",
    },
    {
      title: "Floors",
      value: building.floors,
      subtitle: "Approximate vertical organization.",
    },
    {
      title: "Average Height",
      value: `${formatNumber(building.average_height)} m`,
      subtitle: "Useful for program fit.",
    },
  ]);

  renderBuildingBlock(building.name, [
    { label: "Plot area", value: `${formatNumber(building.plot_area)} m²` },
    { label: "Structure flexibility", value: building.structure_flexibility },
    { label: "Outdoor space", value: building.outdoor_space ? "Yes" : "No" },
    { label: "Roof usable", value: building.roof_usable ? "Yes" : "No" },
  ]);
  void safeRenderLocationPreview(null);
}

function renderProposal(proposal, districtData, buildingData, notes = [], locationPreview = null) {
  const indices = proposal.indices;
  renderSummaryCards([
    {
      title: "Architectural Capacity",
      value: indices.architectural_capacity_index.score,
      subtitle: `Band: ${indices.architectural_capacity_index.capacity_band}`,
    },
    {
      title: "Urban Deficit",
      value: indices.urban_deficit_index.score,
      subtitle: "District facilities pressure.",
    },
    {
      title: "Demographic Pressure",
      value: indices.demographic_pressure_index.score,
      subtitle: "Pressure from local profiles.",
    },
    {
      title: "Climate Risk",
      value: indices.climate_future_risk_index.score,
      subtitle: "Current climate adaptation priority.",
    },
  ]);

  renderDistrictBlock(
    districtData.name,
    [
      { label: "Population", value: formatNumber(districtData.population) },
      { label: "Density", value: formatNumber(districtData.density) },
      { label: "Children share", value: `${Math.round(districtData.children_share * 100)}%` },
      { label: "Seniors share", value: `${Math.round(districtData.seniors_share * 100)}%` },
    ],
    districtData.main_profiles,
  );

  renderBuildingBlock(
    buildingData.name,
    [
      { label: "Area", value: `${formatNumber(buildingData.total_area)} m²` },
      { label: "Plot", value: `${formatNumber(buildingData.plot_area)} m²` },
      { label: "Floors", value: buildingData.floors },
      { label: "Average height", value: `${formatNumber(buildingData.average_height)} m` },
    ],
    notes,
  );

  renderProgramBlock(proposal.recommended_program, proposal.category_ranking, proposal.program_scale);
  renderClimateBlock(proposal.climate_adaptation_package);
  renderPeoplePrograms(proposal.people_programs || []);
  renderNarrative(proposal.architectural_narrative);
  void safeRenderLocationPreview(locationPreview);
}

function renderRealDistrict(payload) {
  const district = payload.normalized_district;
  renderSummaryCards([
    {
      title: "Urban Deficit Index",
      value: payload.indices_preview.urban_deficit_index.score,
      subtitle: "Based on normalized official facility data.",
    },
    {
      title: "Demographic Pressure Index",
      value: payload.indices_preview.demographic_pressure_index.score,
      subtitle: "Based on official demographic structure.",
    },
    {
      title: "Population",
      value: formatNumber(payload.raw_summary.population_total),
      subtitle: "Official Madrid district population.",
    },
    {
      title: "Density",
      value: formatNumber(payload.raw_summary.density_per_km2),
      subtitle: "Official density per km².",
    },
  ]);

  renderDistrictBlock(
    district.name,
    [
      { label: "Children share", value: `${Math.round(district.children_share * 100)}%` },
      { label: "Young adults share", value: `${Math.round(district.young_adults_share * 100)}%` },
      { label: "Adults share", value: `${Math.round(district.adults_share * 100)}%` },
      { label: "Seniors share", value: `${Math.round(district.seniors_share * 100)}%` },
    ],
    district.main_profiles,
  );

  elements.programContent.innerHTML = `
    <div class="program-item">
      <h3>District-only preview</h3>
      <p class="metric-subtext">
        This view already estimates district pressure and profile programs. Add a building address to
        generate the full adaptive reuse proposal.
      </p>
      ${renderTagList(Object.keys(payload.raw_summary.facilities || {}).map((key) => `${key}: ${payload.raw_summary.facilities[key]}`))}
    </div>
  `;
  renderClimateBlock([]);
  renderNarrative(payload.notes.join(" "));
  void safeRenderLocationPreview(null);
}

function renderRealBuilding(payload, options = {}) {
  const { updateSummary = true } = options;

  if (!payload.normalized_building) {
    if (updateSummary) {
      renderSummaryCards([
        {
          title: "Lookup status",
          value: payload.lookup_status,
          subtitle: "Catastro did not return a single detailed property.",
        },
      ]);
    }
    renderBuildingBlock("Building lookup", [{ label: "Status", value: payload.lookup_status }], payload.notes || []);
    void safeRenderLocationPreview(null);
    return;
  }

  const building = payload.normalized_building;
  if (updateSummary) {
    renderSummaryCards([
      {
        title: "Architectural Capacity",
        value: payload.architectural_capacity_index.score,
        subtitle: `Band: ${payload.architectural_capacity_index.capacity_band}`,
      },
      {
        title: "Total Area",
        value: `${formatNumber(building.total_area)} m²`,
        subtitle: "Normalized from public Catastro data.",
      },
      {
        title: "Floors",
        value: building.floors,
        subtitle: "Estimated or normalized from the lookup.",
      },
      {
        title: "Average Height",
        value: `${formatNumber(building.average_height)} m`,
        subtitle: "Normalized HOST building metric.",
      },
    ]);
  }

  renderBuildingBlock(
    building.name,
    [
      { label: "Plot area", value: `${formatNumber(building.plot_area)} m²` },
      { label: "Structure flexibility", value: building.structure_flexibility },
      { label: "Heritage constraint", value: building.heritage_constraint },
      { label: "Condition", value: building.condition },
    ],
    payload.notes || [],
  );
  void safeRenderLocationPreview(payload.location_preview);
}

function renderRealLoadSummary(districtPayload, buildingPayload = null) {
  const cards = [
    {
      title: "Urban Deficit Index",
      value: districtPayload.indices_preview.urban_deficit_index.score,
      subtitle: "Based on normalized official facility data.",
    },
    {
      title: "Demographic Pressure Index",
      value: districtPayload.indices_preview.demographic_pressure_index.score,
      subtitle: "Based on official demographic structure.",
    },
  ];

  if (buildingPayload?.normalized_building) {
    cards.push(
      {
        title: "Architectural Capacity",
        value: buildingPayload.architectural_capacity_index.score,
        subtitle: `Band: ${buildingPayload.architectural_capacity_index.capacity_band}`,
      },
      {
        title: "Total Area",
        value: `${formatNumber(buildingPayload.normalized_building.total_area)} m²`,
        subtitle: "Normalized from public Catastro data.",
      },
    );
  } else {
    cards.push(
      {
        title: "Population",
        value: formatNumber(districtPayload.raw_summary.population_total),
        subtitle: "Official Madrid district population.",
      },
      {
        title: "Building status",
        value: buildingPayload?.lookup_status || "Address pending",
        subtitle: "Building data is shown below when available.",
      },
    );
  }

  renderSummaryCards(cards);
}

function renderPreProposalState(hasBuildingData) {
  elements.programContent.innerHTML = `
    <div class="program-item">
      <h3>${hasBuildingData ? "Ready for proposal" : "District loaded"}</h3>
      <p class="metric-subtext">
        ${
          hasBuildingData
            ? "District and building data are now loaded. Click Generate Real Proposal to calculate the mixed program, climate package, and narrative."
            : "The district data is ready. Complete or correct the address if needed, then click Load again or Generate Real Proposal."
        }
      </p>
    </div>
  `;
  elements.climateContent.innerHTML =
    '<div class="placeholder">The climate package will appear after you generate the real proposal.</div>';
  elements.peopleProgramContent.innerHTML =
    '<div class="placeholder">People-profile program matches will appear after you generate the proposal.</div>';
  elements.narrativeContent.innerHTML =
    '<div class="placeholder">The architectural narrative will appear after you generate the real proposal.</div>';
}

function renderDemoLoadSummary(districtPayload, buildingPayload) {
  renderSummaryCards([
    {
      title: "Urban Deficit Index",
      value: districtPayload.urban_deficit_index.score,
      subtitle: "Estimated from the sample district facilities.",
    },
    {
      title: "Demographic Pressure Index",
      value: districtPayload.demographic_pressure_index.score,
      subtitle: "Based on the sample population profiles.",
    },
    {
      title: "Architectural Capacity",
      value: buildingPayload.architectural_capacity_index.score,
      subtitle: `Band: ${buildingPayload.architectural_capacity_index.capacity_band}`,
    },
    {
      title: "Total Area",
      value: `${formatNumber(buildingPayload.raw_data.total_area)} m²`,
      subtitle: "Sample demo building area.",
    },
  ]);
}

function renderError(message) {
  clearSections();
  setStatus(message);
  elements.rawJson.textContent = JSON.stringify({ error: message }, null, 2);
}

function encodeQueryValue(value) {
  return encodeURIComponent(value ?? "");
}

function getRealQueryString() {
  const params = [
    ["street_type", elements.realStreetType.value.trim() || "CL"],
    ["street_name", elements.realStreetName.value.trim()],
    ["street_number", elements.realStreetNumber.value.trim()],
    ["municipality", "MADRID"],
    ["province", "MADRID"],
  ];

  return params.map(([key, value]) => `${encodeURIComponent(key)}=${encodeQueryValue(value)}`).join("&");
}

async function loadRealDistrict() {
  const district = elements.realDistrict.value.trim();
  const refresh = elements.realRefresh.checked ? "?refresh=true" : "";
  setStatus(`Loading official district data for ${district}...`);
  const payload = await fetchJson(`/real/district/${encodeURIComponent(district)}${refresh}`);
  clearSections();
  renderRealDistrict(payload);
  renderJson(payload);
  setStatus(`Official district data for ${district} loaded.`);
}

async function loadRealBuilding() {
  const query = getRealQueryString();
  setStatus("Looking up the official building data...");
  const payload = await fetchJson(`/real/building/by-address?${query}`);
  clearSections();
  renderRealBuilding(payload);
  renderJson(payload);
  setStatus("Official building lookup finished.");
}

async function loadRealData() {
  const district = elements.realDistrict.value.trim();
  const districtRefresh = elements.realRefresh.checked ? "?refresh=true" : "";
  const buildingQuery = getRealQueryString();

  setStatus(`Loading official district and building data for ${district}...`);

  const [districtResult, buildingResult] = await Promise.allSettled([
    fetchJson(`/real/district/${encodeURIComponent(district)}${districtRefresh}`),
    fetchJson(`/real/building/by-address?${buildingQuery}`),
  ]);

  if (districtResult.status !== "fulfilled") {
    throw districtResult.reason;
  }

  const districtPayload = districtResult.value;
  const buildingPayload = buildingResult.status === "fulfilled" ? buildingResult.value : null;
  clearSections();

  renderRealDistrict(districtPayload);
  renderRealLoadSummary(districtPayload, buildingPayload);
  renderPreProposalState(Boolean(buildingPayload?.normalized_building));

  if (buildingPayload) {
    renderRealBuilding(buildingPayload, { updateSummary: false });
  } else {
    renderBuildingBlock(
      "Building lookup",
      [{ label: "Status", value: "Address lookup could not be completed." }],
      ["The district loaded correctly, but the building lookup failed. Check the address fields and try again."],
    );
    void safeRenderLocationPreview(null);
  }

  renderJson({
    district: districtPayload,
    building: buildingPayload || {
      error: "Building lookup could not be completed for the current address.",
    },
  });

  setStatus(
    buildingPayload
      ? `Official district and building data for ${district} loaded.`
      : `Official district data for ${district} loaded, but the building lookup needs another try.`,
  );
}

async function loadRealProposal() {
  const district = elements.realDistrict.value.trim();
  let query = getRealQueryString();
  if (elements.realRefresh.checked) {
    query = `${query}&refresh=true`;
  }
  setStatus(`Generating official-data proposal for ${district}...`);
  const payload = await fetchJson(`/real/proposal/${encodeURIComponent(district)}?${query}`);
  clearSections();

  if (payload.proposal_status === "ok") {
    renderProposal(payload.proposal, payload.district_data, payload.building_data, payload.notes || [], payload.location_preview);
  } else {
    renderRealDistrict(payload);
    if (payload.building_lookup) {
      renderRealBuilding(payload.building_lookup, { updateSummary: false });
    }
  }

  renderJson(payload);
  setStatus(`Official-data proposal for ${district} loaded.`);
}

async function runSafe(action) {
  try {
    await action();
  } catch (error) {
    renderError(error.message || "Something went wrong.");
  }
}

function loadRealExample() {
  elements.realDistrict.value = "Centro";
  elements.realStreetType.value = "CL";
  elements.realStreetName.value = "ALCALA";
  elements.realStreetNumber.value = "45";
  elements.realRefresh.checked = false;
  runSafe(loadRealData);
}

document.getElementById("real-load-button").addEventListener("click", () => runSafe(loadRealData));
document.getElementById("real-proposal-button").addEventListener("click", () => runSafe(loadRealProposal));

async function initApp() {
  setStatus("Loading the official example...");
  await loadDistrictOptions();
  loadRealExample();
}

void initApp();
