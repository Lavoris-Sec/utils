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
cd D:\Micro\anticonsent_screen_bot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Use

Create or update a profile:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py train cookie-cleaner
```

Run it:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py run cookie-cleaner
```

Train and run immediately without thinking about profiles:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py quick
```

Save that quick run as a normal profile:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py quick --save-profile cookie-cleaner
```

Auto-scroll is enabled by default. If the bot does not find a click target for a few scans,
it scrolls inside the selected area.

Useful knobs:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py run cookie-cleaner --scroll-after-misses 3 --scroll-amount -7
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py run cookie-cleaner --no-scroll
```

In quick mode the script asks for scroll settings interactively.
For `--scroll-amount`, use a negative number to scroll down:

- `-70` = small step
- `-200` = medium step
- `-350` = big step

## GitHub Notes

The repository intentionally ignores:

- `.venv/`
- `__pycache__/`
- `profiles/`

`profiles/` is local because trained templates are screenshots/crops from your
screen and can contain private UI.

---

# Screen Consent Bot / Anti-Consent Screen Bot

Локальная Windows-утилита для повторяющихся окон согласий, настроек обработки
данных и похожих диалогов.

Это личный помощник для автоматизации: он делает скриншот, ищет на экране
заранее выделенный шаблон и кликает по найденному видимому элементу интерфейса.
Он не встраивается в браузер и не меняет сайты.

Как он обучается:

1. Выдели область экрана, где появляется диалог.
2. При желании выдели шаблоны "пропустить, если видно".
3. Выдели одну или несколько кнопок/переключателей, по которым нужно кликать.
4. Запусти профиль и смотри на счётчик в маленьком окне поверх экрана.

Аварийная остановка:

- Нажми `q` на английской раскладке или `й` на русской.
- Или уведи мышь в левый верхний угол экрана.

## Установка

```powershell
cd D:\Micro\anticonsent_screen_bot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Использование

Создать или обновить профиль:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py train cookie-cleaner
```

Запустить сохранённый профиль:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py run cookie-cleaner
```

Быстрый режим без ручной работы с профилями:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py quick
```

Быстрый режим с сохранением как обычный профиль:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py quick --save-profile cookie-cleaner
```

Автопрокрутка включена по умолчанию. Если бот несколько проверок подряд не
находит цель для клика, он прокручивает выбранную область.

Полезные настройки:

```powershell
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py run cookie-cleaner --scroll-after-misses 3 --scroll-amount -7
.\.venv\Scripts\python.exe .\anticonsent_screen_bot.py run cookie-cleaner --no-scroll
```

В quick-режиме скрипт спрашивает настройки прокрутки интерактивно.
Для `--scroll-amount` используй отрицательное число, чтобы скроллить вниз:

- `-70` = маленький шаг
- `-200` = средний шаг
- `-350` = большой шаг

## Заметки для GitHub

Репозиторий специально игнорирует:

- `.venv/`
- `__pycache__/`
- `profiles/`

`profiles/` остаётся локальной папкой, потому что обученные шаблоны являются
скриншотами/фрагментами твоего экрана и могут содержать приватный интерфейс.
