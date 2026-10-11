#!/usr/bin/env python3
"""
Twitch Clipper – findet automatisch die besten Momente eines Twitch-VODs
und schneidet sie zu Clips (Standard: 20 Clips, je 1:00–1:50).

Wie die besten Momente gefunden werden:
  * Chat: plötzliche Spitzen in der Nachrichtenrate + Lach-/Hype-Emotes
  * Audio: laute Stellen (Schreien, Lachen, Hype)

Beispiele:
  python twitch_clipper.py https://www.twitch.tv/trymacs
  python twitch_clipper.py https://www.twitch.tv/videos/2896816435
  python twitch_clipper.py https://www.twitch.tv/trymacs --hochkant
"""

import argparse
import bisect
import csv
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter

LAUGH_HYPE = {
    "kekw", "lul", "lol", "omegalul", "lmao", "xd", "xdd", "haha", "hahaha",
    "pog", "pogchamp", "poggers", "pogu", "w", "ww", "www", "monkas", "omg",
    "wtf", "lulw", "icant", "aware", "kappa", "pepelaugh", "sadge", "ez",
    "clip", "clipit", "😂", "🤣", "💀",
}
CHAT_DELAY = 6  # Chat reagiert ein paar Sekunden nach dem eigentlichen Moment


def log(msg):
    print(msg, flush=True)


def need(tool):
    if shutil.which(tool) is None:
        sys.exit(f"FEHLER: '{tool}' wurde nicht gefunden. Siehe Anleitung in ANLEITUNG.md.")


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def ytdlp_cmd():
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    return [sys.executable, "-m", "yt_dlp"]


def fmt_time(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


# ---------------------------------------------------------------- VOD finden

def resolve_vod(url):
    """Kanal-Link -> neuestes VOD. VOD-Link bleibt unverändert."""
    if "/videos/" in url:
        return url
    channel = url.rstrip("/").split("/")[-1]
    log(f"Suche das neueste VOD von '{channel}' ...")
    out = subprocess.run(
        ytdlp_cmd() + ["--flat-playlist", "--playlist-end", "1", "-J",
                       f"https://www.twitch.tv/{channel}/videos?filter=archives&sort=time"],
        capture_output=True, text=True)
    try:
        entries = json.loads(out.stdout)["entries"]
        vod = entries[0].get("url") or f"https://www.twitch.tv/videos/{entries[0]['id']}"
    except Exception:
        sys.exit("FEHLER: Kein VOD gefunden. Speichert der Kanal seine Streams? "
                 "Du kannst auch direkt einen Link wie https://www.twitch.tv/videos/123 angeben.\n"
                 + out.stderr[-1500:])
    if not vod.startswith("http"):
        vod = f"https://www.twitch.tv/videos/{vod.lstrip('v')}"
    log(f"Neuestes VOD: {vod}")
    return vod


def vod_duration(vod_url):
    out = subprocess.run(ytdlp_cmd() + ["--skip-download", "-J", vod_url],
                         capture_output=True, text=True)
    try:
        info = json.loads(out.stdout)
        return float(info.get("duration") or 0), info.get("title") or ""
    except Exception:
        sys.exit("FEHLER: VOD-Infos konnten nicht geladen werden.\n" + out.stderr[-1500:])


# ---------------------------------------------------------------- Chat

def load_chat(vod_url, cache):
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            return json.load(f)
    try:
        from chat_downloader import ChatDownloader
    except ImportError:
        log("Hinweis: 'chat-downloader' nicht installiert – nutze nur Audio.")
        return []
    log("Lade Chat herunter (kann bei langen Streams einige Minuten dauern) ...")
    msgs = []
    try:
        for i, m in enumerate(ChatDownloader().get_chat(vod_url)):
            t = m.get("time_in_seconds")
            if t is None:
                continue
            msgs.append([float(t), m.get("message") or ""])
            if i % 5000 == 0 and i:
                log(f"  {i} Nachrichten ... (bei {fmt_time(t)})")
    except Exception as e:
        log(f"Hinweis: Chat konnte nicht (vollständig) geladen werden ({e}). "
            "Mache mit dem weiter, was da ist.")
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(msgs, f)
    log(f"Chat: {len(msgs)} Nachrichten")
    return msgs


def chat_scores(msgs, n):
    """Pro Sekunde: Nachrichten + Bonus für Lach-/Hype-Emotes."""
    s = [0.0] * n
    for t, text in msgs:
        i = int(t) - CHAT_DELAY
        if 0 <= i < n:
            words = re.findall(r"\w+|[😂🤣💀]", text.lower())
            bonus = sum(1 for w in words if w in LAUGH_HYPE)
            s[i] += 1 + min(bonus, 3) * 0.7
    return s


# ---------------------------------------------------------------- Audio

def download_audio(vod_url, path):
    if os.path.exists(path):
        return path
    log("Lade nur die Tonspur zur Analyse herunter ...")
    base = os.path.splitext(path)[0]
    try:
        run(ytdlp_cmd() + ["-f", "audio_only/bestaudio/worst", "-x", "--audio-format", "m4a",
                           "-o", base + ".%(ext)s", vod_url])
    except subprocess.CalledProcessError:
        log("Hinweis: Tonspur konnte nicht geladen werden – nutze nur Chat.")
        return None
    return path if os.path.exists(path) else None


def audio_loudness(audio_path, n):
    """RMS-Lautstärke (dB) pro Sekunde über ffmpeg."""
    log("Analysiere Lautstärke ...")
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", audio_path, "-vn",
         "-af", "aresample=8000,asetnsamples=8000,astats=metadata=1:reset=1,"
                "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
         "-f", "null", "-"],
        capture_output=True, text=True)
    vals, t = [-90.0] * n, None
    for line in proc.stdout.splitlines():
        if line.startswith("frame:"):
            m = re.search(r"pts_time:([\d.]+)", line)
            t = int(float(m.group(1))) if m else None
        elif "RMS_level=" in line and t is not None and 0 <= t < n:
            v = line.split("=", 1)[1]
            vals[t] = -90.0 if v in ("-inf", "inf", "nan") else max(float(v), -90.0)
    return vals


# ---------------------------------------------------------------- Bewertung

def smooth(x, w):
    out, acc, half = [0.0] * len(x), 0.0, w // 2
    pref = [0.0]
    for v in x:
        acc += v
        pref.append(acc)
    for i in range(len(x)):
        a, b = max(0, i - half), min(len(x), i + half + 1)
        out[i] = (pref[b] - pref[a]) / (b - a)
    return out


def local_z(x, window=600, step=30):
    """Wie stark ragt eine Stelle über ihre Umgebung (±5 min) heraus?"""
    n = len(x)
    if n == 0:
        return []
    med, spread = [0.0] * n, [1.0] * n
    for c in range(0, n, step):
        seg = x[max(0, c - window // 2):min(n, c + window // 2)]
        m = statistics.median(seg)
        q = sorted(seg)
        iqr = q[int(len(q) * 0.75)] - q[int(len(q) * 0.25)]
        for i in range(c, min(n, c + step)):
            med[i], spread[i] = m, max(iqr, 1e-6)
    return [(x[i] - med[i]) / spread[i] for i in range(n)]


def combined_score(chat, audio, n):
    parts = []
    if chat and sum(chat) > 0:
        parts.append((1.0, local_z(smooth(chat, 10))))
    if audio:
        parts.append((0.6 if parts else 1.0, local_z(smooth(audio, 5))))
    if not parts:
        sys.exit("FEHLER: Weder Chat noch Audio verfügbar – nichts zu analysieren.")
    total = sum(w for w, _ in parts)
    return [sum(w * p[i] for w, p in parts) / total for i in range(n)]


def pick_clips(score, n, count, min_len, max_len, skip_start, skip_end):
    smoothed = smooth(score, 15)
    order = sorted(range(n), key=lambda i: smoothed[i], reverse=True)
    taken, clips = [], []
    lo, hi = skip_start, n - skip_end
    for peak in order:
        if len(clips) >= count:
            break
        if not (lo <= peak < hi):
            continue
        # Bereich um den Peak, solange es "heiß" bleibt
        thr = smoothed[peak] * 0.5
        a = peak
        while a > lo and peak - a < 90 and smoothed[a - 1] > thr:
            a -= 1
        b = peak
        while b < hi - 1 and b - peak < 60 and smoothed[b + 1] > thr:
            b += 1
        # Vorlauf für Kontext, kurzer Nachlauf
        start, end = a - 45, b + 20
        length = end - start
        if length < min_len:
            extra = min_len - length
            start -= int(extra * 0.7)
            end += extra - int(extra * 0.7)
        elif length > max_len:
            start = max(start, peak - int(max_len * 0.65))
            end = start + max_len
        start, end = max(0, start), min(n, end)
        if end - start < min_len:
            continue
        i = bisect.bisect_left(taken, (start,))
        overlap = any(not (end + 10 <= s or start >= e + 10)
                      for s, e in taken[max(0, i - 1):i + 1])
        if overlap:
            continue
        bisect.insort(taken, (start, end))
        clips.append({"start": start, "end": end, "peak": peak, "score": smoothed[peak]})
    return clips


def top_words(msgs, start, end, k=5):
    c = Counter()
    for t, text in msgs:
        if start <= t - CHAT_DELAY < end:
            c.update(w for w in re.findall(r"\w+", text.lower()) if len(w) > 1)
    return " ".join(w for w, _ in c.most_common(k))


# ---------------------------------------------------------------- Schneiden

VERTICAL = ("split[a][b];"
            "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
            "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")


def encode(src, dst, start=None, duration=None, vertical=False):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", src]
    if duration is not None:
        cmd += ["-t", str(duration)]
    if vertical:
        cmd += ["-vf", VERTICAL]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", dst]
    run(cmd)


def cut_from_twitch(vod_url, clip, dst, quality, vertical):
    tmp = dst + ".part.mp4"
    run(ytdlp_cmd() + [
        "-f", f"best[height<={quality}]/best",
        "--download-sections", f"*{clip['start']}-{clip['end']}",
        "--force-keyframes-at-cuts", "-o", tmp, "--force-overwrites", vod_url])
    encode(tmp, dst, vertical=vertical)
    os.remove(tmp)


# ---------------------------------------------------------------- Main

def main():
    p = argparse.ArgumentParser(description="Schneidet die besten Momente aus einem Twitch-VOD.")
    p.add_argument("url", nargs="?", help="Twitch-Kanal oder VOD-Link")
    p.add_argument("--anzahl", type=int, default=20, help="Anzahl Clips (Standard 20)")
    p.add_argument("--min", type=int, default=60, help="Mindestlänge in Sekunden (Standard 60)")
    p.add_argument("--max", type=int, default=110, help="Maximallänge in Sekunden (Standard 110)")
    p.add_argument("--hochkant", action="store_true", help="9:16 für TikTok/Shorts/Reels")
    p.add_argument("--qualitaet", type=int, default=1080, help="Max. Auflösung (Standard 1080)")
    p.add_argument("--ordner", default="clips", help="Ausgabeordner (Standard: clips)")
    p.add_argument("--nur-analyse", action="store_true", help="Nur Zeitstempel finden, nicht schneiden")
    p.add_argument("--video", help="Lokale Videodatei statt Twitch (zum Testen)")
    p.add_argument("--chat-json", help="Lokale Chat-Datei [[sekunde, text], ...] (zum Testen)")
    a = p.parse_args()

    if not a.url and not a.video:
        a.url = input("Twitch-Link (Kanal oder VOD): ").strip()

    need("ffmpeg")
    os.makedirs(a.ordner, exist_ok=True)

    if a.video:
        vod_url, title = None, os.path.basename(a.video)
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video],
            capture_output=True, text=True).stdout.strip())
        tag = "lokal"
        audio_path = a.video
    else:
        vod_url = resolve_vod(a.url)
        dur, title = vod_duration(vod_url)
        tag = vod_url.rstrip("/").split("/")[-1]
        audio_path = download_audio(vod_url, os.path.join(a.ordner, f"_audio_{tag}.m4a"))
    n = int(dur)
    log(f"Video: {title} ({fmt_time(n)})")
    if n < a.min * 2:
        sys.exit("FEHLER: Video ist zu kurz.")

    if a.chat_json:
        with open(a.chat_json, encoding="utf-8") as f:
            msgs = json.load(f)
    elif vod_url:
        msgs = load_chat(vod_url, os.path.join(a.ordner, f"_chat_{tag}.json"))
    else:
        msgs = []

    chat = chat_scores(msgs, n) if msgs else []
    audio = audio_loudness(audio_path, n) if audio_path else []
    score = combined_score(chat, audio, n)

    skip = min(300, n // 20)  # Intro/Outro ("Starting soon", Verabschiedung) überspringen
    clips = pick_clips(score, n, a.anzahl, a.min, a.max, skip, skip)
    if not clips:
        sys.exit("FEHLER: Keine passenden Momente gefunden.")
    log(f"\n{len(clips)} Momente gefunden (nach Stärke sortiert):")

    rows = []
    for rank, c in enumerate(clips, 1):
        name = f"clip_{rank:02d}_{fmt_time(c['start']).replace(':', '-')}.mp4"
        words = top_words(msgs, c["start"], c["end"]) if msgs else ""
        rows.append([rank, name, fmt_time(c["start"]), fmt_time(c["end"]),
                     f"{(c['end'] - c['start']) // 60}:{(c['end'] - c['start']) % 60:02d}",
                     round(c["score"], 2), words])
        log(f"  #{rank:2d}  {fmt_time(c['start'])} – {fmt_time(c['end'])}  "
            f"({rows[-1][4]})  Chat: {words}")

    with open(os.path.join(a.ordner, "uebersicht.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Rang", "Datei", "Start", "Ende", "Länge", "Score", "Häufigste Chat-Wörter"])
        w.writerows(rows)

    if a.nur_analyse:
        log(f"\nÜbersicht gespeichert: {os.path.join(a.ordner, 'uebersicht.csv')}")
        return

    for row, c in zip(rows, clips):
        dst = os.path.join(a.ordner, row[1])
        log(f"\nSchneide #{row[0]} ({row[2]} – {row[3]}) ...")
        try:
            if a.video:
                encode(a.video, dst, c["start"], c["end"] - c["start"], a.hochkant)
            else:
                cut_from_twitch(vod_url, c, dst, a.qualitaet, a.hochkant)
        except subprocess.CalledProcessError as e:
            log(f"  Fehler bei #{row[0]}: {e} – überspringe.")

    log(f"\nFertig! Clips liegen im Ordner '{os.path.abspath(a.ordner)}'.")


if __name__ == "__main__":
    main()
