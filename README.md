# Screen Consent Bot

Local Windows helper for repetitive consent/settings dialogs.

This is a personal automation helper: it uses screenshots and template matching,
then clicks matching visible UI elements. It does not hook into a browser or
modify websites.

It learns from screenshots:

1. Select the screen area where the dialog appears.
2. Capture optional "skip if visible" templates.
3. Capture one or more button/toggle templates to click.
4. Run the profile and watch the counter overlay.

Emergency stop:

- Press `q` on an English layout or `й` on a Russian layout.
- Or move the mouse to the top-left screen corner.

## Install

```powershell
cd D:\Micro\screen_consent_bot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Use

Create or update a profile:

```powershell
.\.venv\Scripts\python.exe .\screen_consent_bot.py train cookie-cleaner
```

Run it:

```powershell
.\.venv\Scripts\python.exe .\screen_consent_bot.py run cookie-cleaner
```

Train and run immediately without thinking about profiles:

```powershell
.\.venv\Scripts\python.exe .\screen_consent_bot.py quick
```

Save that quick run as a normal profile:

```powershell
.\.venv\Scripts\python.exe .\screen_consent_bot.py quick --save-profile cookie-cleaner
```

Auto-scroll is enabled by default. If the bot does not find a click target for a few scans,
it scrolls inside the selected area.

Useful knobs:

```powershell
.\.venv\Scripts\python.exe .\screen_consent_bot.py run cookie-cleaner --scroll-after-misses 3 --scroll-amount -7
.\.venv\Scripts\python.exe .\screen_consent_bot.py run cookie-cleaner --no-scroll
```

In quick mode the script asks for scroll settings interactively.
For `--scroll-amount`, use a negative number to scroll down:

- `-3` = small step
- `-7` = medium step
- `-12` = big step

## GitHub Notes

The repository intentionally ignores:

- `.venv/`
- `__pycache__/`
- `profiles/`

`profiles/` is local because trained templates are screenshots/crops from your
screen and can contain private UI.
