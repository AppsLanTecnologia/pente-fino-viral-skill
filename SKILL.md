---
name: pente-fino-viral
description: Faz o pente fino de um vídeo que viralizou (Reel do Instagram, TikTok, Shorts) e modela tudo para o vídeo de quem pediu. Baixa o vídeo, mede métricas, cortes, ritmo de fala, áudio e gancho, disseca estilo e estrutura, e entrega um roteiro momento a momento dizendo o que falar, mostrar, gravar e editar. Use sempre que a pessoa mandar um link de vídeo de outro criador, disser "analisa esse vídeo", "por que isso viralizou", "quero um vídeo igual a esse", "modela esse reels pra mim", "faz um pente fino" ou colar um link do instagram.com/reel, tiktok.com ou youtube.com/shorts, mesmo sem falar em "análise".
---

# Pente fino viral

Esta skill transforma um vídeo que deu certo para outra pessoa em um plano de vídeo para quem pediu. Ela copia a **estrutura, o ritmo e as técnicas**, nunca as frases, a arte ou a cara do outro criador. O resultado é um vídeo original que usa o que fez o original funcionar.

Responda no idioma de quem pediu (o padrão é português do Brasil).

## Fluxo

### 1. Baixar e medir
Rode o script com o link (ou com o caminho de um .mp4, se o download falhar):

```bash
python3 <pasta-desta-skill>/scripts/analisar.py "<link>" --saida analises
```

Ele cria `analises/AAAA-MM-DD-<id>/` com o vídeo, quadros do gancho, um quadro por plano, folhas de contato, transcrição com tempo por palavra, `dados.json` e `resumo.md`. A transcrição usa o Whisper e leva alguns minutos; avise antes.

- Se o download falhar (post privado, pedido de login), peça para a pessoa baixar o vídeo e mandar o arquivo. Não peça senha nem cookies.
- O Instagram costuma não entregar visualizações para o yt-dlp. Se a pessoa souber as views ou os seguidores do criador, use. Não invente número.

### 2. Olhar o vídeo de verdade
Leia `resumo.md` e **abra as imagens**: todos os quadros de `gancho/`, as folhas de `folhas/` e os quadros de `cenas/` dos planos importantes (gancho, viradas, CTA). Os números dizem o ritmo; as imagens dizem o estilo. Não analise só pelo texto.

Se a detecção de cortes errar (vídeo com câmera tremida, zoom contínuo ou tela gravada), corrija olhando as folhas e diga isso. Em animação sobre fundo fixo, o script pega as trocas de cena, mas não as mudanças dentro da tela (um item entrando, uma janela abrindo). Conte essas mudanças pelas folhas: elas são os reganchos do vídeo.

### 3. Fazer o pente fino
Siga `referencias/pente-fino.md`, dimensão por dimensão. Para cada achado, diga **o que é, em que segundo aparece e por que funciona**. Separe o que é técnica reproduzível do que é contexto que não se copia (base de seguidores, tendência do momento, fama do criador).

### 4. Entender o vídeo de quem pediu
Antes de modelar, descubra:
- o assunto do vídeo dele (se não disse, sugira 2 ou 3 assuntos que encaixam na estrutura e pergunte);
- o formato possível: rosto na câmera, só narração, tela gravada ou animação;
- o que ele vende ou quer como resultado (seguidores, comentários, venda).

Se existir uma skill de marca no projeto (por exemplo `.claude/skills/conteudo-viral/marca/`), leia os arquivos dela: os fatos, números e o jeito de falar vêm de lá. Os ganchos de `manual/ganchos.md` e o portão de `revisao/checklist.md` dessa skill também valem aqui. Se não existir, pergunte os fatos que o roteiro precisa e não invente números sobre a pessoa.

### 5. Modelar e entregar
Use o formato de `referencias/entrega.md`: ficha, por que funcionou, linha do tempo do original, gancho dissecado, ritmo e estilo em números, e então o **roteiro modelado momento a momento**, com fala, texto na tela, o que se vê, como gravar e como editar em cada trecho.

Salve a entrega em `analises/AAAA-MM-DD-<id>/analise.md` e mostre o principal na conversa.

## Regras
- **Estrutura sim, cópia não.** Pode reaproveitar a família do gancho, a sequência de blocos, o ritmo de cortes, o tipo de legenda e de transição. Não reaproveite frases, roteiro, música com direitos, arte, personagem ou marca do original.
- **Número só com fonte.** Métricas vêm de `dados.json` ou da pessoa. Promessa de ganho não entra no roteiro.
- **Mostre a conta.** Ao dizer "corta a cada 1,8 s" ou "fala 3,2 palavras por segundo", isso tem que estar no `resumo.md`.
- **Seja específico.** "Gancho forte" não ajuda. "Aos 0,4 s aparece o print com o número e a fala começa pelo resultado" ajuda.
