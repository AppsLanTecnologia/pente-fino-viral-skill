# Pente fino viral · skill para o Claude Code

Mande o link de um Reel, TikTok ou Short que viralizou e o Claude faz o pente fino:

- **Métricas:** curtidas, comentários, views (quando disponíveis), por dia no ar e a proporção de comentários por curtida, que revela vídeos feitos para gerar comentário.
- **Ritmo:** cortes detectados, duração média de cada plano, palavras por segundo, tempo até a primeira palavra e volume do áudio.
- **Gancho:** o que se vê, se lê e se ouve nos primeiros 3 segundos, com quadros a cada 0,5 s.
- **Estilo e estrutura:** legendas, transições, paleta, música, efeitos, blocos do roteiro, reganchos e CTA.
- **Modelagem:** um roteiro original para o **seu** vídeo, momento a momento: fala, texto na tela, o que mostrar, como gravar e como editar.

Ele copia a estrutura e as técnicas, nunca as frases, a arte ou a música do outro criador.

## Instalar

```bash
git clone https://github.com/AppsLanTecnologia/pente-fino-viral-skill ~/.claude/skills/pente-fino-viral
```

Precisa ter no computador:

- [FFmpeg](https://ffmpeg.org) (cortes, quadros e áudio);
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (baixar pelo link): `pip install yt-dlp`;
- [Whisper](https://github.com/openai/whisper) (transcrição, opcional): `pip install openai-whisper`.

Não sabe instalar? Abra o Claude Code e peça: *"instale o ffmpeg, o yt-dlp e o whisper para a skill pente-fino-viral"*.

## Usar

**Os prompts prontos estão em [PROMPTS.md](PROMPTS.md):** instalar, fazer o pente fino com as informações certas do seu vídeo, pedir ajustes e resolver problemas.

O jeito mais curto, no Claude Code:

> faz o pente fino desse vídeo e modela pra um vídeo meu sobre [assunto]: https://www.instagram.com/reel/...

Quanto mais você contar sobre o seu vídeo (assunto, público, formato, objetivo, duração e chamada final), melhor o roteiro. O prompt principal do PROMPTS.md já pede tudo isso.

A análise fica em `analises/AAAA-MM-DD-<id>/`: vídeo, quadros, folhas de contato, transcrição, `dados.json`, `resumo.md` e a entrega final `analise.md`.

O script também roda sozinho:

```bash
python3 ~/.claude/skills/pente-fino-viral/scripts/analisar.py "<link ou arquivo.mp4>"
```

## Bom saber

- Se o post for privado ou o Instagram pedir login, baixe o vídeo e passe o arquivo `.mp4` no lugar do link. A skill nunca pede senha nem cookies.
- O Instagram costuma não entregar o número de views para ferramentas externas. Se você souber, conte ao Claude.
- Funciona ainda melhor junto com a skill [conteudo-viral](https://github.com/AppsLanTecnologia/conteudo-viral-skill): ela guarda quem você é e como você fala, e o roteiro modelado sai com a sua voz.
