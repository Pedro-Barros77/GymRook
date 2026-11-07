# Revisão visual das animações de pernas — ficha D

Revisão de referência em 7 de novembro de 2026. Escopo: piloto ilustrativo colorido, planejado para 12 fps. Esta revisão não certifica biomecânica profissional nem a correspondência exata com um modelo comercial de máquina.

**Parecer final: os sete ciclos da ficha D estão aprovados visualmente para codificação, nos digests da seção final.** Os pareceres e identificadores anteriores abaixo são históricos; a extensora teve sua distribuição temporal corrigida e o afundo recebeu dois reparos de interpolação antes desta aprovação completa.

## Poses de referência

Foram inspecionadas as seis sheets de `docs/generated-frames-d-v1/`, cada uma com nove poses ordenadas por linhas. Esta seção refere-se às fontes, antes da interpolação e codificação.

| Exercício | Movimento e contatos observados | Parecer das referências |
| --- | --- | --- |
| Cadeira extensora | Joelhos estendem progressivamente e o rolo acompanha a frente da parte baixa das canelas. Pelve, tronco, mãos e apoio permanecem estáveis; as pernas não se invertem. | Adequada ao piloto; conferir o encaixe do rolo nos intermediários. |
| Agachamento hack | Pés permanecem sobre a plataforma; corpo, encosto, ombreiras e anilhas descem na direção do trenó. Joelhos e quadril flexionam sem a pelve perder o encosto. | Adequada ao piloto; preservar trilhos e plataforma fixa sem congelar o trenó. |
| Mesa flexora | Pelve, tronco e coxas continuam apoiados; o movimento principal vem dos joelhos e eleva os calcanhares com o rolo atrás da parte baixa das pernas. | Adequada ao piloto; as primeiras duas poses têm pouca diferença, sem salto de articulação evidente. |
| Stiff com halteres | Quadril vai para trás, tronco inclina, joelhos mantêm pequena flexão e os dois halteres descem próximos das pernas. A primeira versão tinha pescoço estendido; a selecionada corrige o olhar para acompanhar o tronco. | Adequada ao piloto; preservar os pés apoiados ao registrar as poses. |
| Cadeira abdutora | Almofadas ficam por fora das coxas, e os joelhos se afastam; tronco e pelve mantêm a posição. | Adequada ao piloto; não confundir as alavancas e pedais móveis com base fixa. |
| Cadeira adutora | Almofadas ficam por dentro das coxas, e os joelhos se aproximam; tronco e pelve mantêm a posição. | Adequada ao piloto; o fechamento deve manter contato com os apoios internos. |

Não foi identificado nas seis sheets o desaparecimento de um montante ou a formação de uma alavanca em S como no problema anterior do crucifixo. Há pequenas diferenças geradas de textura, reflexo e enquadramento; a montagem deverá usar registro por partes fixas e conferir as transições. Nenhuma nova geração foi solicitada apenas por essas diferenças discretas de estilo.

## Montagem e mídia

Foram conferidos os seis painéis `output/leg-animations/<id>/qa/anchors-contact.png`, cobrindo as 54 âncoras extraídas de 512 × 512. Foram abertas também as sobreposições entre vizinhas da flexora, stiff e adutora. As duplicações nos painéis de onion skin são da sobreposição diagnóstica, não quadros de saída.

Não há região estática que precise ser colada por cima para corrigir um defeito estrutural material nessas fontes. Recomenda-se manter `preserveStaticRects` vazio: uma cópia retangular sem necessidade poderia introduzir emenda de cor ou cortar uma peça móvel, como nas tentativas anteriores do crucifixo. As fontes têm pequenas variações de superfície, aceitáveis para esta etapa do piloto.

O registro inicial das cadeiras abdutora/adutora usava uma faixa baixa que inclui os pedais móveis. A sobreposição da adutora mostra deslocamento global/duplicação da cabeça na transição 3–4; isso é um problema da referência de registro, não uma razão para regenerar as poses. Foi sugerida ao responsável pela montagem uma região de teste no canto superior esquerdo da torre, `[55,10,155,210]` em 512 px, antes do contorno do braço. Se ela não melhorar a estabilidade, preferir desativar o registro dessas duas sheets já enquadradas de forma semelhante. A alteração deve ser verificada antes da interpolação.

O registro das cadeiras foi corrigido com a região da torre indicada, com deslocamentos abaixo de 0,25 px informados pelo responsável pela montagem. Os contatos e sobreposições posteriores já não mostram o deslocamento global induzido pelos pedais.

## Histórico da primeira montagem interpolada

Foram vistos todos os 19 quadros de ida dos seis movimentos acima, em contatos adicionais de quatro colunas, e suas 18 transições vizinhas em onion skin. São 114 posições únicas. A volta de 17 quadros de cada ciclo foi conferida byte a byte: reutiliza as posições de ida correspondentes, sem uma nova trajetória gerada.

Nesta saída de 512 × 512, não foram identificados membros extras, rolos duplicados, peças fixas desaparecendo ou uma mudança grande e impossível de formato das máquinas. Os contatos e movimentos descritos na tabela se mantêm nos intermediários: pés apoiados no hack/stiff, rolos acompanhando as canelas, apoio do tronco nas máquinas, almofadas externas na abdutora e internas na adutora. Pequenas diferenças de superfície/reflexo continuam visíveis; são aceitáveis no escopo deste piloto, sem declarar a estrutura uma simulação mecânica exata.

**Parecer visual daquela montagem: seis ciclos aprovados quanto aos intermediários, a 12 fps, 36 quadros e três segundos.** A extensora foi posteriormente substituída após o root detectar uma cadência abrupta na costura. A aprovação final deve usar a tabela da seção final. O digest desta tabela histórica identifica os PNGs inspecionados então: SHA-256 da concatenação ordenada dos bytes dos 36 hashes SHA-256, não do texto hexadecimal nem do MP4.

| Movimento | Digest dos PNGs aprovados |
| --- | --- |
| Cadeira extensora | `2382f6957a2e6c272ec6c8e3cc7be2d2c44d1a9d0504d869a0b4910ce3415bc1` |
| Hack squat | `8d9b9ff78ef00aa4dcee7fbc95568cc65df1ee11d209dab6b92c0f85b6756214` |
| Mesa flexora | `b0b641ad30fa8267bf536721a684739a97edbd78b77d58bdfacc53e83de8b8f3` |
| Stiff com halteres | `0506127228bdde22d9ab2a5221dd052a5524e1d0f440fa8e5265c62665be9260` |
| Cadeira abdutora | `80dfbb8e0db3e8b3629fa7ce2e68aa0fd86613bc505d08302c57f525f606cf9d` |
| Cadeira adutora | `95ce634063bf06877aba14556855835a556dac49deef6359df8beeec0654d624` |

Evidências fora da distribuição: `output/leg-animations-review/<id>-all-1.png`, `digests.json` e `output/leg-animations/<id>/qa/transitions-onions.png`. Foram lidos também os contatos de amostra do pipeline; esses contatos sozinhos não cobrem todos os quadros.

## Afundo alternado: primeiro interpolado precisa de correção focal

A fonte frontal alternada foi promovida pelo root e pelo revisor das cadeiras. Nesta auditoria foram vistas as 16 âncoras e os 48 quadros do ciclo: a perna à esquerda da imagem avança primeiro, a outra avança na segunda metade, e existe uma posição em pé entre lados. A origem inicial que repetia a mesma perna não foi usada nesta montagem.

O primeiro interpolado tem digest `b1f02678be72486f412c23b208f82d28040f52edfa6b1cf4bd009c8f764849c7`. Nos quadros **18 e 42**, durante o retorno, um tênis fica cinza e visivelmente semitransparente. Foram abertos os PNGs integrais 17–20: o quadro 18 difere materialmente da opacidade normal dos vizinhos. Isso corresponde aos intervalos de âncoras 5→6 e 13→14, na amostra de tempo 2/3. Os demais 46 quadros mostram dois membros inferiores coerentes e mantêm a alternância.

**Parecer deste digest do afundo: pendente de correção desses dois intermediários.** Não é preciso regenerar a ficha nem reabrir os seis ciclos aprovados. O novo resultado deve ser revisto nos respectivos vizinhos antes da promoção. A codificação e a verificação dos arquivos finais são etapas separadas desta revisão visual.

## Aprovação final dos sete ciclos

Na extensora, o progresso das nove poses voltou a ser uniforme, com a distribuição cossenoidal dos 19 instantes de ida. Foram revistos todos os 19 PNGs da nova ida: a subida continua progressiva, o rolo acompanha as canelas e a costura não apresenta o salto observado na tentativa de redistribuição anterior. A volta continua byte-exata.

No afundo, a tentativa de usar FILM nos quadros 18 e 42 foi rejeitada por criar um terceiro tênis separado do corpo. A versão final utiliza **Practical-RIFE 4.25 com tempo efetivo 0,9 somente nessas duas amostras**, conservando a taxa nominal de 12 fps e os outros 46 PNGs. Não houve redesenho manual de membros nem espelhamento da imagem. Foram vistos novamente 17–20, 41–44 e 47–48/1–2 em resolução integral: os dois tênis ficam opacos, não surge um terceiro pé, a alternância continua legível e não foi identificado salto material na costura. Há uma pequena mudança de velocidade local no retorno; no escopo do piloto a 12 fps ela é aceitável e está registrada na configuração.

Os cinco ciclos restantes mantêm os mesmos bytes da revisão anterior. Esta aprovação combina a revisão integral de 114 posições de ida, 48 quadros do afundo, 108 transições de ida em sobreposição e a revisão focal das alterações finais. Ela não se baseia apenas nos testes de contagem ou hashes.

Os identificadores finais abaixo seguem a convenção usada no relatório do pipeline: **SHA-256 da concatenação das strings hexadecimais dos hashes SHA-256 dos PNGs ordenados**. Essa convenção difere da tabela histórica de hashes brutos; são fórmulas diferentes, não versões diferentes da imagem. Os dois cálculos foram conferidos para evitar ambiguidade.

| Movimento final aprovado | Quadros / duração a 12 fps | Digest final das strings hexadecimais |
| --- | --- | --- |
| Cadeira extensora | 36 / 3 s | `3bd701e01b5c3f6eaed0684f434493b1e02f5265e71a86742bfe350abe427e34` |
| Hack squat | 36 / 3 s | `f275ac5e184143196e608d86a6879ef256f30bab13ddd3473967281913f80d0d` |
| Mesa flexora | 36 / 3 s | `64a07771b8ccc8c32b0baf06fc047a1563a61e75c4beb1430f684505c90b472e` |
| Stiff com halteres | 36 / 3 s | `9ae155c82fc280292515d02769da6ebed07136fbdb91f2633f09fbedf5614640` |
| Cadeira abdutora | 36 / 3 s | `ca6f7b30aef5eeca147f058badcb4cf5faf3956c0cf3111b15905d3617e6db91` |
| Cadeira adutora | 36 / 3 s | `0ca737928dd1204e70f8bd2c53e9809663b3b0e6acfd821da96908165c3350eb` |
| Afundo alternado | 48 / 4 s | `0d768014dfefd0a6075e042bc83a33286d4a1f9a91a9181c0ccdd6976af84c2d` |

Como referência cruzada, os digests finais de concatenação dos bytes brutos são `d0188654f44d6af29ac8185171d1e117cc89fb24a2d3bb50799b33a9a134c18e` para a extensora e `7ca20419b87ae6854b8f1f49aac329e1f30850f23c6072cf872d858b4645a630` para o afundo; os outros cinco permanecem na tabela histórica acima. A evidência em `output/leg-animations-review/digests-final.json` contém ambas as fórmulas para todos os movimentos.

**Conclusão desta etapa: PASS visual para os sete ciclos identificados acima, congelados para codificação e posterior verificação dos formatos de distribuição.**
