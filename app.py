"""
Star Switch (Web)
Tells you what's exactly in the sky above you right now — visible planets,
moon phase, and constellations — and turns it into a short interactive
story drawn from sky mythology.
"""

import streamlit as st
import ephem
import datetime
import os
import requests
import math
import matplotlib.pyplot as plt
import asyncio
import edge_tts
import io

# ---------- CONFIG ----------
DEFAULT_LAT = 17.3850   # Hyderabad
DEFAULT_LON = 78.4867
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", None)
GROQ_MODEL = "llama-3.3-70b-versatile"

PLANETS = {
    "Mercury": ephem.Mercury,
    "Venus": ephem.Venus,
    "Mars": ephem.Mars,
    "Jupiter": ephem.Jupiter,
    "Saturn": ephem.Saturn,
    "Uranus": ephem.Uranus,
    "Neptune": ephem.Neptune,
}

CULTURES = ["Greek", "Hindu/Vedic", "Norse", "Egyptian"]

CULTURE_THEME = {
    "Greek": {
        "icon": "⚡︎",
        "color": "#d4af37",
        "glow": "rgba(212, 175, 55, 0.5)",
        "gradient": "linear-gradient(135deg, #2b2447, #4a3d7a)",
        "page_bg": "radial-gradient(ellipse at top, #2b2447 0%, #0b0e2e 50%, #05061a 100%)",
        "tagline": "Gods of Olympus",
        "loading": ["Consulting the Oracle...", "Summoning Olympus...", "Reading the fates..."],
    },
    "Hindu/Vedic": {
        "icon": "ॐ",
        "color": "#ff9d4d",
        "glow": "rgba(255, 157, 77, 0.5)",
        "gradient": "linear-gradient(135deg, #4a1f3d, #7a3d2b)",
        "page_bg": "radial-gradient(ellipse at top, #4a1f3d 0%, #2b0e1f 50%, #1a0510 100%)",
        "tagline": "Vedic Cosmos",
        "loading": ["Chanting the mantras...", "Awakening the devas...", "Tuning to the cosmic Om..."],
    },
    "Norse": {
        "icon": "ᚱ",
        "color": "#8ecae6",
        "glow": "rgba(142, 202, 230, 0.5)",
        "gradient": "linear-gradient(135deg, #1a2b3d, #2b4a5e)",
        "page_bg": "radial-gradient(ellipse at top, #1a2b3d 0%, #0b1620 50%, #05090f 100%)",
        "tagline": "Realms of Asgard",
        "loading": ["Casting the runes...", "Calling the Norns...", "Crossing the Bifrost..."],
    },
    "Egyptian": {
        "icon": "𓂀",
        "color": "#2dd4bf",
        "glow": "rgba(45, 212, 191, 0.5)",
        "gradient": "linear-gradient(135deg, #1f3d3a, #3d2b1f)",
        "page_bg": "radial-gradient(ellipse at top, #1f3d3a 0%, #0b1f1d 50%, #05100e 100%)",
        "tagline": "Eye of the Duat",
        "loading": ["Unsealing the tomb...", "Consulting Thoth's scrolls...", "Weighing the feather..."],
    },
}

MYSTIC_VOICE = "en-GB-SoniaNeural"


# ---------- SKY ENGINE ----------
def get_observer(lat, lon, when=None):
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lon)
    obs.date = when or datetime.datetime.now(datetime.timezone.utc)
    return obs


def visible_planets(obs):
    visible = []
    for name, body_cls in PLANETS.items():
        body = body_cls(obs)
        if body.alt > 0:
            visible.append({
                "name": name,
                "altitude_deg": round(float(body.alt) * 180 / ephem.pi, 1),
                "azimuth_deg": round(float(body.az) * 180 / ephem.pi, 1),
                "magnitude": round(body.mag, 2),
            })
    visible.sort(key=lambda p: p["altitude_deg"], reverse=True)
    return visible


def moon_info(obs):
    moon = ephem.Moon(obs)
    phase_pct = moon.phase

    prev_new = ephem.previous_new_moon(obs.date)
    age_days = obs.date - prev_new

    if age_days < 1.84566:
        phase_name = "New Moon"
    elif age_days < 5.53699:
        phase_name = "Waxing Crescent"
    elif age_days < 9.22831:
        phase_name = "First Quarter"
    elif age_days < 12.91963:
        phase_name = "Waxing Gibbous"
    elif age_days < 16.61096:
        phase_name = "Full Moon"
    elif age_days < 20.30228:
        phase_name = "Waning Gibbous"
    elif age_days < 23.99361:
        phase_name = "Last Quarter"
    elif age_days < 27.68493:
        phase_name = "Waning Crescent"
    else:
        phase_name = "New Moon"

    return {
        "illumination_pct": round(phase_pct, 1),
        "phase_name": phase_name,
        "altitude_deg": round(float(moon.alt) * 180 / ephem.pi, 1),
        "azimuth_deg": round(float(moon.az) * 180 / ephem.pi, 1),
        "visible": moon.alt > 0,
    }


def visible_constellation(obs, body_name="Moon"):
    body = ephem.Moon(obs) if body_name == "Moon" else PLANETS[body_name](obs)
    const_code, const_name = ephem.constellation(body)
    return const_name


def get_sky_snapshot(lat, lon, when=None):
    obs = get_observer(lat, lon, when)
    return {
        "location": {"lat": lat, "lon": lon},
        "datetime_utc": str(obs.date),
        "planets": visible_planets(obs),
        "moon": moon_info(obs),
        "moon_constellation": visible_constellation(obs, "Moon"),
    }


# ---------- STORY GENERATOR (Groq / LLaMA) ----------
def generate_story(sky_data, culture="Greek"):
    if not GROQ_API_KEY:
        return _fallback_story(sky_data, culture)

    planet_names = [p["name"] for p in sky_data["planets"]]
    moon = sky_data["moon"]
    if moon["visible"]:
        moon_line = f"- Moon phase: {moon['phase_name']} ({moon['illumination_pct']}% illuminated), visible in the constellation: {sky_data['moon_constellation']}"
    else:
        moon_line = f"- Moon: currently BELOW the horizon, not visible right now (phase is {moon['phase_name']} if it were up)"

    prompt = f"""You are a sky-mythology storyteller specializing in {culture} mythology. Based on tonight's real sky data, write a SHORT (70-100 word) interactive story or vignette that draws specifically from {culture} mythology and tradition, tied to what's actually visible right now. Keep it concise and punchy.

Sky data:
- Visible planets: {', '.join(planet_names) if planet_names else 'none currently above the horizon'}
{moon_line}

Important: only describe objects as visible if they are actually above the horizon per the data above. If the Moon is below the horizon, do not describe seeing it — you can still reference its mythological significance without claiming it's visible.

Write it as a short second-person narrative ("You look up and see..."), evocative but grounded in the real astronomy, drawing only from {culture} mythology and gods/figures. End with one open question inviting the reader to pick what to explore next."""

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 220,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.warning(f"Groq call failed ({e}) — using fallback story.")
        return _fallback_story(sky_data, culture)


def _fallback_story(sky_data, culture="Greek"):
    moon = sky_data["moon"]
    const = sky_data["moon_constellation"]
    planet_line = (
        f"Nearby, {', '.join(p['name'] for p in sky_data['planets'])} watch silently from the dark."
        if sky_data["planets"] else
        "No planets keep it company tonight — the sky belongs to the Moon alone."
    )
    if moon["visible"]:
        moon_line = (
            f"[{culture} mode] You look up and find a {moon['phase_name']} hanging in the constellation of {const}, "
            f"{moon['illumination_pct']}% lit, like a lamp only half-turned toward Earth. "
        )
    else:
        moon_line = (
            f"[{culture} mode] The Moon has slipped below the horizon for now — "
            f"it's a {moon['phase_name']} tonight, waiting for its turn to rise. "
        )
    return (
        moon_line + planet_line +
        " Set GROQ_API_KEY to unlock the full mythology narrator."
    )


# ---------- VISUAL SKY MAP ----------
def draw_sky_map(sky_data):
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="polar")

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 90)
    ax.set_yticks([0, 30, 60, 90])
    ax.set_yticklabels(["90°", "60°", "30°", "Horizon"], fontsize=7)
    ax.set_xticks([0, math.pi/2, math.pi, 3*math.pi/2])
    ax.set_xticklabels(["N", "E", "S", "W"], fontsize=10, fontweight="bold")

    ax.set_facecolor("#0b0e2e")
    fig.patch.set_facecolor("#0b0e2e")
    ax.tick_params(colors="white")
    ax.spines['polar'].set_color("white")
    ax.grid(color="#333366", linestyle="--", linewidth=0.5)

    for p in sky_data["planets"]:
        theta = math.radians(p["azimuth_deg"])
        r = 90 - p["altitude_deg"]
        size = max(30, 200 - (p["magnitude"] * 30))
        ax.scatter(theta, r, s=size, color="#ffe9a8", edgecolors="white", linewidths=0.5, zorder=5)
        ax.annotate(p["name"], (theta, r), color="white", fontsize=8,
                    xytext=(5, 5), textcoords="offset points")

    moon = sky_data["moon"]
    if moon["visible"]:
        theta_m = math.radians(moon["azimuth_deg"])
        r_m = 90 - moon["altitude_deg"]
        ax.scatter(theta_m, r_m, s=250, color="#e8e8e8", edgecolors="#aaaaaa", linewidths=1, zorder=6)
        ax.annotate(f"Moon ({moon['phase_name']})", (theta_m, r_m), color="white", fontsize=8,
                    xytext=(5, -12), textcoords="offset points")

    ax.set_title("Tonight's Sky", color="white", fontsize=14, pad=20)
    plt.tight_layout()
    return fig


# ---------- VOICE NARRATION ----------
async def _synthesize_bytes(text):
    communicate = edge_tts.Communicate(text, MYSTIC_VOICE, rate="-15%", pitch="-8Hz")
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes


def get_voice_audio(text):
    try:
        return asyncio.run(_synthesize_bytes(text))
    except Exception as e:
        st.warning(f"Mystical voice unavailable: {e}")
        return None


# ---------- STREAMLIT APP ----------
st.set_page_config(page_title="Star Switch", page_icon=":stars:", layout="centered")

if "culture" not in st.session_state:
    st.session_state.culture = "Greek"

st.markdown("""
<style>
    @keyframes twinkle {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }
    @keyframes drift {
        from { background-position: 0 0; }
        to { background-position: 1000px 1000px; }
    }
    .stApp {
        background: radial-gradient(ellipse at top, #2b2447 0%, #0b0e2e 50%, #05061a 100%);
        color: #e8e8f0;
        position: relative;
        transition: background 0.6s ease;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            radial-gradient(1px 1px at 20px 30px, white, transparent),
            radial-gradient(1px 1px at 90px 120px, white, transparent),
            radial-gradient(1.5px 1.5px at 160px 60px, #ffe9a8, transparent),
            radial-gradient(1px 1px at 210px 180px, white, transparent),
            radial-gradient(1.5px 1.5px at 280px 40px, white, transparent),
            radial-gradient(1px 1px at 340px 150px, #d4af37, transparent),
            radial-gradient(1px 1px at 400px 90px, white, transparent),
            radial-gradient(1.5px 1.5px at 470px 200px, white, transparent);
        background-repeat: repeat;
        background-size: 500px 500px;
        opacity: 0.6;
        animation: twinkle 4s ease-in-out infinite, drift 120s linear infinite;
        pointer-events: none;
        z-index: 0;
    }
    h1 {
        font-family: 'Georgia', serif;
        background: linear-gradient(90deg, #ffe9a8, #d4af37, #ffe9a8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 3rem !important;
        letter-spacing: 3px;
        margin-bottom: 0;
        text-shadow: 0 0 30px rgba(212, 175, 55, 0.3);
    }
    .stCaption {
        text-align: center;
        color: #9a9ac0 !important;
        font-style: italic;
        margin-bottom: 2rem;
        letter-spacing: 1px;
    }
    h2, h3, h4 {
        color: #ffe9a8 !important;
        font-family: 'Georgia', serif;
        letter-spacing: 1px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #4a3d7a, #2d2456);
        color: #ffe9a8;
        border: 1px solid #d4af37;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 1px;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5d4d9e, #3d3270);
        border-color: #ffe9a8;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.5);
        transform: translateY(-2px);
    }
    .stMarkdown p {
        color: #e8e8f0;
        line-height: 1.7;
    }
    [data-testid="stExpander"] {
        background: rgba(26, 26, 62, 0.4);
        border: 1px solid #3d3270;
        border-radius: 10px;
    }
    hr {
        border-color: #3d3270 !important;
    }
    .stAlert {
        background: rgba(74, 61, 122, 0.3);
        border-radius: 8px;
    }
    .myth-card {
        border-radius: 12px;
        padding: 1.2rem 0.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    .myth-icon {
        font-size: 2.2rem;
        display: block;
        margin-bottom: 0.3rem;
    }
    .myth-name {
        font-family: 'Georgia', serif;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .myth-tagline {
        font-size: 0.75rem;
        opacity: 0.7;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

_active_bg = CULTURE_THEME[st.session_state.culture]["page_bg"]
st.markdown(f"""
<style>
    .stApp {{
        background: {_active_bg} !important;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>STAR SWITCH</h1>", unsafe_allow_html=True)
st.markdown("<p class='stCaption'>What's really in the sky above you, told through myth</p>", unsafe_allow_html=True)

with st.expander("📍 Set your location (optional)", expanded=False):
    col1, col2 = st.columns(2)
    lat = col1.number_input("Latitude", value=DEFAULT_LAT, min_value=-90.0, max_value=90.0, format="%.4f")
    lon = col2.number_input("Longitude", value=DEFAULT_LON, min_value=-180.0, max_value=180.0, format="%.4f")

if "sky" not in st.session_state or st.button("Check tonight's sky"):
    with st.spinner("Calculating the real sky above you..."):
        try:
            st.session_state.sky = get_sky_snapshot(lat, lon)
        except Exception as e:
            st.error(f"Something went wrong calculating the sky: {e}")
            st.session_state.sky = get_sky_snapshot(DEFAULT_LAT, DEFAULT_LON)

sky = st.session_state.sky

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Visible Planets")
    if sky["planets"]:
        for p in sky["planets"]:
            st.markdown(f"**{p['name']}** — {p['altitude_deg']}° up · mag {p['magnitude']}")
    else:
        st.markdown("*None above the horizon right now.*")

with col2:
    st.markdown("### Moon")
    moon = sky["moon"]
    visibility = "visible" if moon["visible"] else "below horizon"
    st.markdown(f"**{moon['phase_name']}** ({moon['illumination_pct']}% lit)")
    st.markdown(f"In *{sky['moon_constellation']}* — {visibility}")

st.pyplot(draw_sky_map(sky))

st.divider()
st.markdown("### Switch Your Sky Story")
st.markdown("<p style='opacity:0.7; margin-top:-10px;'>Same sky. Different gods. Pick your lens.</p>", unsafe_allow_html=True)

cols = st.columns(4)
for i, cname in enumerate(CULTURES):
    theme = CULTURE_THEME[cname]
    is_selected = st.session_state.culture == cname
    border = f"2px solid {theme['color']}" if is_selected else "1px solid #3d3270"
    glow = f"box-shadow: 0 0 18px {theme['glow']};" if is_selected else ""
    with cols[i]:
        st.markdown(f"""
        <div class="myth-card" style="background: {theme['gradient']}; border: {border}; {glow}">
            <span class="myth-icon">{theme['icon']}</span>
            <span class="myth-name" style="color: {theme['color']};">{cname}</span><br>
            <span class="myth-tagline">{theme['tagline']}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Choose", key=f"pick_{cname}", use_container_width=True):
            st.session_state.culture = cname
            st.rerun()

culture = st.session_state.culture
theme = CULTURE_THEME[culture]

st.markdown(f"<p style='text-align:center; color:{theme['color']}; margin-top:0.5rem;'>{theme['icon']} {culture} selected {theme['icon']}</p>", unsafe_allow_html=True)

if st.button(f"Tell the {culture} story", use_container_width=True):
    import random
    loading_msg = random.choice(theme["loading"])
    with st.spinner(loading_msg):
        story = generate_story(sky, culture=culture)

    st.markdown(f"#### {theme['icon']} {culture} Telling")
    st.markdown(
        f"<div style='background: {theme['gradient']}; border-left: 4px solid {theme['color']}; "
        f"padding: 1.2rem 1.5rem; border-radius: 8px; font-style: italic; "
        f"box-shadow: 0 0 25px {theme['glow']};'>{story}</div>",
        unsafe_allow_html=True
    )

    with st.spinner("Summoning the mystical voice..."):
        audio = get_voice_audio(story)
    if audio:
        st.audio(audio, format="audio/mp3")
