// ---------- CONFIG ----------
const DEFAULT_LAT = 17.3850;  // Hyderabad
const DEFAULT_LON = 78.4867;
const GROQ_API_KEY = "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"; // key
const GROQ_MODEL = "llama-3.3-70b-versatile";

const PLANETS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"];

const CULTURE_THEME = {
  "Greek": { color: "#3b82f6" },
  "Hindu/Vedic": { color: "#f97316" },
  "Norse": { color: "#14b8a6" },
  "Egyptian": { color: "#a855f7" },
};

let currentSky = null;
let currentCulture = null;

function getPhaseName(angle) {
  if (angle < 6 || angle >= 354) return "New Moon";
  if (angle < 84) return "Waxing Crescent";
  if (angle < 96) return "First Quarter";
  if (angle < 174) return "Waxing Gibbous";
  if (angle < 186) return "Full Moon";
  if (angle < 264) return "Waning Gibbous";
  if (angle < 276) return "Last Quarter";
  return "Waning Crescent";
}

function getSkySnapshot(lat, lon) {
  const observer = new Astronomy.Observer(lat, lon, 0);
  const date = new Date();

  const planets = [];
  for (const body of PLANETS) {
    const equ = Astronomy.Equator(body, date, observer, true, true);
    const hor = Astronomy.Horizon(date, observer, equ.ra, equ.dec, "normal");
    if (hor.altitude > 0) {
      const illum = Astronomy.Illumination(body, date);
      planets.push({
        name: body,
        altitude: hor.altitude,
        azimuth: hor.azimuth,
        magnitude: illum.mag,
      });
    }
  }
  planets.sort((a, b) => b.altitude - a.altitude);

  const moonEqu = Astronomy.Equator("Moon", date, observer, true, true);
  const moonHor = Astronomy.Horizon(date, observer, moonEqu.ra, moonEqu.dec, "normal");
  const moonIllum = Astronomy.Illumination("Moon", date);
  const phaseAngle = Astronomy.MoonPhase(date);
  const constellation = Astronomy.Constellation(moonEqu.ra, moonEqu.dec);

  return {
    location: { lat, lon },
    planets,
    moon: {
      phaseName: getPhaseName(phaseAngle),
      illumination: Math.round(moonIllum.phase_fraction * 1000) / 10,
      altitude: moonHor.altitude,
      azimuth: moonHor.azimuth,
      visible: moonHor.altitude > 0,
      constellation: constellation.name,
    },
  };
}

function drawSkyMap(sky) {
  const container = document.getElementById("skyMap");
  const size = 300;
  const center = size / 2;

  let svg = `<svg width="100%" height="100%" viewBox="0 0 ${size} ${size}">`;
  svg += `<text x="${center}" y="14" fill="#99907c" font-size="10" text-anchor="middle" font-family="monospace">N</text>`;
  svg += `<text x="${center}" y="${size - 6}" fill="#99907c" font-size="10" text-anchor="middle" font-family="monospace">S</text>`;
  svg += `<text x="10" y="${center + 4}" fill="#99907c" font-size="10" font-family="monospace">W</text>`;
  svg += `<text x="${size - 16}" y="${center + 4}" fill="#99907c" font-size="10" font-family="monospace">E</text>`;

  svg += `<circle cx="${center}" cy="${center}" r="${center - 20}" fill="none" stroke="rgba(242,202,80,0.15)" stroke-width="1"/>`;
  svg += `<circle cx="${center}" cy="${center}" r="${(center - 20) * 0.5}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>`;

  function toXY(altitude, azimuth) {
    const r = ((90 - altitude) / 90) * (center - 20);
    const angleRad = (azimuth - 90) * (Math.PI / 180);
    const x = center + r * Math.cos(angleRad);
    const y = center + r * Math.sin(angleRad);
    return { x, y };
  }

  for (const p of sky.planets) {
    const { x, y } = toXY(p.altitude, p.azimuth);
    const r = Math.max(2, 6 - p.magnitude);
    svg += `<circle cx="${x}" cy="${y}" r="${r}" fill="#f2ca50" opacity="0.9"/>`;
    svg += `<text x="${x + 8}" y="${y + 3}" fill="#eae1d4" font-size="9" font-family="monospace">${p.name}</text>`;
  }

  if (sky.moon.visible) {
    const { x, y } = toXY(sky.moon.altitude, sky.moon.azimuth);
    svg += `<circle cx="${x}" cy="${y}" r="7" fill="#e8e8e8" stroke="#aaa"/>`;
    svg += `<text x="${x + 10}" y="${y + 3}" fill="#eae1d4" font-size="9" font-family="monospace">Moon</text>`;
  }

  svg += `</svg>`;
  container.innerHTML = svg;
}

function renderSkyInfo(sky) {
  document.getElementById("moonPhase").textContent = sky.moon.phaseName;
  document.getElementById("moonDetail").textContent =
    `${sky.moon.illumination}% illuminated · in ${sky.moon.constellation}` +
    (sky.moon.visible ? "" : " (below horizon)");

  const list = document.getElementById("planetList");
  list.innerHTML = "";
  if (sky.planets.length === 0) {
    list.innerHTML = "<li>None above the horizon right now.</li>";
  } else {
    for (const p of sky.planets) {
      const li = document.createElement("li");
      li.innerHTML = `<span>${p.name}</span><span>${Math.round(p.altitude)}° up</span>`;
      list.appendChild(li);
    }
  }
}

async function generateStory(sky, culture) {
  const planetNames = sky.planets.map(p => p.name).join(", ") || "none currently above the horizon";
  const moonLine = sky.moon.visible
    ? `Moon phase: ${sky.moon.phaseName} (${sky.moon.illumination}% illuminated), visible in ${sky.moon.constellation}`
    : `Moon: currently BELOW the horizon (phase is ${sky.moon.phaseName} if it were up)`;

  const prompt = `You are a sky-mythology storyteller specializing in ${culture} mythology. Based on tonight's real sky data, write a SHORT (70-100 word) story drawn from ${culture} mythology and tradition, tied to what's actually visible right now.

Sky data:
- Visible planets: ${planetNames}
- ${moonLine}

Important: only describe objects as visible if they are actually above the horizon. Write it as a short second-person narrative ("You look up and see..."), evocative but grounded in the real astronomy, drawing only from ${culture} mythology. End with one open question inviting the reader to explore further.`;

  try {
    const resp = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${GROQ_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: [{ role: "user", content: prompt }],
        temperature: 0.8,
        max_tokens: 220,
      }),
    });
    const data = await resp.json();
    return data.choices[0].message.content;
  } catch (e) {
    console.error("Groq call failed:", e);
    return fallbackStory(sky, culture);
  }
}

function fallbackStory(sky, culture) {
  const moon = sky.moon;
  const planetLine = sky.planets.length
    ? `Nearby, ${sky.planets.map(p => p.name).join(", ")} watch silently from the dark.`
    : "No planets keep it company tonight.";
  const moonLine = moon.visible
    ? `You look up and find a ${moon.phaseName} hanging in ${moon.constellation}, ${moon.illumination}% lit.`
    : `The Moon has slipped below the horizon for now — it's a ${moon.phaseName} tonight.`;
  return `[${culture} mode] ${moonLine} ${planetLine} (Add your Groq API key in script.js to unlock full mythology stories.)`;
}

function speakStory(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.9;
  utterance.pitch = 0.9;
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.name.includes("Female") || v.name.includes("Google UK English Female"));
  if (preferred) utterance.voice = preferred;
  window.speechSynthesis.speak(utterance);
}

async function loadSky(lat, lon) {
  currentSky = getSkySnapshot(lat, lon);
  drawSkyMap(currentSky);
  renderSkyInfo(currentSky);
}

document.getElementById("useLocationBtn").addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Geolocation not supported, using default location.");
    loadSky(DEFAULT_LAT, DEFAULT_LON);
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => loadSky(pos.coords.latitude, pos.coords.longitude),
    () => loadSky(DEFAULT_LAT, DEFAULT_LON)
  );
});

document.getElementById("setLocationBtn").addEventListener("click", () => {
  const val = document.getElementById("manualLocation").value.trim();
  const parts = val.split(",").map(s => parseFloat(s.trim()));
  if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1]) &&
      parts[0] >= -90 && parts[0] <= 90 && parts[1] >= -180 && parts[1] <= 180) {
    loadSky(parts[0], parts[1]);
  } else {
    alert("Couldn't understand that format, using default location.");
    loadSky(DEFAULT_LAT, DEFAULT_LON);
  }
});

document.querySelectorAll(".lens-card").forEach(card => {
  card.addEventListener("click", async () => {
    document.querySelectorAll(".lens-card").forEach(c => c.classList.remove("selected"));
    card.classList.add("selected");
    const culture = card.dataset.culture;
    currentCulture = culture;
    const theme = CULTURE_THEME[culture];

    const storyBox = document.getElementById("storyBox");
    storyBox.innerHTML = `<p class="placeholder">Consulting ${culture} mythology...</p>`;

    const story = await generateStory(currentSky, culture);

    storyBox.innerHTML = `
      <div class="story-content">
        <p class="story-culture-label" style="color:${theme.color}">TOLD THROUGH ${culture.toUpperCase()}</p>
        <p class="story-text">${story}</p>
      </div>
    `;
    speakStory(story);
  });
});

loadSky(DEFAULT_LAT, DEFAULT_LON);