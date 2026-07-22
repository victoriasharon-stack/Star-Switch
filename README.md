Star Switch
- it tells you what's exactly happeneing in the sky right now and the mythological stories behind them.

# Visuals
<img width="1455" height="811" alt="Screenshot 2026-07-21 at 10 28 04 PM" src="https://github.com/user-attachments/assets/a31adebb-74d4-45de-bbad-6cf86be0cc07" />
<img width="1442" height="785" alt="Screenshot 2026-07-21 at 10 25 07 PM" src="https://github.com/user-attachments/assets/7972e0b1-c4b2-44e8-b46c-cfc771739fe7" /> 
https://github.com/user-attachments/assets/da7fdd77-0c8e-4abd-9e44-14bead070c27



# Demo URL
you can try it out: https://victoriasharon-stack.github.io/Star-Switch/
you dont need to install it or sign up, just let it track the geographic location that you are at for accurate stories.

# Quick Start Off
For the web version (recommended): you can click the link given above as the demo url.
For Command Line Interface (CLI): if you want to run it locally, type this:
```bash
pip install ephem matplotlib requests pyttsx3 edge-tts playsound==1.2.2 colorama
python star_switch.py
```

# Features
1) it tracks a live sky map based off of real calculations.
2) it tells you a nice and sweet bedtime story lol, and they are real ancient mythologies (so cheers to a history lesson ig)
3) the stories are narrated out loud at first, the voice might be a bit cranky and as you fidget around or switch cultures you can listen to a better voice which narrates the story.


# How to run it locally in yo locality 

reqs for sure:
- python 3.10 or a higher version

for installing dependencies:
```bash
pip install ephem matplotlib requests pyttsx3 edge-tts playsound==1.2.2 colorama
```
(link it's been mentioned before, in the quick start off section where you have to run it locally for the CLI ofc)

after that you gotta set yo API key (I personally used Groq Api cause it's free)
search them up using this link: https://console.groq.com/keys
so it's gonna look something like this (welp-):
```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_your_api_key"
```
but the thing is w/o this the app still runs, but you have a simpler built in story rather than a lame Ai generated one.


then you run it:
```bash
python star_switch.py
```

# How does it work? or challenges i faced. (Credits/Acknowledgements)

in my world it just uses star dust & magic but coming to the ground technial talk:
but the trickiest part was handling the mythology switching. The first version had a blend of all four cultures but the output was pretty mushy and weird.
it was a no go welp- it js had generic space-fantasy that didnt actually feel like something og or relatable. 
so i had to switch to each culture giving it's identity and background in depth. which meant the LLM or the voice module had to be committed to one narrative per story generation instead of hedging across all four. 
and i feel like the name of this is hence "Star Switch", which again feels personally to me and to the entirety of why it matters to someone like me with an enriched cultural background. This is too emo lol but yeah.


If you've come this far, thanks for reading. Hope you like it (i know you did).














