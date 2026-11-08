# Conteúdo do guia GymRook

Revisão editorial: 8 de novembro de 2026. Idioma principal: português brasileiro. Nomes dos exercícios e dos equipamentos também aparecem em inglês para facilitar a identificação na academia.

## Escopo e contrato

`dist/data.js` disponibiliza `window.GYMROOK_DATA`, com quatro treinos, 26 blocos e 31 itens de consulta com demonstrações distintas. Combinações ficam em um único bloco com vários `exerciseIds`, na ordem de execução. Cada item contém nome, equipamento, músculos principais/auxiliares, preparação, passos, dicas e erros comuns.

Os campos `restNote` e `safetyNote` são avisos gerais opcionais. Os arrays `primary` e `secondary` contêm nomes em português. `muscleIds` usa apenas as regiões do mapa acordado. Os realces são esquemáticos: não expressam porcentagens de ativação nem uma hierarquia quantitativa entre os músculos.

Os 31 movimentos têm demonstração em MP4 a 12 fps, GIF de compatibilidade e pôster. A prancha mostra uma postura isométrica estável. Os primeiros quatro pilotos eram:

| Bloco | IDs dos movimentos |
| --- | --- |
| Supino inclinado | `incline-dumbbell-press` |
| Peck deck + flexão | `pec-deck`, `push-up` |
| Rosca inversa rest-pause | `reverse-cable-curl` |

As mídias atuais apontam para `animations-v4`, `animations-v3`, `animations-v2`, `animations-bc-v1` ou `animations-d-v1`, conforme a revisão. Todos os itens têm `media` e `pilot: true`. Fontes anteriores ficam preservadas. Nenhuma foto, GIF ou vídeo de exercício externo foi incorporado ao guia.

## Ajustes seguintes solicitados em 7 de novembro

- A Scott passa para uma máquina seletorizada: nome, equipamento PT/EN, preparação e execução acompanham o aparelho. O banco Scott com barra EZ fica somente no histórico. Os cotovelos alinham ao eixo e os braços ficam apoiados; a posição da pegada segue o formato do aparelho.
- O esclarecimento seguinte diferencia **supra** (crunch do tronco, `floor-crunch`) e **infra** (elevação das pernas deitado, `lying-leg-raise`). A duplicação do supra foi removida. Os endereços antigos `reverse-crunch` e `regular-crunch` abrem o infra por compatibilidade; não há compartilhamento de vídeo entre os dois itens.
- A sequência continua com 20 supra + 20 infra + prancha, por duas voltas. O infra é ilustrado com as duas pernas juntas, joelhos suavemente flexionados e cabeça/ombros apoiados. O texto distingue a ação dos flexores do quadril da estabilização abdominal, sem criar um músculo abdominal inferior separado. Referência: [ExRx — Lying Straight Leg Raise](https://exrx.net/WeightExercises/HipFlexors/BWStraightLegRaise).
- O supino inclinado foi restaurado para os arquivos originais de `animations-v2`, sem recodificação. Por pedido explícito, essa demonstração fica encerrada para novas alterações. A confirmação SHA está em `generated-frames-v4-followup/supino-restore-preflight.json`.
- A panturrilha em pé usa uma máquina inclinada, com peito voltado para o aparelho e calcanhares livres para descer abaixo do apoio do antepé e depois subir. Em 8 de novembro, o usuário confirmou essa versão: em pé, com o corpo inclinado para a frente, de frente para a máquina. A máquina sentada com anilha horizontal permanece separada e inalterada. Referência de arquitetura: [Atlantis M318](https://atlantisstrength.com/gym-equipment/m318). Os ângulos visuais pedidos não foram convertidos em uma amplitude anatômica obrigatória para todos.
- O abdominal sentado usa alças altas junto ao pescoço/ombros. Texto e equipamento acompanham a nova arquitetura; assento e apoio lombar permanecem fixos, enquanto o conjunto superior acompanha a flexão do tronco.
- O afundo mantém 12 fps e passa a um ciclo de seis segundos e 72 quadros, com tempo de retorno comparável ao de saída. Isso altera a apresentação visual, não o número de repetições prescrito.
- O botão de reprodução usa SVG de play e pausa com duas barras. O nome acessível e o estado pressionado continuam correspondendo à reprodução.

## Substituições solicitadas em 7 de novembro

- `stair-calf-raise` foi substituído por `seated-plate-calf-raise`: panturrilha sentada na máquina com anilhas, mantendo 20 repetições após as 15 em pé e três voltas. Texto, equipamento e ilustração mudam juntos. O mapa distingue sóleo principal e gastrocnêmio secundário, com regiões curvas próprias; o sóleo é profundo e aparece pelas bordas da panturrilha no desenho de superfície. Referências: [Life Fitness](https://www.lifefitness.com/en-eu/catalog/strength-training/plate-loaded/life-fitness-calf-raise) e [ACE](https://www.acefitness.org/continuing-education/prosource/september-2014/4975/best-exercises-for-great-legs-and-pain-free-knees/).
- `unilateral-converging-row` foi substituído por `unilateral-cable-row`: remada unilateral sentada na polia baixa, com cabo de aço e pegador individual. Mantém três séries de dez por lado e 30 segundos entre lados. A carga depende do controle do tronco; não se presume equivalência de peso entre aparelhos.

Na tabela abaixo, a coluna registra a ficha recebida antes dessas duas substituições.

## Ficha preservada

Os números, a ordem, os aumentos de carga e as combinações foram mantidos. Textos de execução e identificação foram acrescentados para explicar a ficha.

| Treino | Programação recebida |
| --- | --- |
| A — Peito e bíceps | Supino inclinado com halteres a 45°: 4 × 10, carga crescente; crossover diagonal na polia alta: 4 × 15; peck deck + flexão: 4 × (12 + falha); rosca na polia: 3 × 15; Scott: 3 × 8–12; rosca inversa rest-pause: 2 séries, carga alta, cada uma com 4 blocos de 5 e 10 s entre blocos; supra 20 + infra 20 + prancha máxima, 2 voltas. |
| B — Ombros e panturrilhas | Desenvolvimento na máquina: 3 × 10, carga crescente; elevação lateral com halteres: 4 × 15 + 1 isometria no pico até a falha; frontal na polia: 3 × 12; encolhimento com halteres: 3 × 20; crucifixo inverso na máquina: 4 × 12; panturrilha em pé na máquina 15 + no degrau 20, 3 voltas. |
| C — Costas e tríceps | Puxada alta: 4 × 12, carga crescente; remada convergente unilateral: 3 × 10, carga alta, 30 s entre lados; remada baixa: 20/15/12/10/8, carga crescente; tríceps corda: 3 × 12; tríceps testa com halteres: 3 × 15; tríceps no banco: 3 × 20; abdominal na máquina: 3 × máximo. |
| D — Pernas | Extensora: 10 × 10; hack: 4 × 8–10; mesa flexora: 3 × 12; stiff com halteres: 3 × 10; abdutora + adutora: 3 × (10 + 10); afundo alternado: 2 × 10 por perna. |

Descanso informado: revezar entre três amigos; se o revezamento for rápido, no máximo um minuto. Esse intervalo permanece identificado como o relato da ficha. A recuperação efetiva depende da execução, carga e orientação individual. Os 10 segundos do rest-pause e os 30 segundos entre lados da remada ficam separados do descanso geral.

## Escolhas e pontos a confirmar

- **Supra:** referência de crunch no solo, com joelhos dobrados e pés apoiados.
- **Infra:** elevação das pernas deitado, conforme o esclarecimento posterior. A sugestão de crunch reverso e a duplicação do crunch tradicional ficam somente no histórico.
- **Anatomia abdominal:** supra e infra são nomes usuais de variantes. O reto abdominal tem continuidade; o guia não cria um músculo inferior separado. A [discussão anatômica da ACE](https://www.acefitness.org/continuing-education/prosource/august-2014/4934/can-you-train-upper-and-lower-abs-separately/) admite diferenças regionais de participação sem tratar as regiões como músculos independentes.
- **Máquina abdominal:** identificação provisória como crunch sentado. O aluno deve conferir o modelo real e a placa de instruções. O [manual da Life Fitness](https://kb.cybexintl.com/Product_Info/Life_Fitness_Circuit_Series_Machine_Use_Instructions.pdf) orienta o movimento controlado do tronco, mas seus ajustes específicos não foram generalizados para toda máquina.
- **Rosca Scott:** máquina seletorizada, conforme substituição solicitada. A orientação usa braços apoiados, cotovelos alinhados ao eixo e pegada compatível com o aparelho ilustrado.
- **Elevação frontal:** referência bilateral com barra curta na polia baixa, de costas para a polia. O acessório e a posição original permanecem a confirmar.
- **Puxada e remada baixa:** barra longa pronada e triângulo neutro são referências visuais/textuais; as pegadas originais não foram detalhadas.
- **Afundo:** referência alternada com passo à frente. Direção, carga e eventual uso de halteres precisam ser confirmados.
- **Isometria lateral:** o texto mantém “4 × 15 + 1 isometria”. Não determina que se faça uma sustentação após todas as quatro séries, porque isso acrescentaria volume não indicado. O momento dessa única sustentação permanece a confirmar.
- **Stiff:** mantém esse nome e sua tradução como `Dumbbell stiff-leg deadlift`. A instrução admite pequena flexão estável dos joelhos e amplitude individual. A referência de RDL citada abaixo serve para conferir o padrão de movimento do quadril, sem equiparar automaticamente todos os detalhes das duas variantes.
- **Falha/máximo:** a ficha conserva as palavras originais. A orientação para aprendizado usa perda da técnica como limite de execução; isso é explicitado no glossário.
- **Peck deck:** preservada a grafia comum da ficha em português. O nome técnico inglês é `pec deck`. Máquinas com alças e com apoio dos antebraços exigem ajustes diferentes.

## Fontes de conferência

A pesquisa foi textual e focada em execução, nomenclatura e nas escolhas em aberto. As fontes não validam a programação individual nem as demonstrações geradas. O restante do texto é uma síntese editorial concisa de padrões usuais de treinamento, sujeita à revisão de um profissional de educação física.

| Fonte primária/institucional | Uso nesta revisão |
| --- | --- |
| [ACE — Incline Chest Press](https://www.acefitness.org/resources/everyone/exercise-library/25/incline-chest-press/) | Banco inclinado, apoio dos pés e do tronco, controle dos halteres e punhos. |
| [ACE — Pec deck e crossover](https://www.acefitness.org/certifiednewsarticle/2884/ace-sponsored-research-top-3-most-effective-chest-exercises/) | Padrão de fechamento dos braços e controle da abertura. As classificações de eficácia do artigo não foram reproduzidas como promessa de resultado. |
| [NASM — Push-up](https://www.nasm.org/resource-center/exercise-library/push-up) | Alinhamento do corpo, ação dos cotovelos e músculos envolvidos. |
| [ACE — Crunch](https://www.acefitness.org/resources/everyone/exercise-library/52/crunch/) | Aproximação entre costelas e pelve e volta controlada. |
| [ACE — Upper and Lower Abs](https://www.acefitness.org/continuing-education/prosource/august-2014/4934/can-you-train-upper-and-lower-abs-separately/) | Explicação anatômica de supra/infra. |
| [Life Fitness — Circuit Series Machine Use Instructions](https://kb.cybexintl.com/Product_Info/Life_Fitness_Circuit_Series_Machine_Use_Instructions.pdf) | Referência de crunch sentado; necessidade de identificar o modelo. |
| [NASM — Dumbbell Romanian Deadlift](https://www.nasm.org/resource-center/exercise-library/dumbbell-romanian-deadlift) | Conferência do movimento do quadril, carga próxima às pernas e controle da coluna. |
| [ACE — Exercise Library](https://www.acefitness.org/resources/everyone/exercise-library/) | Referência geral de terminologia e grupos musculares. |

Não foram usados textos de agregadores, fóruns ou resultados promocionais como fonte de autoridade. Uma página consultada de bench dips da NASM apresentava uma lista de músculos incompatível com o próprio movimento; essa lista foi descartada. A presença de uma fonte institucional não dispensa conferência crítica do conteúdo.

## Validação executada

Carregamento de `dist/data.js` em Node com `window` simulado: quatro treinos, 26 blocos, 31 exercícios, 31 referências únicas, nenhuma referência ausente. Todos os movimentos possuem os campos de texto, os arrays previstos e demonstrações. A revisão dos cards e mapas confere a ênfase do sóleo na nova panturrilha sentada. As verificações técnicas não certificam execução ou anatomia.

A revisão editorial não certifica biomecânica de animações geradas. A publicação deve manter claro seu caráter ilustrativo e solicitar validação técnica do professor, especialmente em carga alta, falha e rest-pause.
