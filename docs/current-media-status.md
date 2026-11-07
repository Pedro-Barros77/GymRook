# Estado das demonstrações

Atualização editorial: 7 de novembro de 2026.

## Seleção ativa

Os quatro movimentos piloto são supino inclinado com halteres, crucifixo na máquina (voador), flexão de braços e rosca inversa na polia. São ilustrações geradas; permanecem em revisão técnica e não certificam anatomia, contato físico ou execução.

O crucifixo usa a **v5**, com MP4 como mídia principal e GIF de compatibilidade: 72 quadros, 24 fps e ciclo de três segundos. O detalhe oferece **Ver versão anterior** para consultar o GIF v4 preservado, também de 72 quadros; a v3 permanece em disco. Os outros três pilotos mantêm seus GIFs coloridos de 16 quadros; a rosca inversa também oferece o teste opcional **Testar versão suavizada**, com retorno ao original.

## Crucifixo v4: base preservada

A montagem usa 15 poses em resolução integral na diagonal aprovada, listadas em [landmarks.json](generated-frames-v4/pec-deck/landmarks.json). As poses são estabilizadas globalmente e a distribuição temporal considera as duas mãos. Practical-RIFE 4.25 em CPU, escala 1, interpola a ida; somente o primeiro intervalo usa FILM com midpoints recursivos, para evitar a duplicação do pegador. O quadro 19 recebe uma correção gerada por imagem, limitada a uma faixa de 25 × 80 px na borda da alavanca. A volta copia os quadros em ordem espelhada, incluindo essa correção. A saída compreende 72 PNGs, MP4 e GIF a 24 fps, em três segundos.

Para manter quantidade e textura fixas das placas, a montagem reutiliza o mesmo sprite de nove placas da pose 08 sobre o fundo vazio gerado `tower-clean`. O script monta essa composição; não usa o corpo da tentativa Blender. Interpolação pode introduzir deformações, especialmente em oclusões, e não é validação da execução.

- Fontes: [poses e configuração](generated-frames-v4/pec-deck/); [prompts iniciais](prompts/pec-deck-v4.json), [adicionais](prompts/pec-deck-v4-additional.json) e [correção da borda](prompts/pec-deck-v4-edge-repair.json). Todas as gerações usaram o `image_gen` integrado.
- Montagem: `python scripts/build-pec-deck-v4.py --config docs/generated-frames-v4/pec-deck/landmarks.json --film-intervals 0`.
- Saída: [mídia v4](../dist/assets/animations-pec-deck-v4/); [auditoria e revisão](pec-deck-v4-review.md).
- A v3 permanece em `dist/assets/animations/pec-deck-v3.gif` e `pec-deck-v3-poster.webp`; suas fontes e revisão anteriores estão em `docs/generated-frames-v3/` e `docs/pec-deck-perspective-review-20261107.md`.

Practical-RIFE 4.25 é o backend padrão do script. O backend anterior pode ser escolhido explicitamente com `--backend rife-ncnn-v4.6`. A primeira tentativa com sete poses e RIFE NCNN foi rejeitada por imagens fantasma e arquivada em `output/pec-deck-v4-rife-rejected/`.

Embora uma revisão anterior da v4 tenha aprovado correções de duplicações e oclusão, a v4 foi posteriormente reprovada quanto à continuidade estrutural do aparelho: a coluna desaparecia em parte da sequência e as alavancas mudavam de perfil. Essa distinção está na [auditoria](pec-deck-v5-review.md).

## Crucifixo v5: correção estrutural

A v5 substitui a coluna que desaparecia nos quadros 11–14 por uma coluna canônica fixa. As alavancas do aparelho usam a mesma malha rígida 3D em toda a ida, com material prateado derivado da fonte; o conector preto acompanha o eixo da haste. O corpo e o movimento são mantidos da v4: 37 quadros de ida e 35 espelhados, em 72 quadros a 24 fps. Limpezas RGBA seletivas removem a silhueta metálica antiga e harmonizam apenas fundo ou pele antes ocluídos. Uma remoção antisserrilhada de até dois pixels fica restrita ao suporte fixo. A partir de `y=164`, os pixels permanecem idênticos à v4; não há novos quadros humanos nem deformação da geometria do corpo.

A [revisão visual independente](pec-deck-v5-review.md) aprovou a correção após examinar 37 quadros canônicos e 36 sobreposições entre quadros vizinhos. Isso não certifica anatomia, contato físico ou execução. A edição limpa da estrutura foi feita uma vez com o `image_gen` integrado: [fontes](generated-frames-v5/pec-deck/) e [prompt](prompts/pec-deck-v5-structure.json). A mídia usa nomes `pec-deck.*` em `dist/assets/animations-pec-deck-v5/`.

Para reproduzir a montagem com as fontes e o backup preservados:

```sh
python scripts/prepare-pec-deck-v5-plate.py
python scripts/prepare-pec-deck-v5-cleanups.py
python scripts/render-pec-deck-rigid-levers.py
python scripts/build-pec-deck-v5.py
```

O renderizador usa por padrão os ajustes registrados do eixo das hastes. As máscaras efetivas ficam em `docs/generated-frames-v5/pec-deck/effective-tower-masks/`. Não se substitui a área superior inteira da cabeça por um retângulo: essa abordagem foi rejeitada por criar uma emenda de exposição.

A v4 anterior à alteração estrutural foi preservada e verificada em `backups/pec-deck-v4-before-structure-20261107/` (173 arquivos, cerca de 111 MB). Uma tentativa anterior baseada em uma faixa de painel foi rejeitada e preservada no backup do projeto.

## Rosca inversa: teste opcional

O teste mantém as nove poses ascendentes da folha gerada, estabilizadas por detalhes fixos da torre. A altura visual da barra redistribui o tempo e RIFE-v4.6 interpola os instantes intermediários; a volta reutiliza os quadros interiores em ordem inversa. O ciclo tem 72 quadros em três segundos a 24 fps. O GIF original continua como seleção inicial.

Fontes e relatórios locais: `output/generated-motion/reverse-cable-curl/`; mídias de comparação: `dist/assets/animations-interpolated/`; scripts: `scripts/prepare-generated-motion.py`, `scripts/interpolate-generated.py` e `scripts/verify-generated-motion.py`.

## Preservação e limites

O snapshot `backups/2d-v2-20261106/` preserva as versões anteriores com manifesto SHA-256. Fontes e prompts das primeiras versões permanecem em `docs/generated-frames/`, `docs/generated-frames-v2/` e `docs/prompts/`.

A tentativa Blender foi rejeitada por problemas de anatomia, contato e fidelidade à execução. Cenas e documentação foram preservadas, e suas mídias foram arquivadas fora da pasta publicada em `backups/3d-trial-20261106/animations-3d/`; ela não é oferecida como alternativa na interface.

Na v4, `scripts/verify-3d.py`, `npm run build` e `npm run check` passaram; esses testes de arquivos e interface não detectaram os problemas estruturais identificados depois. Para a v5, a codificação e `scripts/verify-3d.py` passaram: MP4 H.264/yuv420p de 512 × 512, 72 quadros a 24 fps em três segundos; GIF de 72 quadros, loop contínuo e duração de 3.000 ms (60 quadros de 40 ms e 12 de 50 ms); e pôster WebP de 512 × 512. O digest dos PNGs corresponde à revisão congelada (`f80dd9538e59e20105b05d915fbe7409272c5261e0614044f07bd0bf3b428d56`), e quatro arquivos da v4 continuam idênticos. A verificação de movimento confirmou ainda 16 arquivos originais preservados.

`npm run build` e `npm run check` passaram: 59 arquivos, 27,80 MB, cache `becf6b95b6040fef`, 31 movimentos e quatro pilotos verificados, além de interface em DOM em memória e operações offline. Em HTTP local na porta 4173, a página respondeu 200 e uma requisição Range ao novo MP4 respondeu 206 com 1.024 bytes. A revisão visual está descrita acima; não houve teste de layout em navegador real ou em telefone. Controles, contagem, continuidade ou cache não certificam anatomia nem execução correta.
