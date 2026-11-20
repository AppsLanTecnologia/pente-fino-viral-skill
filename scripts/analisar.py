#!/usr/bin/env python3
"""Pente fino viral: baixa um Reel/TikTok/Short e extrai tudo o que dá para medir.

Uso:
    python3 analisar.py <link-ou-arquivo.mp4> [--saida PASTA] [--modelo base] [--idioma pt] [--sem-transcricao]

Gera, dentro da pasta da análise:
    video.mp4            o vídeo
    info.json            metadados do yt-dlp (quando veio de link)
    gancho/g_0.0.jpg...  quadros dos primeiros 3 s, a cada 0,5 s
    cenas/c_01.jpg...    um quadro do meio de cada plano (corte a corte)
    folhas/folha_1.jpg   folhas de contato, 1 quadro por segundo, 6 colunas x 5 linhas (30 s por folha)
    transcricao/         saída do Whisper (texto com tempo por palavra)
    dados.json           tudo em números
    resumo.md            leitura rápida para a análise

Só usa a biblioteca padrão do Python. Precisa de: ffmpeg, ffprobe, yt-dlp (para links), whisper (opcional).
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys

CORTE_LIMIAR = 0.28  # sensibilidade da detecção de corte (0 a 1; menor pega mais cortes)


def rodar(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def precisa(binario, dica):
    if not shutil.which(binario):
        sys.exit(f"Falta o programa '{binario}'. {dica}")


def baixar(link, pasta):
    precisa("yt-dlp", "Instale com: pip install yt-dlp")
    saida = os.path.join(pasta, "video.%(ext)s")
    r = rodar(["yt-dlp", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
               "--write-info-json", "--no-playlist", "-o", saida, link])
    if r.returncode != 0:
        sys.exit("Não consegui baixar o vídeo.\n" + r.stderr[-1500:] +
                 "\nSe o post for privado ou o Instagram pedir login, baixe o vídeo você mesmo e rode de novo passando o arquivo .mp4.")
    info = os.path.join(pasta, "video.info.json")
    if os.path.exists(info):
        os.replace(info, os.path.join(pasta, "info.json"))
    for nome in os.listdir(pasta):
        if nome.startswith("video.") and nome.endswith(".mp4"):
            return os.path.join(pasta, nome)
    sys.exit("O download terminou, mas não achei o arquivo .mp4.")


def sondar(video):
    r = rodar(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    num, den = (v.get("avg_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = round(float(num) / float(den), 2) if float(den) else 0
    return {
        "duracao_s": round(float(d["format"].get("duration", 0)), 2),
        "largura": v.get("width"), "altura": v.get("height"), "fps": fps,
        "tem_audio": a is not None,
    }


def cortes(video, duracao):
    """Mede a mudança entre quadros e marca corte onde ela salta.

    O limiar se adapta ao vídeo: animação em fundo fixo muda pouco entre cenas,
    vídeo de câmera muda muito. Usa CORTE_LIMIAR ou o pico estatístico, o que for menor.
    """
    r = rodar(["ffmpeg", "-hide_banner", "-i", video, "-vf",
               "scale=270:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score", "-an", "-f", "null", "-"])
    tempos = [float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    notas = [float(n) for n in re.findall(r"lavfi.scene_score=([\d.]+)", r.stderr)]
    pares = list(zip(tempos, notas))
    if not pares:
        return [{"n": 1, "inicio": 0.0, "fim": duracao, "duracao": duracao}], CORTE_LIMIAR
    media = sum(notas) / len(notas)
    desvio = (sum((n - media) ** 2 for n in notas) / len(notas)) ** 0.5
    limiar = round(max(0.05, min(CORTE_LIMIAR, media + 5 * desvio)), 3)
    limpos = []
    for t, n in pares:  # junta cortes a menos de 0,25 s um do outro (flash, transição)
        if n >= limiar and t > 0.2:
            if limpos and t - limpos[-1] <= 0.25:
                continue
            limpos.append(round(t, 2))
    bordas = [0.0] + limpos + [duracao]
    planos = [{"n": i + 1, "inicio": bordas[i], "fim": bordas[i + 1],
               "duracao": round(bordas[i + 1] - bordas[i], 2)} for i in range(len(bordas) - 1)]
    return planos, limiar


def quadro(video, t, destino, largura=540):
    rodar(["ffmpeg", "-hide_banner", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
           "-vf", f"scale={largura}:-2", "-q:v", "3", destino])


def quadros(video, info_v, planos, pasta):
    os.makedirs(os.path.join(pasta, "gancho"), exist_ok=True)
    os.makedirs(os.path.join(pasta, "cenas"), exist_ok=True)
    os.makedirs(os.path.join(pasta, "folhas"), exist_ok=True)
    t = 0.0
    while t <= min(3.0, info_v["duracao_s"] - 0.05):
        quadro(video, t, os.path.join(pasta, "gancho", f"g_{t:.1f}.jpg"))
        t += 0.5
    for p in planos:
        meio = p["inicio"] + p["duracao"] / 2
        quadro(video, meio, os.path.join(pasta, "cenas", f"c_{p['n']:02d}.jpg"), 360)
    rodar(["ffmpeg", "-hide_banner", "-y", "-i", video, "-vf", "fps=1,scale=200:-2,tile=6x5:padding=4:color=black",
           "-q:v", "3", os.path.join(pasta, "folhas", "folha_%d.jpg")])


def audio(video, pasta):
    wav = os.path.join(pasta, "audio.wav")
    rodar(["ffmpeg", "-hide_banner", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav])
    r = rodar(["ffmpeg", "-hide_banner", "-i", video, "-vn", "-af", "ebur128=peak=true,silencedetect=n=-35dB:d=0.35",
               "-f", "null", "-"])
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    pico = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    silencios = []
    for ini, fim in zip(re.findall(r"silence_start: ([\d.]+)", r.stderr),
                        re.findall(r"silence_end: ([\d.]+)", r.stderr)):
        silencios.append({"inicio": round(float(ini), 2), "fim": round(float(fim), 2)})
    return wav, {"lufs": float(lufs[-1]) if lufs else None,
                 "pico_dbfs": float(pico[-1]) if pico else None,
                 "silencios": silencios}


def transcrever(wav, pasta, modelo, idioma):
    if not shutil.which("whisper"):
        return None, "whisper não instalado (pip install openai-whisper); transcrição pulada"
    destino = os.path.join(pasta, "transcricao")
    os.makedirs(destino, exist_ok=True)
    cmd = ["whisper", wav, "--model", modelo, "--word_timestamps", "True",
           "--output_format", "json", "--output_dir", destino, "--fp16", "False"]
    if idioma:
        cmd += ["--language", idioma]
    r = rodar(cmd)
    arq = os.path.join(destino, "audio.json")
    if not os.path.exists(arq):
        return None, "o Whisper falhou: " + r.stderr[-500:]
    d = json.load(open(arq))
    palavras = []
    for seg in d.get("segments", []):
        for w in seg.get("words", []):
            palavras.append({"p": w["word"].strip(), "i": round(w["start"], 2), "f": round(w["end"], 2)})
    return {"idioma": d.get("language"), "texto": d.get("text", "").strip(), "palavras": palavras}, None


def metricas(info_path):
    if not os.path.exists(info_path):
        return {}
    i = json.load(open(info_path))
    m = {k: i.get(k) for k in ("uploader", "channel", "upload_date", "view_count", "like_count",
                               "comment_count", "repost_count", "duration", "track", "artist", "webpage_url")}
    m["legenda"] = i.get("description") or ""
    m["hashtags"] = re.findall(r"#\w+", m["legenda"])
    if m.get("upload_date"):
        d = dt.datetime.strptime(m["upload_date"], "%Y%m%d").date()
        m["dias_no_ar"] = max(1, (dt.date.today() - d).days)
        m["upload_date"] = d.strftime("%d/%m/%Y")
        for k in ("view_count", "like_count", "comment_count"):
            if m.get(k):
                m[k.replace("_count", "") + "_por_dia"] = round(m[k] / m["dias_no_ar"])
    if m.get("like_count") and m.get("comment_count"):
        m["comentarios_por_curtida"] = round(m["comment_count"] / m["like_count"], 2)
    if m.get("view_count") and m.get("like_count"):
        m["curtidas_por_100_views"] = round(100 * m["like_count"] / m["view_count"], 2)
    return m


def fmt(n):
    return "—" if n is None else (f"{n:,}".replace(",", ".") if isinstance(n, int) else str(n))


def resumo(pasta, v, planos, au, tr, m, aviso_tr):
    dur = v["duracao_s"] or 1
    L = [f"# Dados brutos do vídeo", "", "## Ficha"]
    L += [f"- Autor: {m.get('uploader') or m.get('channel') or '—'} · publicado em {m.get('upload_date') or '—'}"
          f" ({m.get('dias_no_ar', '—')} dias no ar)",
          f"- Visualizações: {fmt(m.get('view_count'))} · curtidas: {fmt(m.get('like_count'))} · comentários: {fmt(m.get('comment_count'))}",
          f"- Comentários por curtida: {m.get('comentarios_por_curtida', '—')} · curtidas a cada 100 views: {m.get('curtidas_por_100_views', '—')}",
          f"- Música: {m.get('track') or '—'} {('· ' + m['artist']) if m.get('artist') else ''}",
          f"- Formato: {v['largura']}x{v['altura']}, {v['fps']} fps, {dur} s",
          "", "## Ritmo",
          f"- Planos (cortes detectados): {len(planos)} · duração média do plano: {round(dur / len(planos), 2)} s"
          f" · cortes por minuto: {round(60 * (len(planos) - 1) / dur, 1)} (limiar {v.get('limiar_corte')}; confira nas folhas)",
          f"- Áudio: {au['lufs']} LUFS integrado, pico {au['pico_dbfs']} dBFS, {len(au['silencios'])} silêncios ≥ 0,35 s"]
    if tr:
        pal = tr["palavras"]
        falado = sum(p["f"] - p["i"] for p in pal)
        L += [f"- Fala: {len(pal)} palavras · {round(len(pal) / dur, 2)} palavras/s no vídeo todo",
              f"- Primeira palavra em {pal[0]['i'] if pal else '—'} s · tempo com voz: {round(100 * falado / dur)}%"]
        tres = " ".join(p["p"] for p in pal if p["i"] < 3.0)
        L += ["", "## Gancho (0–3 s)", f"- Falado: \"{tres}\"",
              "- Quadros: pasta `gancho/` (0,0 s a 3,0 s, a cada 0,5 s)"]
    else:
        L += [f"- Transcrição: {aviso_tr}"]
    L += ["", "## Plano a plano", "| # | Início | Fim | Dur. | Fala neste plano | Quadro |", "|---|---|---|---|---|---|"]
    for p in planos:
        fala = ""
        if tr:
            fala = " ".join(w["p"] for w in tr["palavras"] if p["inicio"] <= w["i"] < p["fim"])
        L.append(f"| {p['n']} | {p['inicio']} | {p['fim']} | {p['duracao']} | {fala} | cenas/c_{p['n']:02d}.jpg |")
    if m.get("legenda"):
        L += ["", "## Legenda do post", "", m["legenda"]]
    L += ["", "## Folhas de contato", "`folhas/folha_N.jpg`: 1 quadro por segundo, 6 por linha, 30 s por folha "
          "(a célula k da folha N mostra o segundo 30·(N−1)+k−1)."]
    open(os.path.join(pasta, "resumo.md"), "w").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fonte", help="link do Reel/TikTok/Short ou caminho de um .mp4")
    ap.add_argument("--saida", default="analises", help="pasta onde criar a análise (padrão: ./analises)")
    ap.add_argument("--modelo", default="base", help="modelo do Whisper (tiny, base, small)")
    ap.add_argument("--idioma", default=None, help="idioma da fala (pt, en, es); vazio detecta sozinho")
    ap.add_argument("--sem-transcricao", action="store_true")
    a = ap.parse_args()
    precisa("ffmpeg", "Instale o FFmpeg (https://ffmpeg.org).")

    eh_link = re.match(r"https?://", a.fonte)
    ident = re.sub(r"[^\w-]", "", (re.search(r"/(?:reel|p|video|shorts)/([\w-]+)", a.fonte) or [None, None])[1]
                   or os.path.splitext(os.path.basename(a.fonte))[0])[:40] or "video"
    pasta = os.path.abspath(os.path.join(a.saida, f"{dt.date.today():%Y-%m-%d}-{ident}"))
    os.makedirs(pasta, exist_ok=True)
    print("Pasta da análise:", pasta)

    if eh_link:
        print("Baixando…")
        video = baixar(a.fonte, pasta)
    else:
        video = os.path.join(pasta, "video.mp4")
        if os.path.abspath(a.fonte) != video:
            shutil.copy(a.fonte, video)
        vizinho = os.path.join(os.path.dirname(os.path.abspath(a.fonte)), "info.json")
        if os.path.exists(vizinho) and not os.path.exists(os.path.join(pasta, "info.json")):
            shutil.copy(vizinho, os.path.join(pasta, "info.json"))

    v = sondar(video)
    print("Detectando cortes…")
    planos, limiar = cortes(video, v["duracao_s"])
    v["limiar_corte"] = limiar
    print(f"{len(planos)} planos. Extraindo quadros…")
    quadros(video, v, planos, pasta)
    au, tr, aviso = {"lufs": None, "pico_dbfs": None, "silencios": []}, None, "vídeo sem áudio"
    if v["tem_audio"]:
        print("Medindo o áudio…")
        wav, au = audio(video, pasta)
        if not a.sem_transcricao:
            print("Transcrevendo (pode levar alguns minutos)…")
            tr, aviso = transcrever(wav, pasta, a.modelo, a.idioma)
        else:
            aviso = "transcrição desligada"
    m = metricas(os.path.join(pasta, "info.json"))
    json.dump({"video": v, "metricas": m, "planos": planos, "audio": au, "transcricao": tr},
              open(os.path.join(pasta, "dados.json"), "w"), ensure_ascii=False, indent=1)
    resumo(pasta, v, planos, au, tr, m, aviso)
    print("Pronto:", os.path.join(pasta, "resumo.md"))


if __name__ == "__main__":
    main()
