# Star Switch 🌌

**Star Switch** tells you whats exactly happening in the sky right now. It pulls out stories from different ancient mythological cultures that are actually accurate according to the calculations. It gives a sense of taste to someone who wants to enrich themselves culturally. Giving short interactive stories of the stars and the planets in the sky right now, it leaves you with a luring question to learn more.

this was built for [Hack Club Horizons Arcana](https://hackclub.com/) 2026.

## What it does

1. **Calculations of the real sky** for the location your are in at this very moment — it tells you which planets are visible, their respective altitude and brightness accordingly, the Moon phases and the illumination or the brightness of it, and which constellation it exactly sits in. This is powered by [`ephem`].
2. (https://pypi.org/project/ephem/), a real astronomical calculation library — not some medicore placeholder data.
3. **Draws live sky map** — a radar like chart which shows exactly where each visible object sits adjacent to the North, East, South, West, and the horizon or should I say (horizons) lol.
4. **Switches between the mythologies** whether you pick Greek, Hindu/Vedic, Norse, or Egyptian, an LLM (Groq / Llama 3.3 70B) writes a little short story about tonight's actual sky through that culture's lens. If you switch again anytime to hear a totally different story on based on a totally different culture.
5. **Narrates it aloud** in an mystical, atmospheric, slowed-down voice (via Microsoft Edge's neural TTS), with an originally composed ambient space-drone track playing while the narration is fetched live.

## Why

Most stargazing apps just label something that you are looking at. Star Switch treats this night sky you are gazing at as a living story and also the same stars or planets that you are looking at right now might mean something else to someone else from another culture. So it's always like to really just peep in and see things from somebody else's pov, tonight.

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

You'll be asked for your location (or press Enter to default to Hyderabad, India- my city and country ofc), then shown tonight's real sky data and a saved sky map image. Pick a mythology from the menu of options given to hear its story and switch back to explore other stories as many times as you's like.

## Screenshots

*(add a terminal screenshot and a sky_map.png example here)*
<img width="1050" height="1050" alt="sky_map" src="https://github.com/user-attachments/assets/dab59e13-77a1-4bea-8a99-7bf555a0c02f" />
<img width="1491" height="778" alt="image" src="https://github.com/user-attachments/assets/41f38315-c05a-47ce-b30b-77b3ddb0c1a6" />




## What's next

- prolly more visible constellations tracked beyond just the Moon's
- A proper GUI instead of terminal menu
- Making the "what will you explore next" story prompts actually clickable/interactive further in depth

---

Built by Victoria Sharon for Horizons Arcana 2026.
Thanks for stopping by <3
