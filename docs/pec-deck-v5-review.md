# Auditoria estrutural do crucifixo — v4 e v5

7 de novembro de 2026. Esta revisão substitui o parecer de continuidade da terceira montagem v4: **a v4 está REPROVADA em continuidade estrutural**. A avaliação anterior verificou mãos, transparência e trajetória, mas deixou passar o desaparecimento de uma peça fixa e não demonstrou rigidez das alavancas. O usuário identificou corretamente esse limite. Corpo, estilo, perspectiva e 24 fps já foram aceitos; esta auditoria se concentra no equipamento.

Não é validação anatômica ou profissional de execução do exercício.

**Parecer final: APROVADO visualmente no escopo de perspectiva, continuidade estrutural e integração do equipamento.** O candidato aprovado é o de digest `f80dd9538e59e20105b05d915fbe7409272c5261e0614044f07bd0bf3b428d56`. Nenhum digest anterior recebeu esta aprovação completa. O histórico abaixo registra os defeitos encontrados e corrigidos, sem misturá-los com a saída final.

## Saída final congelada para codificação

São 72 PNGs de 512 × 512, destinados a três segundos a 24 fps, com retorno espelhado exato. O identificador acima é o SHA-256 da concatenação dos **bytes** dos hashes SHA-256 dos 72 arquivos em ordem; não é o hash de um MP4. A codificação deve usar esses PNGs sem alterá-los.

A aprovação combina a revisão completa de 37 quadros/36 transições do CONX com as revisões focadas e os testes de identidade das correções posteriores. Corpo, coluna, alavancas, pivôs e conexões já aprovados permaneceram preservados. O último reparo foi uma cobertura efetiva explícita da antiga borda antialias, limitada a `[145,45,180,86]`: máscara binária com margem de dois pixels de Chebyshev nessa região e recorte canônico limpo. As máscaras originais foram preservadas e as efetivas versionadas em `docs/generated-frames-v5/pec-deck/effective-tower-masks/`.

No candidato final foram vistos os doze recortes da viga, especialmente 4–11, e novamente os PNGs integrais de 1, 4, 5, 6, 8, 10 e 12. A antiga linha diagonal e as pequenas ilhas claras desapareceram; a superfície fixa do capô/viga fica lisa e coerente com a referência. Não foi identificado novo defeito material aparente nessa região. Evidências `.cache/qa-pecdeck-v5/brace-final/effective1-12.png` e `effective-pixel-check.json`.

O teste independente `verify_unoccluded_tower.py`, executado com as máscaras efetivas, confirma em **todos os 72 PNGs**:

- erro RGB zero na torre visível onde máscara antiga efetiva =0 e alpha do novo aparelho =0, contra a base v4;
- erro zero fora do ROI da torre e nos pixels opacos das novas peças, contra o CONX já conferido;
- erro zero em y164–511 contra a base v4;
- erro zero no retorno espelhado e zero cobertura de máscara fora do ROI.

O equipamento mantém a coluna inteira e a identidade das peças curvas; as conexões não apresentam as abas antigas nem as fendas que reprovaram os candidatos anteriores. As emendas da torre, retângulos acima dela, hachuras e contornos antigos que motivaram as últimas rejeições foram resolvidos no escopo inspecionado. Essa conclusão vem da inspeção dos pixels e das superfícies inteiras, não apenas de hashes ou trajetórias das mãos.

**Pode seguir para a codificação autorizada, mantendo congelado o digest final.** A aprovação é da continuidade visual da ilustração; não certifica um aparelho comercial específico, anatomia ou execução profissional do exercício. Esta auditoria não alterou os ativos da aplicação.

## Primeiro candidato v5: estrutura corrigida, composição reprovada

Foi conferida a montagem de `output/pec-deck-v5/frames/`, com 72 PNGs, cujo primeiro quadro tem SHA-256 `2b79e276ed550e605fad3e78e9af83a255a0b1dc03d12eb02f1f7c155242352c`. O digest SHA-256 da concatenação ordenada dos 72 hashes é `80e066c76d22a2ad4456f343fee7037429d1de4d712ed7ecd41057f66746de32`. Esses identificadores distinguem este candidato de uma eventual revisão no mesmo diretório; não se trata de um MP4 já aprovado.

Foram inspecionadas todas as 37 posições de ida em regiões de coluna, carcaças superiores, alavancas inteiras e colares, além das **36 sobreposições anterior/atual a 50%**. Também foram abertos individualmente 1, 12, 16–20, 23, 28 e 37. Evidências atuais em `.cache/qa-pecdeck-v5/`: `v5-fullupper-37.jpg`, `v5-post-37.jpg`, `v5-caps-37.jpg`, `v5-collars-37.jpg`, `v5-onions-02.jpg` e `v5-onions-20.jpg`.

### Estrutura que melhorou

- A coluna está presente em todos os 37 quadros. O teste do interior protegido descrito abaixo retorna **zero pixels claros em todos eles**, inclusive 11–14. Oclusão pela nova alavanca não é apagamento da coluna.
- As duas peças novas mantêm um perfil curvo único durante a rotação e não adquirem a concavidade em S das fontes antigas. As sobreposições de posições sucessivas mostram deslocamento da mesma forma, sem criar uma segunda curva intermediária. A metainformação de malha fixa/yaw é coerente com a observação; o hash sozinho não foi o critério de aprovação visual.
- Carcaças/pivôs superiores e seus detalhes pretos permanecem fixos. Não foi identificado um fragmento preto se soltando dessas carcaças nos 37 quadros. A junção de colar/pegador abaixo delas é um problema separado, descrito a seguir.

### Falhas de integração que impedem a promoção

| Região | Achado material | Evidência |
| --- | --- | --- |
| 17, aproximadamente `[234,85,246,147]`; 18, `[240,80,256,149]` | Uma fita da alavanca **antiga** sobrevive à esquerda da nova, cruzando cabelo/orelha/pescoço. O resultado volta a mostrar duas peças em parte do trajeto. | `v5-face-and-old-edge.png`, `old-metal-retention.png` e `old-metal-retention.json` |
| Colar próximo, por exemplo 12 e 23–37; em 37 aproximadamente `[347,152,357,160]` | Há uma aba prata/marrom do colar antigo à esquerda da anilha nova. O cleanup para em y155, enquanto parte desse objeto antigo ocupa y155–160. | `v5-near-collar-details.png` |
| Faixa horizontal da torre em y≈155, principalmente 12 e 20 | A área superior recomposta encontra a base com uma diferença visível de tom. É uma emenda de exposição, não uma peça fixa que deveria mudar de cor. | Imagens integrais 12/20 e grade `v5-fullupper-37.jpg` |

A retenção de metal antigo foi verificada também por pixels: nas duas ROIs de 17 e 18, respectivamente **96 e 175 pixels de cinza médio continuam idênticos byte a byte à base v4 e estão fora da alpha da alavanca nova**. A seleção auxiliar usa diferença entre canais <35 e média RGB entre 75 e 210; a identificação como peça antiga foi conferida na imagem e na sua silhueta. Não são uma sombra calculada pela nova malha. O overlay vermelho marca esses pixels sem alterar o ativo.

A remoção apenas por cor neutra não garante que a silhueta antiga inteira desapareça: reflexos escuros/tintados ficaram de fora. A correção deve considerar o objeto antigo completo, descontar a cobertura do objeto novo e reconstruir o fundo/cabeça exposto de forma consistente. A máscara local de colar pode alcançar y163 mantendo y164+ protegido; não se deve estender uma remoção retangular sobre o corpo inteiro.

O pequeno recorte claro ao lado do queixo em 22–23 foi notado, mas **não foi tratado como defeito comprovado**: parte dessa área pode ser fundo legítimo após a nova oclusão. Não remover pele nem retocar essa região apenas por conjectura.

O conector escuro novo também termina com um degrau retangular sobre o cilindro antigo, inclinado em algumas poses. Isso é menor que a aba antiga remanescente, mas deve ser revisto ao integrar colar e pegador para que pareçam uma única conexão.

### Verificações independentes e parecer

O comparativo direto dos PNGs com o backup v4 encontrou **erro máximo zero abaixo de y164**. O retorno é pixel-exato, erro médio absoluto zero. Esses resultados e os hashes estão em `v5-candidate-1-pixel-audit.json`. Preservar o corpo e repetir a volta não remove os objetos antigos que sobreviveram acima dele.

**Parecer do candidato v5 nº1: REPROVADO como mídia final.** A coluna e a geometria das alavancas novas atendem ao problema estrutural observado, mas as duas peças antigas parciais, o colar residual e a faixa de exposição precisam ser integrados antes de nova revisão. Nenhum ativo de aplicação foi modificado por esta auditoria.

### Correção intermediária: verificação pontual, sem parecer final

Depois do primeiro candidato, a limpeza foi ampliada para o metal sombreado junto à cabeça e para as zonas dos colares até y163. A revisão pontual dos quadros 17 e 18 confirma **zero pixels no mesmo teste de cinza antigo idêntico à v4 fora da nova alavanca**. A fita cinza desapareceu também na inspeção visual. Referências desta verificação: quadro 17 SHA-256 `82d7aa39e0cdc45ca6ac1417d4e4ea6d5e10c83e450a6a44ad46f2982d115576`; quadro 18 `880c6afcefe231f61f48d30df9e743b6cbbf391714d39e02b10458fb57cd375e`. Evidências `post-cleanup-head-check.json` e `post-cleanup-head-check.png`.

Os recortes de colar em 12, 17, 18, 23, 28 e 37 também mostram que a aba antiga foi removida. Essa etapa expõe uma pequena fenda de fundo/pele entre o conector novo e o cilindro existente, aproximadamente em y164–166, além do desalinhamento lateral tardio já encaminhado para ajuste. Evidência `post-cleanup-collar-check.png`. A ligação precisa ser contínua em x **e** em y depois de ajustar o encontro do colar com a haste.

Esta é somente uma confirmação dos reparos localizados, não uma aprovação da composição completa. A faixa de exposição não foi reapresentada como defeito atual sem nova conferência: sua observação acima permanece ligada ao primeiro digest. A nova variante final deverá receber revisão de todos os 37 quadros e transições.

## Candidato CONX e histórico do material conferido

### Candidato CONX congelado: revisão completa dos 37 quadros

O candidato seguinte foi identificado independentemente pelo digest SHA-256 dos **bytes** dos 72 hashes ordenados: `8f44dacdf05d08dd193eeb370f628edfe31562bddd7726a77884e6f0d601000b`. O primeiro PNG tem hash `e7a081ba64b7f4a78b52df699be87e783ca0817c0e35e251ec86946ed017b31e`. Não confundir esse cálculo com o digest de strings hexadecimais usado para identificar a primeira tentativa.

Todos os **37 quadros de ida** foram inspecionados novamente nas regiões inteiras de equipamento/coluna/colares e todas as **36 transições** foram vistas em sobreposição anterior/atual a 50%. Foram ampliados separadamente 12, 17, 18, 19, 20, 23, 28 e 37. As imagens e os testes desta revisão ficam em `.cache/qa-pecdeck-v5/finalconx/`.

Os reparos determinantes de estrutura e conexão passam:

- A coluna permanece presente; o teste de fundo claro no interior esperado retorna zero em todos os 37 quadros.
- As alavancas mantêm o mesmo perfil curvo, sem formação de S nem bifurcação nas intermediárias. A posição do conjunto permanece coerente com a perspectiva aceita.
- A fita da peça antiga em 17–18 foi removida: o teste de pixels antigos retidos retorna 0/0 e os recortes visuais estão limpos.
- Os colares e cilindros agora têm uma ligação contínua, sem abas antigas nem a fenda exposta pela correção intermediária. Foram conferidos ambos os lados nos 37 recortes; os detalhes de 1, 12, 25 e 37 confirmam a conexão junto à linha y164.
- O comparativo com a base v4 confirma erro máximo zero em y164–511. A volta é byte-exata/pixel-exata para os quadros correspondentes. Isso está documentado em `pixel-audit.json`.

**O único impedimento visual identificado nesta revisão completa é a faixa da torre em y≈155.** Foi conferida de novo neste digest, não apenas herdada da primeira tentativa. Os quadros 12 e 20 mostram mudança de tom e pequenos entalhes na passagem dos trilhos pela fronteira do patch; 37 não mostra a mesma emenda. Evidência atual `tower-seam-current.png` e valores em `tower-seam-current.json`.

Um exemplo mensurável no quadro 20: em `(160,154)` o RGB atual é `(54,51,50)`; em `(160,160)`, `(72,68,65)`. A base v4 nessa mesma região ia aproximadamente de `(74,69,66)` para `(72,68,65)`. A composição escureceu a parte de cima e voltou ao tom da base em poucos pixels junto à borda. As amostras não medem o aparelho inteiro; sustentam a emenda visível no recorte atual.

**Parecer do CONX `8f44…000b`: estrutura, remoção das peças antigas e conexões aprovadas visualmente; promoção global pendente da integração da faixa da torre.** Não executar uma nova geração de corpo nem reabrir os reparos de colares para resolver esse item. A próxima revisão pode se concentrar nessa região, confirmar o mesmo restante congelado e revalidar os pixels de proteção/espelho.

### Tentativa de correção da torre `83f126…de78`: reprovada

Digest completo dos bytes dos 72 hashes ordenados: `83f126d677a1bef9709938892d4709cda9f403b4377dc95147020f01a3a5de78`. O escopo foi comprovado independentemente: **erro máximo zero fora de x124–179/y0–163** em todos os 72 PNGs, erro zero nos pixels totalmente opacos das novas alavancas e retorno pixel-exato. Assim, não há motivo para reabrir as correções de coluna, cabeça e conectores para tratar este defeito.

A antiga emenda em y155 melhorou nas amostras críticas, mas a transformação por coluna alterou regiões que não eram trilhos expostos:

- Linhas verticais artificiais aparecem sobre o capô da torre em 1–16.
- Em 12–15 o fundo acima da torre ganha manchas/retângulos brancos e cópias das linhas. O quadro 12 é o mais claro: 1.873 pixels na região x124–179/y0–49 diferem em mais de dez níveis de RGB do CONX anterior.
- A comparação independente do agente de montagem também identificou uma nova fronteira em y130 no quadro 12: em x138, o pixel de y129 é `(193,186,182)` e o seguinte é `(255,252,252)`. Essa região deveria continuar como trilho claro, não ganhar um novo corte.

Foram conferidos os 37 recortes de torre, os 37 recortes do topo inteiro e individualmente 1, 4, 5, 6, 7, 8, 12 e 20. Evidências em `.cache/qa-pecdeck-v5/tower-final/`: `tower37.png`, `early1-8.png`, `top37-new-artifacts.jpg`, `top37-new-artifacts.json` e `scope-independent.json`.

**Parecer: NÃO promover nem codificar `83f126…de78`.** O próximo reparo deve preservar o fundo/capô CONX onde não existe uma faixa a corrigir e trabalhar apenas nas superfícies reais da torre. Não deslocar a emenda para outra linha nem copiar trilhos sobre o fundo acima do equipamento.

### Máscaras de silhueta e preenchimento temporal `2b6ed3…935e`

As 37 máscaras de peça antiga foram conferidas contra as fontes reais v4: os primeiros doze overlays, recortes com grade e os detalhes de 11/12. Incluem silhueta, colar e borracha antiga até y163; 13–37 são vazias, coerentes com a peça já fora dessa região. A coluna x180 foi removida para respeitar o ROI exclusivo `[124,0,180,164]`; a cobertura começa em y56 ou abaixo e não alcança o fundo acima do equipamento. As máscaras foram aceitas como candidatas de composição, não como aprovação antecipada dos pixels reconstruídos.

Digest do composto temporal: `2b6ed33b26b004d3113c8c658c67477d17baa69aafcaf59c78afe327a532935e`. O script independente `verify_unoccluded_tower.py` foi executado sobre os 72 PNGs e as máscaras congeladas no projeto. Retornou zero em todos estes itens:

- RGB diferente da v4 em pixels de torre onde máscara antiga =0 e alpha do novo aparelho =0;
- pixels alterados fora do ROI em relação ao CONX;
- alteração dos pixels opacos do aparelho em relação ao CONX;
- alteração em y164–511 em relação à v4;
- erro de espelhamento da volta;
- cobertura das máscaras fora do ROI.

Dados em `.cache/qa-pecdeck-v5/temporal-final/pixel-check.json`. Os 37 recortes da torre, os 37 do topo e as aberturas 1–8 foram inspecionados, além dos PNGs integrais 1, 6, 10, 12 e 20.

A faixa em y155, a fronteira em y130 e os retângulos brancos acima da torre não aparecem nessa montagem. Porém, o preenchimento por vizinho temporal produz **linhas pretas/cinzas em pente ou checkerboard na viga fixa atrás da alavanca**, aproximadamente x157–179/y60–83 nos primeiros quadros. É mais evidente em 1–4 e migra até cerca de 10. Também é visível no PNG integral de 512 px. A superfície correspondente na referência 08 é lisa; essa textura não é um detalhe legítimo da carcaça.

Evidências em `.cache/qa-pecdeck-v5/temporal-final/`: `top37.jpg`, `tower37.jpg` e `early1-8.jpg`. A revisão independente do agente de montagem identificou o mesmo achado. Escolher um pixel de um frame cuja máscara está zerada não prova que ele esteja livre de borda antialias, sombra ou resíduo do objeto antigo. A reconstrução dessa superfície fixa precisa de um recorte canônico limpo ou de doadores com margem de oclusão mais conservadora, sem alterar o fundo visível fora da silhueta.

**Parecer do temporal `2b6ed3…935e`: NÃO promover.** Os testes de preservação e o conserto das emendas passam, mas o novo preenchimento da viga fixa ainda apresenta um defeito aparente. Não é necessário reabrir corpo, coluna ou conexões aprovados; a próxima revisão pode se concentrar nesses pequenos buracos de fundo.

### Recorte canônico da viga: borda antiga ainda fora da máscara

O recorte canônico local removeu o checkerboard no candidato `7a01f67bedaf0efae21afa0cdfd477530e9a442fe6057abd576327a23fa50373`, mas deixou uma linha residual clara/escura que acompanha a antiga peça em 1–10. Ela não é a borda física do capô: a referência canônica e a fonte 08 são lisas nesse ponto. A comparação está em `.cache/qa-pecdeck-v5/brace-final/canonical-donor-comparison.png`.

Uma tentativa seguinte, `538520e3f0103e07b5747c1e7430c1e7e831b6e56fd64dc05d07029c722beba9`, substituiu integralmente o fundo apenas onde a máscara já era positiva. Corrigiu o exemplo `(156,72)` do quadro 1, mas não alcançou pixels da borda antiga que estavam fora da silhueta anotada:

- Quadro 4, `(172,65)`: máscara antiga =0, alpha nova =0, RGB atual e v4 `(151,145,144)`, enquanto o fundo canônico é `(67,63,61)`.
- Quadro 5, `(172,69)`: máscara antiga =0, RGB atual e v4 `(157,149,147)`, fundo canônico `(68,63,61)`.

Os dois candidatos permaneceram sem aprovação. O teste de preservação passa justamente porque a máscara subestimada classifica esses pixels misturados da peça antiga como fundo visível. Essa é uma limitação da segmentação, não motivo para ignorar a linha na inspeção.

Medidas em `residual-boundary-pixels.json` e `residual-mask-distance.json` mostram que os resíduos relevantes de 4–11 estão a até dois pixels de distância de Chebyshev da cobertura atual, na região `[145,45,180,86]`. A margem proposta para a tentativa seguinte deve ser explícita em máscaras efetivas versionadas: binarizar e expandir somente nesse pequeno trecho, mantendo as máscaras originais e a justificativa. A preservação deve então ser conferida contra a cobertura efetivamente revisada, sem afrouxar o teste de pixels.

### Material original v4

Saída v4 híbrida, 72 PNGs de 512 × 512, com 37 posições de ida e volta exatamente espelhada. MP4 identificado por SHA-256 `8ec7810e2332021af636db5a5a7af64f3fcd37b82366cd009354d522682cd2e1`. Foram novamente inspecionados **todos os 37 quadros de ida**, por regiões de coluna e ambas as alavancas, e comparados com as **quinze fontes originais de 1254 × 1254**. Há também sobreposições de cada quadro com o anterior e com a abertura.

As duplicações nas imagens de onion skin são intencionais da sobreposição; não devem ser confundidas com ghosts presentes no PNG final.

Evidências em `.cache/qa-pecdeck-v5/`:

- `post37.png` e `post15-originals.png`: coluna em todos os quadros/fontes.
- `post08-coordinates.png`: grade de coordenadas sobre a referência completa.
- `post-presence.json`: contagem objetiva de fundo claro no interior esperado da coluna.
- `near-15-originals.png` e `far-15-originals.png`: geometria das duas alavancas nas quinze fontes.
- `near-onion-01.jpg`, `near-onion-19.jpg` e `near-onion-37.png`; equivalentes `far-*`: todos os quadros contra o anterior.
- `onion-01.jpg`, `onion-13.jpg`, `onion-25.jpg`: sobreposições mais amplas contra a abertura.
- `structural-guide.json`: ROIs, polígono da coluna e marcos visuais para a correção.

## 1. A coluna superior desaparece

A peça é o montante vertical cinza entre o conjunto superior do pivô e o topo arredondado do encosto. Ela é fixa e deveria permanecer por trás da alavanca. O fundo claro nos quadros defeituosos **não é uma oclusão legítima**: há uma área exposta onde a coluna deveria continuar e que não está coberta pelo braço da máquina.

| Material | Diagnóstico |
| --- | --- |
| Fontes `pose-mid-early-small.png` e `pose-mid-small.png` | A parte superior da coluna já foi apagada na imagem gerada. |
| Ida 11–14 | A coluna some/é erodida durante a passagem por essas fontes; 12 é o exemplo mais claro. |
| Ida 1–10 e 15–37 | A coluna volta a aparecer; os testes abaixo não encontram o mesmo fundo claro no interior protegido. |
| Volta 60–63 | Repetem, em ordem inversa, os defeitos da ida 14–11. |

ROI de inspeção na saída de 512 px: **`[193,35,248,111]`**. Teste em um interior protegido da coluna: **`[212,57,231,87]`**, 19 × 30 = 570 pixels. Conta-se fundo quase branco (mínimo RGB >220 e diferença entre canais <25) onde a referência completa mostra metal cinza. A contagem é auxiliar e foi conferida visualmente; não é uma segmentação universal de todo o equipamento.

| Quadro de ida | Pixels claros no interior esperado, de 570 |
| --- | ---: |
| 11 | 315 |
| 12 | 546 |
| 13 | 480 |
| 14 | 224 |
| Todos os outros 33 quadros | 0 |

Nas originais, `mid-early-small` tem 546 pixels claros e `mid-small` tem 445; todas as outras treze fontes têm zero nesse recorte. Portanto, o defeito nasce na geração das referências e a interpolação o propaga. Trocar apenas o interpolador não restaura a peça ausente.

### Referência completa e área para recomposição

**Referência preferida: `pose-08.png`**, a mesma fonte fechada usada como referência de registro da v4. `pose-00.png` também mostra a coluna completa. O quadro 37 é útil para conferir o alinhamento na saída.

Polígono conservador do trecho visível, em 512 px: **`[(209,58),(234,58),(234,88),(210,91)]`**. Em 1254 px: aproximadamente `[(511,90;142,05),(573,12;142,05),(573,12;215,53),(514,34;222,88)]`.

Esse polígono evita copiar a carcaça superior móvel do pivô e termina junto à borda do encosto. A coluna deve ficar **atrás da alavanca e atrás do encosto**. Não colar um retângulo sobre o braço da máquina, o cabelo, o rosto ou o encosto. Os limites acima são uma proposta de composição; o resultado deverá ser inspecionado, sobretudo em 11–17.

## 2. A alavanca próxima muda de perfil

ROI de toda a peça prateada próxima, sem as mãos: **`[125,25,375,164]`**, em 512 px. A região distante é **`[315,31,460,164]`**.

O perfil próximo muda de um braço com um joelho/curva principal na abertura para uma peça com concavidade e reversão lateral em **S** nas intermediárias. Essa forma já existe em `mid-early-small`, `mid-small`, `mid-late-small` e `03`, portanto também não é exclusivamente um erro de flow. A transição é visível no quadro 11; a região problemática da saída é **12–17**, especialmente **13–16**. Após isso, o perfil volta a avançar para a direita e se aproxima do braço da referência fechada.

Uma projeção 2D pode mudar a aparência de uma peça 3D. Sem um modelo/câmera mecânicos, esta revisão não afirma que toda diferença de contorno é matematicamente impossível. O problema é que **não foi preservado nem comprovado um único objeto rígido**: cada fonte redesenha a curva e a largura da peça. O conjunto de referências não pode continuar sendo aceito só porque os pegadores andam na direção correta. Uma composição com perfil controlado deverá evitar que o tubo/placa ganhe e perca curvas internas.

Marcos visuais aproximados para comparação (erro estimado de até cerca de 3 px na saída):

| Fonte | Parafuso lateral visível | Joelho/curva | Centro do colar |
| --- | --- | --- | --- |
| 00 | (237;40) | (148;99) | (142;146) |
| 03 | (229;40) | (209;90) | (237;148) |
| 04 | (232;40) | (242;89) | (259;148) |
| 08 | (241;40) | (348;101) | (358;151) |

O parafuso visível muda de lado/posição na carcaça entre as fontes; ele **não é automaticamente o eixo fixo de rotação 3D**. Os centros aproximados das carcaças superiores fixas são próximo `(239;31)` e distante `(335;40)`. Usar o parafuso lateral como pivô fixo sem essa distinção pode introduzir novo deslocamento.

A alavanca distante foi conferida nas quinze fontes e nos 37 quadros. Ela mantém uma curva principal, sem o mesmo desaparecimento de coluna ou mudança pronunciada para S. Mesmo assim, seus raios, larguras e trechos inferiores variam entre desenhos e não receberam uma certificação de rigidez. Deve entrar na mesma solução de geometria controlada; não foi declarada correta apenas por ter um defeito menos evidente.

## 3. Ordem de camadas e limites da correção

A coluna e demais peças fixas devem ter identidade estável. O encosto fica na frente da coluna; as alavancas próximas ficam na frente da coluna e, quando cruzam a cabeça, na frente do rosto. As mãos continuam na frente das regiões de pegada. A composição não pode alongar/deformar o corpo para encaixá-lo numa peça nova nem apagar uma mão para estabilizar o fundo.

Os nove pesos determinísticos da v4 resolvem um problema de identidade próprio do bloco; não provam continuidade do restante do aparelho. As pequenas ondulações dos trilhos da abertura 4–5 e a faixa acima dos pesos continuam itens separados a observar ao montar a v5.

## Critérios antes de um novo parecer

1. Conferir em todos os 37 quadros a permanência da coluna fora de oclusões explicitamente identificadas. A área exposta não pode voltar a virar fundo claro. Comparar com a peça canônica, e não só com o quadro anterior defeituoso.
2. Conferir ambas as alavancas em suas regiões inteiras: eixo superior, trecho de ligação, curva, largura, colar e cilindro. Identidade do perfil precisa vir do método de construção/transformação e da inspeção; monotonia das mãos não substitui esse critério.
3. Inspecionar 4–5, 11–17, 18–20 e as regiões fechadas, com sobreposições e imagens sem sobreposição. Onion skins mostram mudança, mas não permitem aprovar opacidade por si só.
4. Conferir as oclusões contra coluna, encosto, cabeça e mãos; só depois conferir suavidade, retorno exato e costura do loop.

**Parecer consolidado:** v4 e os candidatos intermediários identificados neste relatório foram rejeitados pelos respectivos defeitos. A saída final `f80dd953…28d56`, descrita no início, corrigiu os impedimentos observados e recebeu aprovação visual para codificação. O registro das falhas anteriores foi preservado para que uma reprodução futura não reutilize por engano um digest reprovado.
