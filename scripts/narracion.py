"""Genera la narración de public/plan-de-salvacion.html y la sincroniza.

Uso: python3 -I scripts/narracion.py <archivo-con-la-api-key>

Lee guion.json, pide a ElevenLabs cada escena con marcas de tiempo (los clips
quedan en clips/ y no se vuelven a cobrar mientras el texto no cambie) y
escribe los tiempos en el bloque NARRACION del HTML. Con musica.json compone
la música por secciones a la medida de las escenas (también se guarda en
clips/) y la mezcla bajo la voz en public/narracion.mp3.
Correrlo dos veces deja el mismo resultado.
"""

import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
HTML = ROOT / "public/index.html"
AUDIO = ROOT / "public/narracion.mp3"
CLIPS = HERE / "clips"
LEAD, TAIL, WORD_LEAD, LINE_TAIL = 0.4, 1.2, 0.3, 0.5
VOICE_LUFS = -16


def says(scene):
    return [p.get("say", p.get("line")) for p in scene["parts"]]


def spoken(scene):
    return "\n\n".join(says(scene))


def takes(scene):
    """Una toma por escena; con pausa, una por parte, para que el silencio sea real y no un corte."""
    n = len(scene["parts"])
    return [[k] for k in range(n)] if scene.get("pause") else [list(range(n))]


def clip(name, text, prev, nxt, guion, key):
    body = {"text": text, "model_id": guion["model"], "output_format": "mp3_44100_128",
            "previous_text": prev, "next_text": nxt}
    digest = hashlib.sha256(json.dumps([guion["voice"], body], ensure_ascii=False).encode()).hexdigest()[:10]
    base = CLIPS / f"{name}-{digest}"
    if not base.with_suffix(".json").exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{guion['voice']}/with-timestamps",
            data=json.dumps({k: v for k, v in body.items() if v}).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json"})
        data = json.load(urllib.request.urlopen(req))
        base.with_suffix(".mp3").write_bytes(base64.b64decode(data["audio_base64"]))
        base.with_suffix(".json").write_text(json.dumps({"text": text, "alignment": data["alignment"]}, ensure_ascii=False))
        print("generada", name, len(text), "caracteres")
    data = json.loads(base.with_suffix(".json").read_text())
    assert "".join(data["alignment"]["characters"]) == text, name
    return base.with_suffix(".mp3"), data["alignment"]


def lufs(path):
    out = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])


def lufs_range(path, ss, t):
    out = subprocess.run(["ffmpeg", "-nostats", "-ss", f"{ss}", "-t", f"{t}", "-i", str(path), "-af", "ebur128",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])


def music(durations, key):
    cfg = json.loads((HERE / "musica.json").read_text())
    covered = [scene for section in cfg["sections"] for scene in section["scenes"]]
    assert covered == list(durations), "musica.json debe cubrir todas las escenas en orden"
    total_ms, used, chunks = round(sum(durations.values()) * 1000), 0, []
    for k, section in enumerate(cfg["sections"]):
        ms = total_ms - used if k == len(cfg["sections"]) - 1 else round(sum(durations[s] for s in section["scenes"]) * 1000)
        used += ms
        chunks.append({"text": section["text"], "duration_ms": ms, "positive_styles": section["styles"],
                       "negative_styles": cfg["negative_styles"], "context_adherence": "high"})
    bounds = [0.0]
    for chunk in chunks:
        bounds.append(bounds[-1] + chunk["duration_ms"] / 1000)
    levels = [(lo, hi, section.get("level_db", 0)) for lo, hi, section in zip(bounds, bounds[1:], cfg["sections"])]
    body = {"composition_plan": {"chunks": chunks}, "model_id": cfg["model"]}
    path = CLIPS / f"musica-{hashlib.sha256(json.dumps(body).encode()).hexdigest()[:10]}.mp3"
    if not path.exists():
        req = urllib.request.Request("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128",
                                     data=json.dumps(body).encode(),
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
        path.write_bytes(urllib.request.urlopen(req, timeout=600).read())
        print("música generada", total_ms / 1000, "s")
    return path, cfg["duck_db"], levels


def gain_curve(points):
    """Expresión de ffmpeg para una curva de ganancia en dB, lineal entre puntos (t, dB)."""
    expr = f"{points[-1][1]:.2f}"
    for (t0, g0), (t1, g1) in reversed(list(zip(points, points[1:]))):
        expr = f"if(lt(t,{t1:.3f}),{g0:.2f}+({g1 - g0:.2f})*(t-{t0:.3f})/{max(t1 - t0, 0.001):.3f},{expr})"
    return f"pow(10,({expr})/20)"


def main():
    guion = json.loads((HERE / "guion.json").read_text())
    key = Path(sys.argv[1]).read_text().strip() if len(sys.argv) > 1 else ""
    html = HTML.read_text(encoding="utf-8")
    defaults = {m[0]: float(m[1]) for m in re.findall(r"\{ id: '(\w+)', name: '[^']*', dur: ([\d.]+) \}", html)}
    prayer = json.loads(re.search(r"const L = (\[\[.*?\]\]);", html).group(1))
    scenes = guion["scenes"]
    assert [s["id"] for s in scenes] == list(defaults), "guion.json y SCENES deben tener las mismas escenas"
    CLIPS.mkdir(exist_ok=True)
    sync = {"scenes": {}, "words": {}}
    start, inputs, filters = 0.0, [], []
    for i, scene in enumerate(scenes):
        before = spoken(scenes[i - 1]) if i else ""
        after = spoken(scenes[i + 1]) if i + 1 < len(scenes) else ""
        lines_said, pause = says(scene), scene.get("pause", 0)
        located, offset, scene_takes = {}, 0.0, takes(scene)
        for t, take in enumerate(scene_takes):
            text = "\n\n".join(lines_said[k] for k in take)
            prev = "\n\n".join([before] * (t == 0) + lines_said[:take[0]]) if len(scene_takes) > 1 else before
            nxt = "\n\n".join(lines_said[take[-1] + 1:] + [after] * (t == len(scene_takes) - 1)) if len(scene_takes) > 1 else after
            name = scene["id"] if len(scene_takes) == 1 else f"{scene['id']}-{t}"
            path, a = clip(name, text, prev.strip(), nxt.strip(), guion, key)
            inputs += ["-i", str(path)]
            ms = int((start + LEAD + offset) * 1000)
            filters.append(f"[{len(filters)}:a]adelay={ms}|{ms}[a{len(filters)}]")
            begin = [offset + x for x in a["character_start_times_seconds"]]
            end = [offset + x for x in a["character_end_times_seconds"]]
            pos = 0
            for k in take:
                at = text.index(lines_said[k], pos)
                located[k] = (at, text, begin, end)
                pos = at + len(lines_said[k])
            offset = end[-1] + pause
        marks, lines = {}, []
        for k, part in enumerate(scene["parts"]):
            at, text, begin, end = located[k]
            say = lines_said[k]
            if "mark" in part:
                marks[part["mark"]] = round(LEAD + begin[at], 3)
            else:
                line = part["line"]
                assert f">{line}<" in html, f"el texto no coincide con el HTML: {line}"
                lat, times = at, []
                for word in line.split():
                    lat = text.index(word.strip(",.;:"), lat)
                    times.append(round(LEAD + begin[lat], 3))
                    lat += len(word.strip(",.;:"))
                sync["words"][line] = times
                lines.append((times[0], LEAD + end[at + len(say) - 1]))
        end = located[len(scene["parts"]) - 1][3]
        default = defaults[scene["id"]]
        dur = round(max(default, LEAD + end[-1] + TAIL), 2)
        anchors = [[0, 0]]
        if scene["id"] == "oracion":
            for (first, last), (orig_in, orig_out) in zip(lines, prayer):
                anchors += [[round(first - WORD_LEAD, 3), orig_in], [round(last + LINE_TAIL, 3), orig_out]]
            assert all(a[0] < b[0] for a, b in zip(anchors, anchors[1:])), "líneas de la oración encimadas"
        anchors.append([dur, default])
        sync["scenes"][scene["id"]] = {"dur": dur, "anchors": anchors, "marks": marks}
        start += dur
    AUDIO.parent.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp())
    voice = work / "voz.wav"
    mix = ";".join(filters) + ";" + "".join(f"[a{i}]" for i in range(len(filters)))
    mix += f"amix=inputs={len(filters)}:normalize=0,apad=whole_dur={start}[out]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", mix, "-map", "[out]",
                    "-ac", "2", str(voice)], check=True)
    if (HERE / "musica.json").exists():
        track, duck_db, levels = music({s: d["dur"] for s, d in sync["scenes"].items()}, key)
        voice_gain = VOICE_LUFS - lufs(voice)
        target, ramp, points = VOICE_LUFS - duck_db, 0.75, []
        for lo, hi, level in levels:
            g = target + level - lufs_range(track, lo, hi - lo)
            points += [(lo + ramp if lo else 0.0, g), (hi - ramp, g)]
        points[-1] = (start, points[-1][1])
        mix = (f"[0:a]volume={voice_gain:.2f}dB,asplit=2[v][side];[1:a]volume='{gain_curve(points)}':eval=frame,afade=t=in:d=1.5,"
               f"afade=t=out:st={start - 3:.2f}:d=3[m];"
               "[m][side]sidechaincompress=threshold=0.02:ratio=3:attack=60:release=800[d];"
               "[v][d]amix=inputs=2:normalize=0,alimiter=limit=0.95,asetnsamples=n=1152:p=0[out]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(voice), "-i", str(track),
                        "-filter_complex", mix, "-map", "[out]", "-t", f"{start}", "-b:a", "128k", str(AUDIO)], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(voice), "-ac", "1", "-b:a", "96k",
                        "-af", "asetnsamples=n=1152:p=0", str(AUDIO)], check=True)
    sync["audio"] = f"{AUDIO.name}?v={hashlib.sha256(AUDIO.read_bytes()).hexdigest()[:10]}"
    block = "/* NARRACION:INICIO */\nconst SYNC = " + json.dumps(sync, ensure_ascii=False, separators=(",", ":")) + ";\n/* NARRACION:FIN */"
    html = re.sub(r"/\* NARRACION:INICIO \*/.*?/\* NARRACION:FIN \*/", lambda _: block, html, flags=re.S)
    HTML.write_text(html, encoding="utf-8")
    print(f"listo: {start:.1f} s, {sum(len(spoken(s)) for s in scenes)} caracteres en el guion")


main()
