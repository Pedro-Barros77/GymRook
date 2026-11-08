# Revisão das demonstrações — terceira rodada

7 de novembro de 2026. Seleção atual em `dist/data.js`; configuração em [generated-frames-v3-repairs/config.json](generated-frames-v3-repairs/config.json). Todas as demonstrações ativas continuam a 12 fps. O ciclo habitual tem 36 quadros/3 s; o afundo tem 72 quadros/6 s.

## Pedidos atendidos

| Pedido | Alteração e evidência de revisão |
| --- | --- |
| Cabeça deformando no supino | Nova sequência com banco a 45° e trajetória dos halteres fora da cabeça. O contorno protegido reutiliza pixels da cabeça canônica; os halteres foram conferidos antes da composição para evitar mascarar uma colisão. Fontes e revisão em `incline-dumbbell-press/`. |
| Scott na máquina | Aparelho seletorizado com apoio dos braços. Antebraços raster giram em torno dos cotovelos fixos; alavanca e pegadores acompanham o movimento. Corpo, apoio e chassi ficam fixos. Texto e equipamento PT/EN atualizados. Fonte congelada em `preacher-curl/source-index.json`. |
| Crunch normal | `regular-crunch` substitui `reverse-crunch` e reutiliza a demonstração de `floor-crunch`. Pés e quadril permanecem apoiados. Texto, mapa e roteiro passam a descrever o crunch tradicional. O endereço antigo continua abrindo o item correspondente. |
| Crucifixo inverso incoerente | Novo aparelho integrado, com banco, apoio peitoral, torre e braços conectados. As duas mãos acompanham os pegadores; ambos os braços abrem juntos com os cotovelos elevados. Cabeça, quadril, pernas e chassi usam referência canônica. Revisões em `reverse-pec-deck/source-review.json` e `independent-final-composition-review.json`. |
| Anilha da panturrilha | Troca restrita ao equipamento: anilha horizontal, atravessada por pino vertical. Fora da região editada, todos os pixels do corpo são idênticos aos quadros antes aprovados. Evidência em `seated-plate-calf-raise/immutable-body-review.json`. |
| Máquina abdominal tremendo | Novo aparelho integrado com assento, apoio lombar e torre fixos. A alavanca é composta com comprimento constante; a superfície frontal acompanha a flexão do tronco. Fontes e composição em `machine-ab-crunch/`. |
| Pés virando na extensora | Novas poses em perfil e revisão dos quadros intermediários, acompanhando a orientação dos pés em vez de aceitar uma mudança súbita. Fontes em `leg-extension/`. |
| Hack na ponta dos pés | Referências corrigidas com calcanhar e antepé apoiados na plataforma. Os cantos da sola permanecem praticamente na mesma posição projetada nas poses. Fontes em `hack-squat/`. |
| Rolo atravessando a perna na flexora | Movimento composto de pernas raster com joelho fixo, tíbia e alavanca de comprimento constante. Rolo tangente à parte posterior da perna, acima do tornozelo. A versão escolhida conserva o volume muscular da ilustração. Fonte congelada em `lying-leg-curl/rig-v2/source-index-rig.json`. |
| Stiff deformando e tremendo | Nova sequência com proporções revisadas, pés estáveis e continuidade de quadril/tronco conferida em 19 quadros de ida e 18 sobreposições entre quadros. Fontes em `dumbbell-stiff-leg-deadlift/`. |
| Afundo saltando ao voltar | Retorno usa os mesmos desenhos da saída em ordem inversa. A redistribuição do tempo dá mais espaço para recolher o pé e desacelerar antes da postura em pé. As duas emendas foram comparadas visualmente com a versão linear; o rastreamento usa pontos reais dos tênis. |
| Símbolo de pausa | SVG com duas barras arredondadas, mantendo rótulos acessíveis e estado de reprodução. |

Os caminhos da tabela são relativos a `docs/generated-frames-v3-repairs/`.

## Conteúdo e volume

Há 31 itens de consulta e 30 demonstrações distintas. A troca do crunch conserva os dois blocos de 20 repetições mais a prancha; não houve orientação para reduzir o volume. A Scott mantém 3 × 8–12. Não foi acrescentado acompanhamento de cargas ou progresso.

## Como a revisão foi feita

O `image_gen` integrado gerou e editou as ilustrações. O processo mantém a aparência colorida e muscular dos desenhos anteriores. A composição combina interpolação Practical-RIFE, partes fixas canônicas e, onde necessário, rotação de recortes raster/peças rígidas. Não usa o corpo 3D da tentativa Blender.

As fontes foram revisadas antes da interpolação e os quadros efetivos foram revisados depois. Contatos, mãos, pés, peças fixas e emendas receberam recortes ampliados e sobreposições. Ciclos de ida e volta reutilizam os PNGs interiores byte a byte. A revisão cruzada do afundo inclui as janelas ao redor dos quadros 36→37 e 72→1.

As máquinas interpoladas, como o crucifixo inverso, não são modelos cinemáticos completos. Medidas em imagens são projeções 2D com oclusões; não certificam comprimentos anatômicos, biomecânica ou execução. A ausência de diferenças nas partes protegidas comprova estabilidade desses pixels, não a correção das partes móveis. O caráter ilustrativo continua indicado na interface.

## Verificação técnica

O relatório de montagem é [repair-animations-build.json](repair-animations-build.json). O verificador confere fontes e PNGs congelados, cópias de retorno, decodificação integral dos MP4s H.264/yuv420p, dimensões, 12 fps, duração, GIFs, pôsteres e preservação dos arquivos anteriores. A suíte Node confere conteúdo, navegação, reprodução e operações offline.

A [verificação técnica final](repair-animations-technical-verification.json) passou em 10/10 conjuntos e 396 PNGs. Os dez MP4s, dez GIFs e dez pôsteres somam 38.033.535 bytes; 3.392 arquivos originais de produção continuam idênticos.

```sh
python scripts/verify-repair-animations.py
npm run build
npm run check
```

`npm run build` e `npm run check` passaram: 210 arquivos, 202.009.838 bytes, cache `e9ffb6b9974e1005`. A [conferência HTTP](repair-http-check.json) verificou os 31 itens e 30 vídeos distintos, com Range 206 e pôsteres 200. O [índice final](generated-frames-v3-repairs/final-release-review.json) reúne as dez revisões visuais e seus hashes. A [geração](prompts/repair-animations-v3.json) tem 27 registros de prompts preservados.

A interface foi verificada em DOM em memória; esta rodada não inclui teste em telefone real ou playback em navegador nativo. O tamanho do pacote e as orientações de atualização ficam em [current-media-status.md](current-media-status.md).

## Preservação

O snapshot `backups/visual-v2-before-repairs-20261107/` contém 3.472 arquivos e 1.194.394.265 bytes, com manifesto SHA-256. Fontes, scripts, PNGs e mídias anteriores permanecem preservados. Estudos rejeitados e comparações ficam nas pastas de fontes e em `output/repair-animations/`, fora do deploy. Somente `dist/` é publicado pelo workflow existente.
