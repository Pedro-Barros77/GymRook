# Produção das demonstrações 3D

> Tentativa arquivada e rejeitada. O usuário identificou problemas de anatomia, contato e execução. Continuidade técnica e testes de formato não validaram a biomecânica. O guia voltou às ilustrações geradas; estas cenas não são a mídia ativa. Os MP4s/GIFs deste teste ficam em `backups/3d-trial-20261106/animations-3d/` e os `.blend` em `assets/3d/scenes/`.

As cenas são produzidas e renderizadas offline. O PWA recebe somente os arquivos de vídeo, GIF e imagem já prontos. Não há modelo 3D, Blender ou simulação física sendo executada no celular.

## Backup do piloto 2D

O snapshot `backups/2d-v2-20261106/` preserva os quatro GIFs coloridos de 16 quadros, seus pôsteres, `data.js`, o script de montagem, os prompts e todas as folhas fonte PNG das duas primeiras versões. Seu manifesto contém SHA-256 e tamanho de cada arquivo. As fontes originais também continuam nos diretórios `docs/generated-frames/` e `docs/generated-frames-v2/`.

```sh
python scripts/backup-2d.py --verify
```

O script verifica e preserva snapshots já existentes; não os sobrescreve. As instruções de restauração estão no `RESTORE.md` do backup. Os arquivos desse diretório não entram no download offline do site.

## Quadros e formatos

Cada ciclo contém **72 quadros renderizados a 24 fps**, com duração de três segundos. A entrada do codificador é:

```text
output/3d/<exercise-id>/frames/frame_0001.png
...
output/3d/<exercise-id>/frames/frame_0072.png
```

Os quatro IDs do piloto são `pec-deck`, `incline-dumbbell-press`, `push-up` e `reverse-cable-curl`.

O formato preferido é MP4/H.264, sem áudio, com `yuv420p` e `faststart` para reprodução ampla em navegadores móveis. O vídeo mantém uma taxa constante de 24 fps. Cada animação também tem um GIF compatível e um pôster WebP.

O GIF só aceita durações em centésimos de segundo: não existe nele um intervalo constante de 41,666… ms. Sua cópia de compatibilidade usa intervalos de 40/50 ms distribuídos por arredondamento acumulado, mantendo os mesmos quadros e exatamente três segundos por ciclo. A paleta de 192 cores é compartilhada por todos os quadros, sem pontilhado. Não há geração de imagens por quadro, morphing, crossfade ou mudança de textura na codificação.

## Codificação e verificação

Dependências apenas de produção:

```sh
python -m pip install Pillow imageio-ffmpeg
python scripts/encode-3d.py --exercise pec-deck
python scripts/verify-3d.py
```

Para codificar os quatro exercícios depois que todas as cenas tiverem sido renderizadas:

```sh
python scripts/encode-3d.py --exercise all
```

Os resultados ficam em `dist/assets/animations-3d/`: `<id>.mp4`, `<id>.gif`, `<id>-poster.webp` e `manifest.json`. A folha de contato de inspeção fica junto aos quadros em `output/3d/<id>/contact-sheet.jpg`, fora do site publicado.

O verificador decodifica o MP4 completo com FFmpeg e confere 72 quadros, taxa de entrada 24/1 fps, formato de pixels e hashes. Também confere dimensões, animação e duração dos GIFs, além de pôsteres válidos. O manifesto registra a versão do codificador, tamanhos, hashes e os intervalos efetivos do GIF.

Nesta sessão o codificador é fornecido por `imageio-ffmpeg 0.8.1`, cujo executável empacotado informa FFmpeg `9.0.2-essentials_build-www.gyan.dev`. Não foi incorporada mídia de exercício de bibliotecas externas. A origem e as licenças da malha humana ficam documentadas separadamente em `3d-human-provenance.md`.

Essas verificações confirmam integridade dos arquivos e temporização. A anatomia, os pontos de contato e a mecânica das cenas também precisam de inspeção visual e revisão técnica das poses.
