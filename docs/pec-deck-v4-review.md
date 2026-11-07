# Revisão independente do crucifixo v4

Revisão em 7 de novembro de 2026. Escopo: perspectiva, progressão das mãos, continuidade visual do aparelho e artefatos dos quadros produzidos. Esta inspeção não valida anatomia nem execução do exercício.

**Parecer atual: a terceira montagem PASSA na revisão visual de perspectiva e continuidade para apresentação ao usuário.** Os ghosts de mão/pegador do quadro 5 e os fragmentos de rosto na borda da alavanca do 19 foram corrigidos. Restam pequenas ondulações locais nos trilhos/metal da abertura e uma faixa tonal suave acima das placas; não são duplicação de membros nem transparência ampla do aparelho. Este parecer não declara perfeição física nem validação da execução.

## Terceira montagem: interpolação híbrida e correções locais

Saída atual conferida: `output/pec-deck-v4/frames/frame_0001.png` a `frame_0072.png`, 512 × 512, 24 fps, três segundos. MP4: SHA-256 `8ec7810e2332021af636db5a5a7af64f3fcd37b82366cd009354d522682cd2e1`. O relatório de construção continua marcando a saída como experimento de continuidade visual; execução humana não validada.

O primeiro intervalo, 00→early-small, foi interpolado com **Google FILM TFHub v1**; os demais usam **Practical-RIFE 4.25**, escala 1. FILM usa fase quantizada em 1/64 neste processamento, com seis tarefas registradas, incluindo a extremidade. O retorno reutiliza os PNGs em ordem inversa.

O quadro 19 recebeu um recorte de imagem gerada e já alinhada para reparar somente a borda da alavanca: região `[268,70,293,150]`, 25 × 80 px, com margem suavizada de 1 px. O relatório registra 1.975 pixels diferentes e erro zero fora da região. O quadro de volta 55 reutiliza a mesma correção. As regiões de corpo/mãos fora dela não são alteradas por essa operação. Os PNGs anteriores à composição/correção continuam em `output/pec-deck-v4/raw-frames/`.

A camada dos pesos mantém o mesmo recorte de nove placas. A margem superior foi ampliada para 40 px na referência de 1254 px, com transição de 10 px, aproximadamente 4 px na saída. Isso suaviza a emenda anterior sem apagar a mão inicial que passa na frente da torre.

### Conferência da saída atual

Todos os 37 quadros de ida foram novamente inspecionados em folha ampliada de tronco/aparelho e em grade de mãos. Foram abertos individualmente 4, 5, 6, 12, 18, 19 e 20 e ampliados os trechos de abertura, oclusão do rosto e pesos. Evidências atuais em `.cache/qa-pec-deck-v4/`: `hybrid-upper-37.jpg`, `hybrid-hands37.png`, `hybrid-early.png`, `hybrid-face.png` e `hybrid-weight-crops.png`.

- Em 4–5, há agora uma única mão envolvendo um único pegador opaco. O ghost e a mistura de dois pegadores que reprovavam a segunda montagem não aparecem.
- Em 19, a alavanca oculta a face com uma borda limpa; os fragmentos de pele/feição na borda direita foram removidos. 18→19→20 mantém a progressão da oclusão, sem metal amplamente transparente.
- A direção diagonal para a direita e o avanço dos dois pegadores permanecem ao longo da sequência, com fechamento desacelerado e sem o salto final dominante da v3.
- O bloco selecionado conserva nove placas, espaçamento e textura; sobe ao fechar, enquanto a base inferior permanece parada. A faixa tonal acima dele é agora suave. Ainda é perceptível com ampliação, portanto não foi rotulada como invisível.
- Na abertura, há pequenas ondulações locais dos trilhos e do contorno metálico atrás do pegador, mais claras na ampliação de 4–5. O conjunto permanece único e opaco; esse residual é menor que os defeitos que reprovaram as tentativas anteriores. Não foi medido como subpixel nem tratado como prova de rigidez física perfeita.

O script QA encontra os dois eixos dos pegadores nos 37 PNGs; não detecta reversões de x superiores a 0,75 px. O retorno é pixel-exato, com erro médio absoluto zero para os pares espelhados. Dados em `hybrid-final-review.json`. Os limites dessas medidas continuam os descritos abaixo: não são uma validação anatômica nem profissional.

Os indicadores de pixels da terceira montagem são: primeiro passo/máximo ≈0,0594; último/máximo ≈0,00431; máximo/mediana ≈2,762. Os limites automáticos passam. O primeiro passo é maior que na segunda montagem após a troca para FILM, mas continua pequeno frente ao movimento máximo; a inspeção não mostrou um salto amplo no fechamento ou na passagem do loop. O loop não foi avaliado em navegador físico nesta revisão, apenas nos PNGs e em suas diferenças.

**Decisão da terceira montagem:** pode ser apresentada como a nova versão de perspectiva/continuidade, acompanhada da descrição honesta de que é uma ilustração gerada com pequenos resíduos visuais. Não a descrever como execução/anatomia clinicamente ou profissionalmente validada.

## Histórico: segunda montagem com Practical-RIFE 4.25

Saída rejeitada, preservada em `output/pec-deck-v4-practical-first/`, 512 × 512, 24 fps, três segundos. Quinze referências, Practical-RIFE 4.25, escala 1. MP4 desta tentativa: SHA-256 `f48d8f7de081bf1bf130d5e456128f84719693b196190753bba697045562cd70`.

Foram inspecionados todos os 37 quadros de ida em uma folha ampliada do tronco/aparelho e outra dedicada às mãos. Quadros 4–9, 12 e 16–23 foram ampliados individualmente, com recortes adicionais da passagem da alavanca pelo rosto. A volta é cópia exata dos quadros de ida em ordem inversa; os defeitos também voltam.

### Problemas restantes

| Quadros | Fontes e fase efetivas | Achado |
| --- | --- | --- |
| 4–5, pico 5 | 00 → early-small; t≈0,331 e 0,586 | O pegador próximo dobra; em 5 aparecem duas posições semitransparentes do pegador/mão e os trilhos de fundo entortam. O defeito é visível na imagem de 512 px, não apenas com ampliação extrema. 6 já está limpo. |
| 19 | 04 → pre-cross-tiny; t≈0,682 | A borda direita da alavanca junto ao rosto fica irregular, com fragmentos de feição/pele na transição. É menor que a transparência ampla da primeira montagem, mas a oclusão ainda deforma localmente o metal. 18 e 20 são mais limpos. |
| Faixa acima das placas, por exemplo 12 e 19 | Composição determinística dos pesos | O topo variável da máscara cria uma emenda horizontal de tom nos trilhos/fundo antes do bloco. A contagem das placas está estável; esta é uma questão de integração da faixa. |

Evidências em `.cache/qa-pec-deck-v4/`: `dense-upper-37.jpg`, `dense-hands37.png`, `dense-early-ghost.png`, `dense-face-occlusion.png` e `dense-weight-crops.png`.

A correção da abertura pode concentrar-se no par 00→early-small: uma referência com o próximo perto de x370, entre x346 e x393, reduziria novamente a lacuna, ou pode-se testar outro interpolador somente nesse par. Na passagem pelo rosto, uma referência entre 04 e pre-cross-tiny precisa manter a alavanca opaca e rígida. Essas são propostas para nova tentativa, não garantias de resultado.

A emenda da camada de pesos merece tratamento local de borda. Estender uma máscara retangular fixa até o topo da torre apagaria a mão/alavanca inicial que passam na frente dos trilhos; essa não é uma solução aceitável.

### O que melhorou e o que os números demonstram

A diagonal frontal para a direita é preservada ao longo das quinze fontes e da saída. O movimento avança desde a abertura; não fica parado até um último quadro corrigido. Os fechamentos examinados mantêm ambos os pegadores à direita do esterno, coerentes com a orientação do banco e do rosto. Nos quadros limpos, o metal oculta o rosto em vez de ficar amplamente transparente.

O script de QA `.cache/qa-pec-deck-v4/review_frames.py`, atualizado para a temporização bilateral atual, encontra os dois pegadores nos 37 PNGs e não detecta reversões de x superiores a 0,75 px. O resultado está em `dense-final-review.json`. O erro médio absoluto da volta contra os quadros correspondentes é zero. A medida automática ainda pode ajustar um eixo falso quando há um fantasma; ela não aprova o quadro 5 nem demonstra uma trajetória anatômica correta.

O relatório de construção registra razão do primeiro passo para o máximo ≈0,0050; último ≈0,00425; máximo para mediana ≈2,708. Os limites automáticos passam e o fechamento não tem o salto final dominante da v3. Esses números não detectam nem anulam os artefatos descritos acima.

A estabilização das referências estimou deslocamentos de centro menores que aproximadamente 0,6 px na saída. A inspeção não revelou o antigo deslocamento amplo da cena. As deformações locais do pegador/trilhos em 4–5 continuam presentes mesmo com registro global estável.

A camada dos pesos reutiliza um único recorte de nove placas da pose 08, deslocado verticalmente. Em ampliações dos quadros 1, 5, 12, 19, 24, 30 e 37, contagem, espaçamento e textura do bloco permanecem consistentes e a base inferior fica parada. O relatório registra erro zero fora do canal da composição e na base fixa. Isso resolve a variação de quantidade das placas das fontes, mas não resolve a emenda de borda nem o ghost acima da máscara.

## Referências e medidas

Seleção: **00 → early-small → 01c → mid-early-small → mid-small → mid-late-small → 03 → 04 → pre-cross-tiny → cross-small → 05b → late-far-tiny → 06 → 07 → 08**.

Fontes em `docs/generated-frames-v4/pec-deck/`, 1254 × 1254 px. Próximo é o pegador que começa à esquerda; distante, o que começa à direita. O y de contato foi escolhido visualmente; o x é uma estimativa do eixo do cilindro visível na altura da mão. As casas decimais são resultado de ajuste de linha, não precisão anatômica subpixel. Os dados completos estão em `.cache/pec-deck-v4-dense-landmarks.json`.

| Fonte | Próximo (x; y) px | Distante (x; y) px | Topo bruto das placas para apagamento |
| --- | --- | --- | --- |
| 00 | (346,10; 460) | (1088,00; 447) | 655 |
| early-small | (392,50; 460) | (1090,80; 447) | 619 |
| 01c | (422,10; 460) | (1070,80; 452) | 619 |
| mid-early-small | (460,66; 467) | (1071,76; 460) | 612 |
| mid-small | (515,77; 467) | (1073,04; 460) | 612 |
| mid-late-small | (552,56; 467) | (1066,49; 460) | 612 |
| 03 | (580,90; 466) | (1060,50; 457) | 613 |
| 04 | (634,90; 466) | (1049,20; 461) | 560 |
| pre-cross-tiny | (690,52; 473) | (1040,90; 470) | 563 |
| cross-small | (720,17; 473) | (1038,09; 470) | 563 |
| 05b | (736,10; 473) | (1016,40; 472) | 563 |
| late-far-tiny | (785,35; 473) | (999,60; 472) | 539 |
| 06 | (831,40; 473) | (986,50; 471) | 537 |
| 07 | (857,80; 473) | (983,70; 471) | 538 |
| 08 | (888,50; 464) | (954,40; 466) | 512 |

As pequenas excursões iniciais do distante (+2,8, +0,96 e +1,28 px no original) permanecem explícitas; não se afirma monotonia estrita das fontes. A maior lacuna do próximo é 55,62 px, aproximadamente 22,7 px na saída. No intervalo agregado 01c→mid-small o próximo anda cerca de 94 px enquanto o distante varia pouco; dividir esse intervalo em mais referências não comprova sincronismo físico. A projeção é não linear e estas imagens não foram validadas como mecanismo/exercício exatos.

## Histórico da primeira montagem rejeitada

A primeira montagem usava sete fontes (00, 01c, 03, 04, 05b, 06, 08) com RIFE 4.6. Seu MP4 tinha SHA-256 `33bc822f1d6507238499bb8aba3736552c53068aa6f0a53abfd5f1421189c26b`. Os 72 PNGs foram preservados em `output/pec-deck-v4-rife-rejected/`.

Foi rejeitada por duplicação de mão/pegador em 5–7; ghosts e aparente desconexão do pegador em 12–13; alavanca deformada em 16; e metal amplamente transparente sobre o rosto em 19–20. Os pares eram, respectivamente, 00→01c, 01c→03, 03→04 e 04→05b. A volta exata e a monotonia dos eixos também passavam nessa tentativa, sem eliminar as falhas visuais.

Na avaliação antiga da v3, o fechamento correto foi aceito como prova da sequência toda, apesar da mudança concentrada no último quadro. Esse critério foi descartado. A avaliação atual considera todas as poses e os PNGs realmente produzidos.

**Decisão histórica da segunda montagem:** foi rejeitada por 4–5 e 19, com a emenda da camada de pesos sinalizada para melhoria. A terceira montagem descrita no início deste relatório corrigiu os defeitos determinantes e foi novamente inspecionada antes de receber o parecer de aprovação visual. Esta revisão não certifica anatomia nem execução.
