# Conteúdo do guia GymRook

Revisão editorial: 6 de novembro de 2026. Idioma principal: português brasileiro. Nomes dos exercícios e dos equipamentos também aparecem em inglês para facilitar a identificação na academia.

## Escopo e contrato

`dist/data.js` disponibiliza `window.GYMROOK_DATA`, com quatro treinos, 26 blocos e 31 movimentos distintos. Combinações ficam em um único bloco com vários `exerciseIds`, na ordem de execução. Cada movimento contém nome, equipamento, músculos principais/auxiliares, preparação, passos, dicas e erros comuns.

Os campos `restNote` e `safetyNote` são avisos gerais opcionais. Os arrays `primary` e `secondary` contêm nomes em português. `muscleIds` usa apenas as regiões do mapa acordado. Os realces são esquemáticos: não expressam porcentagens de ativação nem uma hierarquia quantitativa entre os músculos.

Existem quatro movimentos com mídia, distribuídos em três blocos piloto:

| Bloco | IDs dos movimentos |
| --- | --- |
| Supino inclinado | `incline-dumbbell-press` |
| Peck deck + flexão | `pec-deck`, `push-up` |
| Rosca inversa rest-pause | `reverse-cable-curl` |

Cada piloto aponta para `assets/animations/<id>.gif` e `assets/animations/<id>-poster.webp`. Os outros 27 movimentos têm `media: null` e `pilot: false`. A existência e a qualidade dos arquivos de mídia são verificadas pela etapa de produção visual. Nenhuma foto, GIF ou vídeo de exercício externo foi incorporado por esta etapa de conteúdo.

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
- **Infra:** sugestão de crunch reverso deitado, com joelhos dobrados. É uma escolha editorial para o movimento que não foi especificado; deve ser confirmada com o professor. A explicação enfatiza enrolar a pelve de forma controlada. A [descrição da ACE](https://www.acefitness.org/resources/everyone/exercise-library/76/reverse-crunch/) fundamenta esse padrão.
- **Anatomia abdominal:** supra e infra são nomes usuais de variantes. O reto abdominal tem continuidade; o guia não cria um músculo inferior separado. A [discussão anatômica da ACE](https://www.acefitness.org/continuing-education/prosource/august-2014/4934/can-you-train-upper-and-lower-abs-separately/) admite diferenças regionais de participação sem tratar as regiões como músculos independentes.
- **Máquina abdominal:** identificação provisória como crunch sentado. O aluno deve conferir o modelo real e a placa de instruções. O [manual da Life Fitness](https://kb.cybexintl.com/Product_Info/Life_Fitness_Circuit_Series_Machine_Use_Instructions.pdf) orienta o movimento controlado do tronco, mas seus ajustes específicos não foram generalizados para toda máquina.
- **Rosca Scott:** banco Scott com barra EZ é a referência do guia. A ficha não escolheu entre barra, halteres e máquina.
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
| [ACE — Reverse Ab Crunch](https://www.acefitness.org/resources/everyone/exercise-library/76/reverse-crunch/) | Referência para a sugestão de infra. |
| [ACE — Upper and Lower Abs](https://www.acefitness.org/continuing-education/prosource/august-2014/4934/can-you-train-upper-and-lower-abs-separately/) | Explicação anatômica de supra/infra. |
| [Life Fitness — Circuit Series Machine Use Instructions](https://kb.cybexintl.com/Product_Info/Life_Fitness_Circuit_Series_Machine_Use_Instructions.pdf) | Referência de crunch sentado; necessidade de identificar o modelo. |
| [NASM — Dumbbell Romanian Deadlift](https://www.nasm.org/resource-center/exercise-library/dumbbell-romanian-deadlift) | Conferência do movimento do quadril, carga próxima às pernas e controle da coluna. |
| [ACE — Exercise Library](https://www.acefitness.org/resources/everyone/exercise-library/) | Referência geral de terminologia e grupos musculares. |

Não foram usados textos de agregadores, fóruns ou resultados promocionais como fonte de autoridade. Uma página consultada de bench dips da NASM apresentava uma lista de músculos incompatível com o próprio movimento; essa lista foi descartada. A presença de uma fonte institucional não dispensa conferência crítica do conteúdo.

## Validação executada

Carregamento real de `dist/data.js` em Node com `window` simulado: quatro treinos, 26 blocos, 31 exercícios, 31 referências únicas, nenhuma referência ausente. Todos os movimentos possuem os campos de texto e os sete arrays previstos. Todos os IDs musculares pertencem ao contrato. Exatamente os quatro movimentos piloto possuem `media` e `pilot: true`.

A revisão editorial não certifica biomecânica de animações geradas. A publicação deve manter claro seu caráter ilustrativo e solicitar validação técnica do professor, especialmente em carga alta, falha e rest-pause.
