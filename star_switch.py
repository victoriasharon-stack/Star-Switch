"""
Star Switch
Tells you what's exactly in the sky above you right now - visible planets,
moon phase, and constellations - and turns it into a short interactive
story drawn from sky mythology.
"""

import ephem
import datetime
import os
import requests
import math
import matplotlib.pyplot as plt
import pyttsx3

# ---------- CONFIG ----------
DEFAULT_LAT = "17.3850"   # Hyderabad
DEFAULT_LON = "78.4867"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # set this before running
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


# ---------- SKY ENGINE ----------
def get_observer(lat=DEFAULT_LAT, lon=DEFAULT_LON, when=None):
    obs = ephem.Observer()
    obs.lat = lat
    obs.lon = lon
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


def get_sky_snapshot(lat=DEFAULT_LAT, lon=DEFAULT_LON, when=None):
    obs = get_observer(lat, lon, when)
    return {
        "location": {"lat": lat, "lon": lon},
        "datetime_utc": str(obs.date),
        "planets": visible_planets(obs),
        "moon": moon_info(obs),
        "moon_constellation": visible_constellation(obs, "Moon"),
    }


CULTURES = {
    "1": "Greek",
    "2": "Hindu/Vedic",
    "3": "Norse",
    "4": "Egyptian",
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

    prompt = f"""You are a sky-mythology storyteller specializing in {culture} mythology. Based on tonight's real sky data, write a short (120-180 word) interactive story or vignette that draws specifically from {culture} mythology and tradition, tied to what's actually visible right now.

Sky data:
- Visible planets: {', '.join(planet_names) if planet_names else 'none currently above the horizon'}
{moon_line}

Important: only describe objects as visible if they are actually above the horizon per the data above. If the Moon is below the horizon, do not describe seeing it - you can still reference its mythological significance without claiming it's visible.

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
                "max_tokens": 400,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[Groq call failed: {e} - using fallback story]")
        return _fallback_story(sky_data, culture)


def _fallback_story(sky_data, culture="Greek"):
    moon = sky_data["moon"]
    const = sky_data["moon_constellation"]
    planet_line = (
        f"Nearby, {', '.join(p['name'] for p in sky_data['planets'])} watch silently from the dark."
        if sky_data["planets"] else
        "No planets keep it company tonight - the sky belongs to the Moon alone."
    )
    if moon["visible"]:
        moon_line = (
            f"[{culture} mode] You look up and find a {moon['phase_name']} hanging in the constellation of {const}, "
            f"{moon['illumination_pct']}% lit, like a lamp only half-turned toward Earth. "
        )
    else:
        moon_line = (
            f"[{culture} mode] The Moon has slipped below the horizon for now - "
            f"it's a {moon['phase_name']} tonight, waiting for its turn to rise. "
        )
    return (
        moon_line + planet_line +
        " Set GROQ_API_KEY as an environment variable to unlock the full mythology narrator."
    )


# ---------- VISUAL SKY MAP ----------
def draw_sky_map(sky_data, save_path="sky_map.png"):
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="polar")

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 90)
    ax.set_yticks([0, 30, 60, 90])
    ax.set_yticklabels(["90", "60", "30", "Horizon"], fontsize=7)
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
    plt.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    return save_path


# ---------- VOICE NARRATION ----------
def speak_story(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.say(text)
    engine.runAndWait()


# ---------- LOCATION INPUT ----------
def get_location_from_user():
    print(f"\nDefault location: Hyderabad ({DEFAULT_LAT}, {DEFAULT_LON})")
    raw = input("Enter your latitude,longitude (or press Enter for default): ").strip()

    if not raw:
        return DEFAULT_LAT, DEFAULT_LON

    try:
        lat_str, lon_str = raw.split(",")
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            print("Those coordinates are out of range - using default location instead.")
            return DEFAULT_LAT, DEFAULT_LON
        return str(lat), str(lon)
    except (ValueError, IndexError):
        print("Couldn't understand that format - using default location instead.")
        return DEFAULT_LAT, DEFAULT_LON


if __name__ == "__main__":
    print("=" * 50)
    print("STAR SWITCH - what's in the sky right now")
    print("=" * 50)

    lat, lon = get_location_from_user()

    try:
        sky = get_sky_snapshot(lat=lat, lon=lon)
    except Exception as e:
        print(f"\nSomething went wrong calculating the sky: {e}")
        print("Falling back to Hyderabad's coordinates.")
        sky = get_sky_snapshot()

    print(f"\nLocation: {sky['location']['lat']}, {sky['location']['lon']}")
    print(f"Time (UTC): {sky['datetime_utc']}\n")

    print("Visible planets:")
    if sky["planets"]:
        for p in sky["planets"]:
            print(f"  - {p['name']}: {p['altitude_deg']} deg up, mag {p['magnitude']}")
    else:
        print("  None above the horizon right now.")

    print(f"\nMoon: {sky['moon']['phase_name']} "
          f"({sky['moon']['illumination_pct']}% illuminated), "
          f"in {sky['moon_constellation']}")

    map_path = draw_sky_map(sky)
    print(f"\nSky map saved to: {map_path}")

    while True:
        print("\n" + "=" * 50)
        print("SWITCH YOUR SKY STORY")
        for key, name in CULTURES.items():
            print(f"  {key}) {name}")
        print("  q) Quit")
        choice = input("\nPick a culture (1-4) or q to quit: ").strip().lower()

        if choice == "q":
            print("Clear skies!")
            break

        culture = CULTURES.get(choice)
        if not culture:
            print("Not a valid option, try again.")
            continue

        print(f"\n--- Tonight's Story ({culture}) ---\n")
        story = generate_story(sky, culture=culture)
        print(story)

        print("\nReading story aloud...")
        speak_story(story)
