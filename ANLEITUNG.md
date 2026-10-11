# Twitch Clipper – Anleitung

Das Skript lädt ein Twitch-VOD (z. B. von **trymacs**), findet automatisch die
**20 besten Momente** und schneidet sie zu Clips von **1:00–1:50 Minuten**.

Die besten Momente erkennt es an:
- **Chat-Spitzen**: plötzlich viele Nachrichten, besonders mit KEKW, LUL, Pog, W, 😂 usw.
- **Lautstärke**: Schreien, Lachen, Hype

Es lädt **nicht** den ganzen Stream in Videoqualität herunter, sondern nur die Tonspur
(zur Analyse) und danach gezielt die 20 Ausschnitte.

---

## 1. Einmalig installieren

### Windows
1. **Python** installieren: https://www.python.org/downloads/
   → Beim Installieren unbedingt den Haken **„Add python.exe to PATH“** setzen!
2. **Eingabeaufforderung** öffnen (Windows-Taste, `cmd` tippen, Enter) und eingeben:
   ```
   winget install Gyan.FFmpeg
   pip install -U yt-dlp chat-downloader
   ```
3. Eingabeaufforderung schließen und neu öffnen (damit ffmpeg gefunden wird).

### Mac
1. **Terminal** öffnen und Homebrew installieren (falls noch nicht da): https://brew.sh
2. Dann:
   ```
   brew install python ffmpeg
   pip3 install -U yt-dlp chat-downloader
   ```

## 2. Dateien herunterladen
Lade `twitch_clipper.py` (und unter Windows `clips_erstellen.bat`) aus diesem
Repository herunter und lege sie zusammen in einen Ordner, z. B. `Desktop\clips`.

## 3. Starten

**Windows (einfach):** Doppelklick auf `clips_erstellen.bat`, Link einfügen, Enter.

**Oder per Befehl** (im Ordner mit dem Skript):
```
python twitch_clipper.py https://www.twitch.tv/trymacs
```
(Mac: `python3` statt `python`)

- Ein **Kanal-Link** nimmt automatisch das **neueste VOD**.
- Ein **VOD-Link** (`https://www.twitch.tv/videos/2896816435`) nimmt genau dieses Video.

Die Clips landen im Ordner `clips`, dazu eine `uebersicht.csv` mit Zeitstempeln
und den häufigsten Chat-Wörtern pro Clip (öffnet sich in Excel).

## Optionen

| Option | Bedeutung |
|---|---|
| `--hochkant` | 9:16 für TikTok / Shorts / Reels (unscharfer Hintergrund) |
| `--anzahl 30` | andere Anzahl Clips (Standard 20) |
| `--min 60 --max 110` | Clip-Länge in Sekunden (Standard 60–110) |
| `--qualitaet 720` | kleinere Dateien (Standard 1080) |
| `--nur-analyse` | nur Zeitstempel finden, nichts schneiden |
| `--ordner name` | anderer Ausgabeordner |

Beispiel hochkant:
```
python twitch_clipper.py https://www.twitch.tv/trymacs --hochkant
```

## Häufige Probleme
- **„python“ wird nicht erkannt** → Python neu installieren, Haken „Add to PATH“ setzen.
- **„ffmpeg“ nicht gefunden** → Eingabeaufforderung neu öffnen; sonst PC neu starten.
- **Chat lädt nicht** → Das Skript macht dann nur mit der Lautstärke weiter
  (etwas ungenauer). `pip install -U chat-downloader` hilft oft.
- **Download-Fehler** → `pip install -U yt-dlp` (Twitch ändert öfter etwas).
- Ein Stream, der **gerade live** ist, hat noch kein fertiges VOD → nach dem Stream starten.

## Wichtig: Rechte
Die Inhalte gehören dem Streamer. Wer Clips z. B. auf TikTok/YouTube hochladen
will, sollte vorher die Erlaubnis haben (viele Streamer haben Clipper-Regeln).
