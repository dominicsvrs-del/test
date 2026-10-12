# Schnittplatz

Ein Videoeditor, der komplett im Browser läuft: Schnitt, Untertitel, Motion Design und Export. Es gibt keinen Server und keinen Upload, deine Videos bleiben auf deinem Rechner.

## Starten

`index.html` im Browser öffnen (Chrome oder Edge empfohlen, Firefox geht auch). Fertig.

## Funktionen

**Schnitt & Look**
- Video öffnen oder per Drag & Drop in die Vorschau ziehen
- In- und Out-Punkt setzen (Tasten `I` / `O`, oder Clip-Kanten in der Zeitleiste ziehen)
- Tempo von 0,25× bis 2×
- Formate 16:9, 9:16 (Reels/TikTok/Shorts), 1:1, 4:5 oder Original
- Einpassen: Füllen, mit Balken, oder mit unscharfem Hintergrund (für Querformat in 9:16)
- Color Grading mit Presets (Warm, Kühl, Kino, Vintage, Noir, Punch) und Reglern für Helligkeit, Kontrast, Sättigung, Farbton, Sepia, Schwarzweiß, Vignette und Weichzeichner
- Ohne Video: leere Komposition mit animiertem Farbverlauf für Intros und Motion-Grafiken

**Untertitel**
- Stil-Presets: Reels Karaoke, Wort für Wort, Klassisch, Doku, Pop-In
- Animationen: Karaoke (aktives Wort hervorgehoben), Wort für Wort, Pop-In, Einblenden
- Schrift, Größe, Farben, Kontur, Hintergrundbox, Großbuchstaben, Position (auch per Ziehen in der Vorschau)
- SRT/VTT importieren und exportieren
- Transkript einfügen und automatisch auf den Clip verteilen
- Alle Untertitel gemeinsam zeitlich verschieben

**Motion Design**
- Ebenen: Titel, Bauchbinde, Badge, Zähler (animierte Zahl), Kreis-Highlight, Fortschrittsbalken
- Animationen rein und raus: Einblenden, Slide, Pop, Zoom, Unschärfe, Schreibmaschine, Wischen
- Ebenen in der Vorschau verschieben, in der Zeitleiste verschieben und trimmen, duplizieren, Reihenfolge ändern

**Export**
- Rendert In bis Out als MP4 (wenn der Browser es kann) oder WebM, mit Ton, in 1080p, 720p oder 540p
- Standbild als PNG, Untertitel als SRT/VTT, Projekt als JSON speichern und wieder laden
- Das Projekt wird automatisch im Browser zwischengespeichert (das Video selbst nicht)

## Tastenkürzel

| Taste | Aktion |
|---|---|
| Leertaste | Abspielen / Pause |
| ← / → | 1 Frame zurück / vor (mit Shift: 1 Sekunde) |
| I / O | In- / Out-Punkt setzen |
| N | Untertitel am Playhead einfügen |
| D | Ausgewählte Ebene duplizieren |
| Entf | Auswahl löschen |
| Pos1 / Ende | Zum In- / Out-Punkt |

## Grenzen

- Der Export läuft in Echtzeit (ein 60-Sekunden-Clip braucht etwa 60 Sekunden). Den Tab währenddessen offen lassen.
- Ein Video pro Projekt, kein Mehrspur-Schnitt.
- Untertitel werden nicht automatisch aus der Sprache erkannt. Transkript einfügen und verteilen lassen, dann in der Zeitleiste feinjustieren.
