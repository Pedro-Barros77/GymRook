# Estado das demonstrações

Atualização: 7 de novembro de 2026.

## Seleção ativa

Os **31 exercícios** têm MP4 a **12 fps**, GIF de compatibilidade e pôster. O ciclo normal tem 36 quadros em três segundos; o afundo alternado tem 48 quadros em quatro segundos. A prancha é uma sustentação estável: vídeo com 36 quadros iguais e GIF com uma imagem de 3.000 ms. A interface identifica a isometria.

A revisão atual publica 18 conjuntos em `dist/assets/animations-v2/`; os outros 13 conjuntos aprovados continuam em `animations-d-v1` e `animations-bc-v1`. As versões antigas a 24 fps continuam preservadas em disco, sem aparecer como seleções atuais.

## Alterações desta revisão

| Pedido | Resultado |
| --- | --- |
| Flexora: perna crescendo no alto | Novas poses em perfil, medidas nas próprias imagens; fêmur e tíbia acompanhados. Quadril apoiado, rolo e alavanca seguem o joelho fixo. |
| Stiff: distorção de pernas/quadril no fundo | Nova sequência em perfil, com pés plantados, flexão suave dos joelhos e amplitude controlada pelo quadril. |
| Afundo: salto no fechamento | Mesma referência em pé nas chaves 0, 8 e 15; o retorno do pé chega à postura inicial e mantém uma breve pausa antes de recomeçar. |
| Lateral: cotovelos travados | Novas poses com flexão visível durante todo o trajeto. |
| Crucifixo inverso: orientação e braços | Banco alinhado à máquina, vista posterior elevada, abertura dos dois braços juntos e torre afastada da área de passagem das mãos/alavancas. |
| Panturrilha no degrau | Substituída por panturrilha sentada em máquina com anilhas; texto, equipamento, combinação e mapa muscular atualizados. O mapa destaca sóleo principal e gastrocnêmio secundário. |
| Remada unilateral com ferragens móveis | Substituída por remada unilateral sentada na polia baixa, com cabo de aço e pegador individual. |
| Abdominal: banco móvel e pesos deformando | Assento e encosto vertical fixos; o apoio frontal acompanha a flexão. A torre tem proteção opaca, como no aparelho ilustrado, sem placas expostas se multiplicando. |
| Completar A e reduzir FPS | Crossover, rosca na polia, Scott, supra, infra e prancha acrescentados. Os quatro pilotos anteriores passam para 12 fps. |

A panturrilha sentada usa duas referências geradas e revisadas, em vez de nove poses com variações de anatomia. A segunda referência foi ajustada para que joelho e tornozelo subissem juntos, mantendo o antepé no apoio. O pivô traseiro fica fixo; almofada e anilha sobem na mesma alavanca.

O supra faz uma flexão curta do tronco, o infra mostra uma pequena elevação da pelve com joelhos dobrados, e a prancha mantém a postura. Não se acrescentou acompanhamento de carga, histórico ou progresso.

## Fontes, montagem e revisão

O `image_gen` integrado produziu as novas ilustrações. Cada pasta em [generated-frames-v2-fixes](generated-frames-v2-fixes/) preserva os prompts e as versões geradas. A [configuração](generated-frames-v2-fixes/config.json) e o [relatório de montagem](final-animations-build.json) registram recortes, fontes, hashes e tempos.

`scripts/build-final-animations.py` reutiliza os mecanismos D/B+C sem modificá-los. `prepareReady` libera somente a extração; `motionReady` exige revisão das fontes. A interpolação local usa Practical-RIFE 4.25, com registro por translação em regiões fixas. A volta normal reutiliza os 17 quadros interiores em ordem inversa; não há espelhamento lateral da imagem. A conversão dos dois ciclos antigos de 72 quadros usa exatamente os quadros ímpares para manter três segundos a 12 fps.

As revisões cruzadas incluem:
- [fontes da ficha A](generated-frames-v2-fixes/cross-review-leg-agent.json);
- [pernas e emendas](generated-frames-v2-fixes/qa-leg-temporal.json);
- [remada, abdominal e novos movimentos A](generated-frames-v2-fixes/upper-independent-motion-review.json);
- medidas e sobreposições nos diretórios de cada exercício;
- [resumo desta revisão](final-animations-review.md).

As medidas são estimativas manuais de projeções 2D nos próprios arquivos, com SHA e incerteza. Elas não provam comprimentos 3D ou ângulos anatômicos exatos. No Scott há um pequeno deslocamento aparente do centro do cotovelo ao longo do apoio, cerca de 15 px com incerteza de 8 px por oclusão; o contato do braço com o apoio permanece visível, sem deformação ou duplicação evidente. Isso foi registrado e aceito para este piloto ilustrativo.

## Verificação e uso offline

```sh
python scripts/verify-final-animations.py
npm run build
npm run check
```

O verificador dos 18 conjuntos confere os PNGs e entradas congelados, decodifica integralmente MP4 H.264/yuv420p de 512 × 512 a 12 fps, confere GIFs, duração, loop, pôsteres e integridade. Os tipos de ciclo, decimação e isometria têm regras próprias. Essas verificações não aprovam biomecânica.

A suíte Node verifica os 31 exercícios, cards, mapas, navegação, reprodução manual e operações offline, incluindo requisições Range. A interface foi verificada em DOM em memória; não houve teste desta revisão em telefone real.

O build e o check final passaram: **179 arquivos, 156,36 MiB e versão `fa4a7521fef8d86c`**. O verificador de mídia passou em **18/18**; os 31 vídeos também responderam corretamente às requisições Range em HTTP local, e os 31 pôsteres responderam a HEAD. O arquivo `asset-manifest.json` registra 163.957.200 bytes. Após publicar, abra o guia com conexão e refaça o download offline para obter a revisão completa.

## Preservação

O snapshot `backups/visual-v1-before-fixes-20261107/` tem manifesto SHA-256 e preserva 2.862 arquivos anteriores, incluindo mídias, fontes, scripts, configurações e PNGs. `scripts/verify-visual-backup.py` confere o arquivo e a preservação dos originais por escopo. Novas fontes rejeitadas também ficaram versionadas nas pastas de trabalho.

As revisões [D v1](leg-animations-v1-review.md), [B v1](bc-animations-v1-review-b.md), [C v1](bc-animations-v1-review-c.md) e [voador v5](pec-deck-v5-review.md) registram o histórico anterior. As aprovações históricas não se sobrepõem às correções solicitadas agora.

A tentativa de corpo Blender permanece arquivada em `backups/3d-trial-20261106/` e não é oferecida na interface.
