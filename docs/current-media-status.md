# Estado das demonstrações

Atualização: 8 de novembro de 2026, revisão complementar.

## Seleção ativa

Os **31 exercícios** têm demonstrações distintas em MP4 a **12 fps**, GIF de compatibilidade e pôster. O ciclo habitual tem 36 quadros em três segundos; o afundo alternado mantém 72 quadros em seis segundos. A prancha permanece uma sustentação isométrica estável.

Quatro conjuntos novos ficam em `dist/assets/animations-v4/`: Scott na máquina, abdominal infra com elevação das pernas, panturrilha em pé inclinada e abdominal sentado com alças altas. O supino volta diretamente aos arquivos de `animations-v2`, sem geração nem recodificação, e fica encerrado para novas alterações. As outras 26 demonstrações mantêm a seleção anterior.

## Conteúdo e fontes

A [revisão complementar](followup-animations-review.md) relaciona os cinco pedidos às fontes e aos estudos. Supra e infra usam vídeos próprios: crunch do tronco e elevação das pernas deitado. Permanecem 20 repetições de cada, mais a prancha, em duas voltas. Equipamentos PT/EN, instruções e lista muscular acompanham as novas variantes.

A panturrilha é a versão em pé, inclinada para a frente, com o corpo voltado ao aparelho, confirmada pelo usuário em 8 de novembro. A versão sentada com anilha horizontal permanece separada e inalterada. A amplitude visual destaca calcanhares abaixo e acima do apoio, sem impor ângulos anatômicos obrigatórios a todos.

As [fontes e configuração](generated-frames-v4-followup/config.json) registram seleção, tempos, máscaras e hashes. As ilustrações foram produzidas com o `image_gen` integrado; os prompts ficam por exercício e no [índice da rodada](prompts/followup-animations-v4.json). O [relatório de montagem](followup-animations-build.json) identifica os PNGs codificados.

O processo usa Practical-RIFE 4.25 e composição raster. O infra conserva o mesmo desenho das pernas na rotação; partes fixas usam pixels canônicos. A tentativa Blender não participa das demonstrações. Fontes com pernas crescendo ou joelhos compensando a panturrilha foram rejeitadas antes da seleção final.

## Verificação e uso offline

```sh
python scripts/verify-followup-animations.py
npm run build
npm run check
```

O verificador exige todos os quatro conjuntos, confere fontes e PNGs congelados, cópias de retorno, decodificação integral dos MP4s H.264/yuv420p de 512 × 512 a 12 fps, GIFs, duração, pôsteres e preservação dos originais. O supino restaurado tem uma conferência SHA própria. A suíte Node verifica os 31 exercícios, mapas, navegação, reprodução e operações offline; inclui uma verificação de que supra e infra demonstram movimentos distintos.

A [verificação técnica](followup-animations-technical-verification.json) passou em **4/4 conjuntos e 144 PNGs**. Os quatro MP4s, quatro GIFs e quatro pôsteres somam 15.370.941 bytes. Foram conferidos 5.735 arquivos originais preservados e os três arquivos do supino restaurado.

Na validação das animações, a [conferência HTTP local](followup-http-check.json) passou nos **31 vídeos distintos** e 31 pôsteres: vídeos responderam 206 para Range de 1.024 bytes e pôsteres responderam 200. O relatório conserva a versão de cache daquela conferência.

A publicação **1.0** acrescenta a versão ao lado de Treinos. O build local e `npm run check` passaram com **223 arquivos, 207,32 MiB (217.390.243 bytes), cache `340cfce2fc43d3df`**. O GitHub Actions recalcula o manifesto durante o deploy. [Notas da versão](release-1.0.md).

A revisão visual inclui quadros no tamanho real, recortes ampliados, contatos e sobreposições. Não certifica anatomia ou cinemática 3D completa. A interface é verificada em DOM em memória e as mídias por HTTP local; esta rodada não inclui teste em telefone real ou playback em navegador nativo.

Após publicar, abra o guia com conexão e refaça o download offline para obter a revisão completa.

## Preservação

O snapshot `backups/visual-v3-before-followup-20261107/` contém 5.860 arquivos e 1.879.987.059 bytes, com SHA conferido. Os arquivos anteriores de mídia e produção continuam preservados; estudos rejeitados também ficam guardados. O supino de `animations-v2` permanece byte a byte idêntico à versão anterior.

As revisões [v3](repair-animations-review.md), [v2](final-animations-review.md), [D v1](leg-animations-v1-review.md), [B v1](bc-animations-v1-review-b.md) e [C v1](bc-animations-v1-review-c.md) são históricas. Suas aprovações não se sobrepõem às correções seguintes.

Cache, renders e backups locais ficam fora do deploy. O workflow existente publica somente `dist/`; a produção das imagens não é repetida no GitHub Pages.
