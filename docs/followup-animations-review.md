# Revisão complementar das demonstrações

8 de novembro de 2026. Esta rodada atende aos cinco pedidos posteriores à v3. São quatro conjuntos novos em `dist/assets/animations-v4/` e a restauração de um conjunto existente. As outras 26 demonstrações mantêm a seleção anterior. Tudo continua a 12 fps; os quatro novos ciclos têm 36 quadros em três segundos.

## Supino restaurado e encerrado

O supino inclinado volta diretamente a `dist/assets/animations-v2/incline-dumbbell-press.*`. Não houve geração, interpolação ou recodificação desses arquivos. Os três SHA-256 correspondem ao snapshot anterior à v3; a [conferência](generated-frames-v4-followup/supino-restore-preflight.json) registra os valores.

Por instrução explícita, essa demonstração fica fora de novas alterações. O pipeline v4 não inclui seu ID e verifica a preservação dos arquivos restaurados.

## Scott na máquina

A animação foi refeita com arte muscular em três quartos, apoio frontal inclinado e pegada supinada. A fonte selecionada é `preacher-curl/sheet-v1.png`. As outras tentativas ficam preservadas.

Os quadros finais ficam em `preacher-curl/static-v1/frames/`, com cabeça, base e partes fixas canônicas. Um quadro com barra duplicada foi substituído por uma inferência alternativa no mesmo instante, sem alterar o tempo do movimento; a volta usa a cópia correspondente. O [índice da fonte](generated-frames-v4-followup/preacher-curl/static-v1/source-index.json) e a revisão temporal registram a escolha.

## Supra e infra distintos

O supra continua sendo o crunch do tronco, `floor-crunch`. O infra passa a `lying-leg-raise`, com elevação das pernas juntas e cabeça/ombros apoiados. Foram mantidos 20 supra + 20 infra + prancha, duas voltas. Os endereços antigos `reverse-crunch` e `regular-crunch` levam ao novo infra.

Duas folhas geradas foram rejeitadas porque as pernas aumentavam de comprimento na elevação. A seleção final usa um único recorte muscular, com rotação no quadril, comprimento constante e pelve/cintura sobrepostas da referência fixa. A perna distante fica oculta pela vista de perfil. O [índice da fonte selecionada](generated-frames-v4-followup/lying-leg-raise/rig-v2/source-index-native-v2.json) e as revisões independentes registram os quadros reais.

Texto e lista muscular distinguem a elevação realizada pelos flexores do quadril da estabilização abdominal. A referência consultada foi [ExRx — Lying Straight Leg Raise](https://exrx.net/WeightExercises/HipFlexors/BWStraightLegRaise). Não se apresenta um músculo abdominal inferior separado.

## Panturrilha em pé inclinada

A versão implementada é a máquina de panturrilha em pé inclinada para a frente: peito voltado para o aparelho, apoio dos ombros e antepé na borda, com os calcanhares livres. O usuário confirmou essa identificação em 8 de novembro. A panturrilha sentada com anilha horizontal permanece inalterada.

A arquitetura foi conferida na referência primária [Atlantis M318](https://atlantisstrength.com/gym-equipment/m318); a imagem comercial foi usada somente como referência local e não entra no site. As novas fontes mostram os calcanhares abaixo e acima do degrau. A indicação visual de amplitude não vira uma prescrição de ângulos obrigatórios para todos.

A folha de nove poses foi rejeitada: os joelhos flexionavam no alto para compensar a pouca subida do corpo. A fonte escolhida parte dos dois originais, `standing-machine-calf-raise/start-v2.png` e `end-v1.png`, nos quais o corpo e o carrinho sobem juntos. O estudo de pose intermediária também foi preservado, sem substituir o corpo aprovado.

Os fragmentos de sola foram corrigidos com uma edição local do quadro intermediário e uma nova interpolação apenas da região dos pés. Fora dessa região, 252.827 pixels por quadro conservam o corpo original; os tempos do movimento não foram alterados. A estrutura usa uma placa fixa e a pilha de pesos é um único recorte rígido transladado. O [índice da cena final](generated-frames-v4-followup/standing-machine-calf-raise/final-composition-v1/source-index.json) e os recortes ampliados permitem conferir os contornos no degrau. Há pequena variação contínua da faixa branca da sola em alguns intermediários; o sapato não é um modelo 3D rígido.

## Abdominal sentado com alças altas

O aparelho foi substituído por arquitetura com alças junto ao pescoço/ombros, conforme a descrição recebida. A referência primária de arquitetura foi [Life Fitness Axiom Abdominal](https://shop.lifefitness.com/products/axiom-series-abdominal). A primeira fonte que lembrava um pec-deck foi rejeitada.

As sete poses úteis de `machine-ab-crunch/sheet-v2.png` descrevem a flexão do tronco. Assento, torre, pés e apoio lombar usam referência canônica, respeitando o corpo em primeiro plano. A área do encosto revelada pela flexão recebeu uma placa de equipamento sem atleta; não se gerou outro corpo para essa limpeza.

O [pacote congelado](generated-frames-v4-followup/machine-ab-crunch/final-composition-packet.json), a revisão temporal e a segunda opinião registram os 36 PNGs e suas máscaras. As alças permanecem ligadas às mãos; o banco não acompanha as costas.

## Fontes, limites e checagem

As ilustrações e edições foram produzidas pelo `image_gen` integrado, com prompts preservados por exercício em `docs/generated-frames-v4-followup/` e no [índice dos 20 registros de prompts](prompts/followup-animations-v4.json). A [configuração](generated-frames-v4-followup/config.json) registra a seleção efetiva. O movimento combina Practical-RIFE 4.25 e composição raster; não usa o boneco 3D da tentativa Blender.

As revisões incluem quadros no tamanho real, 19 posições de ida, 18 sobreposições e retorno byte a byte dos 17 quadros interiores. Os registros de preservação comprovam estabilidade dos pixels protegidos; não certificam anatomia, execução ou cinemática 3D completa. O desenho e o texto continuam sujeitos à revisão técnica no aparelho real.

```sh
python scripts/verify-followup-animations.py
npm run build
npm run check
```

Os resultados finais e o tamanho do pacote ficam em [current-media-status.md](current-media-status.md). A suíte da interface usa DOM em memória; esta rodada não inclui teste em telefone real ou playback em navegador nativo.

A [verificação técnica final](followup-animations-technical-verification.json) passou nos quatro conjuntos: 144 PNGs, quatro MP4s, quatro GIFs e quatro pôsteres. As 12 mídias somam 15.370.941 bytes. O [índice visual final](generated-frames-v4-followup/final-release-review.json) reúne fontes, pareceres e hashes. A [conferência HTTP](followup-http-check.json), o build e a suíte PWA também passaram: 31 vídeos distintos, 223 arquivos no pacote, 217.390.026 bytes e cache `5dc7b988d3dfdfea`.

## Preservação

O snapshot `backups/visual-v3-before-followup-20261107/` contém 5.860 arquivos e 1.879.987.059 bytes, com SHA conferido. Fontes, quadros, mídias e estudos anteriores permanecem preservados. O deploy continua publicando somente `dist/` pelo workflow existente; cache, renders e backups locais ficam fora dele.
