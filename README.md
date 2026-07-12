# Star Switch 🌌

**Star Switch** tells you exactly what's in the sky above you right now — real planets, moon phase, and constellations — then turns it into a short mythological story, narrated aloud in an atmospheric voice. Switch between Greek, Hindu/Vedic, Norse, and Egyptian mythology to hear a different story about the *same* real sky.

Built for [Hack Club Horizons Arcana](https://hackclub.com/) 2026.

## What it does

1. **Calculates the real sky** for your location right now — which planets are visible, their altitude and brightness, the Moon's phase and illumination, and which constellation it sits in. Powered by [`ephem`](https://pypi.org/project/ephem/), a real astronomical calculation library — not placeholder data.
2. **Draws a live sky map** — a radar-style chart showing exactly where each visible object sits relative to North, East, South, West, and the horizon.
3. **Switches between mythologies** — pick Greek, Hindu/Vedic, Norse, or Egyptian, and an LLM (Groq / Llama 3.3 70B) writes a short story about tonight's actual sky through that culture's lens. Switch again anytime to hear a totally different take on the same sky.
4. **Narrates it aloud** in an atmospheric, slowed-down voice (via Microsoft Edge's neural TTS), with an original ambient space-drone track playing while the narration is fetched.

## Why

Most stargazing apps just label what you're looking at. Star Switch treats the night sky as a living story — the same stars meant something different to every culture that looked up at them, and this app lets you hear those different stories about the sky that's actually above you, right now, tonight.

## Tech stack

- **`ephem`** — real astronomical calculations (planet positions, moon phase, constellations)
- **`matplotlib`** — live polar sky map rendering
- **Groq API (Llama 3.3 70B)** — mythology-aware story generation
- **`edge-tts`** — atmospheric neural text-to-speech narration
- **`winsound`** — background ambient audio during narration fetch
- **`colorama`** — colored terminal output

## Setup

```bash
pip install ephem matplotlib requests pyttsx3 edge-tts playsound==1.2.2 colorama
```

Set your Groq API key as an environment variable:
```bash
# PowerShell
$env:GROQ_API_KEY="your_key_here"
```

Get a free key at [console.groq.com](https://console.groq.com).

## Run it

```bash
python star_switch.py
```

You'll be asked for your location (or press Enter to default to Hyderabad, India), then shown tonight's real sky data and a saved sky map image. Pick a mythology from the menu to hear its story — switch as many times as you like.

## Screenshots

*(add a terminal screenshot and a sky_map.png example here)*
<img width="1050" height="1050" alt="sky_map" src="https://github.com/user-attachments/assets/dab59e13-77a1-4bea-8a99-7bf555a0c02f" />
<img width="1491" height="778" alt="image" src="https://github.com/user-attachments/assets/41f38315-c05a-47ce-b30b-77b3ddb0c1a6" />




## What's next

- More visible constellations tracked beyond just the Moon's
- A proper GUI instead of terminal menu
- Making the "what will you explore next" story prompts actually clickable/interactive

---

Built by Victoria Sharon for Horizons Arcana 2026.
