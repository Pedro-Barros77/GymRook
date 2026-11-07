# Revisão visual da ficha B — animações v1

**Estado final da revisão PNG: os sete exercícios B estão aprovados para codificação no escopo piloto.** O crucifixo inverso foi aprovado na montagem final com três referências mecânicas intermediárias; o histórico abaixo conserva as tentativas rejeitadas e seus limites. O digest final desse ciclo é `2ed86eb0ec346a3337720109f5322b166797c1526a857fa1c83742678d47e10b`.

Revisão das ilustrações de 512 × 512, 36 quadros e 12 fps. Foram inspecionados os **19 quadros de ida de cada um dos sete exercícios** (133 posições) e as **18 transições consecutivas** de cada exercício (126 sobreposições a 50%). As imagens integrais 0, 4 e 8 das âncoras do crucifixo inverso também foram abertas separadamente para conferir a execução inicial, intermediária e final.

Os 17 quadros de volta de cada ciclo foram comparados byte a byte com as posições correspondentes da ida: todos são cópias exatas. Portanto, as transições de volta e as duas emendas dos extremos reutilizam pares de posições já conferidos. As duplicações nas grades de sobreposição são diagnósticas e não significam, por si, fantasmas no PNG de saída.

Esta é uma revisão visual de um piloto ilustrativo. Não certifica biomecânica profissional, rigidez matemática da máquina, amplitude individual ou o modelo comercial de equipamento encontrado na academia.

## Seis ciclos aprovados para codificação

| Exercício | Observação | Parecer |
| --- | --- | --- |
| Desenvolvimento na máquina | As mãos acompanham as alças, os braços pressionam acima da cabeça, tronco/pelve/pés permanecem apoiados. Pivôs, alavancas e peso carregado continuam identificáveis; nenhum membro extra ou peça fixa desaparecida foi identificado. | PASS visual no escopo piloto |
| Elevação lateral com halteres | Dois halteres acompanham a elevação dos braços até perto da altura dos ombros, com pequena flexão dos cotovelos. Sem impulso claro das pernas nem grande encolhimento dos ombros. A sustentação isométrica adicional permanece descrita no texto da ficha. | PASS visual no escopo piloto |
| Elevação frontal na polia | Barra sobe à frente, cabo permanece conectado ao acessório e à polia baixa atrás do corpo, peso carregado sobe. Sem transformação do movimento em rosca ou grande inclinação para trás. | PASS visual no escopo piloto |
| Encolhimento com halteres | Ombros e halteres sobem verticalmente, cotovelos permanecem quase estendidos. Não foi identificado círculo dos ombros ou inversão do braço. Pequena deriva gerada de superfície/proporções permanece, sem tremor grande da cabeça. | PASS visual no escopo piloto |
| Panturrilha em pé na máquina | Calcanhares sobem com antepés apoiados; joelhos permanecem quase estendidos. Existe uma subida pequena do corpo/yoke e movimento do peso carregado. A amplitude visual do corpo é modesta e não representa uma simulação mecânica exata. | PASS visual no escopo piloto |
| Panturrilha no degrau | Calcanhares sobem e descem mantendo apoio na borda do degrau; corpo continua alinhado e uma mão mantém o apoio no corrimão. Sem novo pé fantasma ou perda importante do apoio. | PASS visual no escopo piloto |

Há pequenas variações de textura e reflexo nas fontes geradas e nos intermediários. Elas não foram tratadas como motivo para reabrir os seis ciclos, pois não alteram materialmente o padrão do movimento neste piloto. A codificação dos GIFs/MP4s e a decodificação dos arquivos finais são verificações posteriores e separadas.

## Crucifixo inverso: primeira representação rejeitada

O ciclo mostra abertura horizontal dos braços e preserva a estrutura principal, sem um novo desaparecimento de coluna. Entretanto, na vista traseira elevada, a posição inicial parece ter cotovelos muito dobrados e a posição final parece quase estendida. A passagem pode ser interpretada como extensão dos cotovelos junto com a abertura dos ombros.

Uma projeção 2D de braços apontando para a frente pode acentuar muito a flexão aparente. Por isso esta revisão **não afirma ter provado uma alteração impossível do ângulo 3D**. O problema para o guia de iniciantes é que a imagem não demonstra de modo suficientemente claro a pequena flexão constante do cotovelo exigida pela instrução. Essa ambiguidade é material à execução e não equivale às pequenas variações de superfície aceitas nos outros exercícios.

**Parecer desta representação: não promover como demonstração final.** Recomenda-se gerar apenas esta fonte novamente em vista traseira de três quartos mais lateral, pouco elevada, deixando o braço próximo visível desde o ombro até o punho no começo da abertura. A mão deve estar à frente do tronco com o braço quase reto, e não em uma silhueta de U. O movimento deve continuar sendo a rotação no ombro com pequena flexão constante do cotovelo.

## Identificadores da montagem conferida

### Correções posteriores do crucifixo inverso — fontes ainda sem novo parecer de movimento

A tentativa `sheet-v3-side-candidate.png` torna o braço próximo mais visível no começo, mas o braço distante quase não abre. Ela não foi promovida. Foi gerado um endpoint aberto separado, `endpoint-open-v4-candidate.png`, usando o início da v3 como referência exata de câmera e a posição T traseira como referência do movimento.

Na câmera lateral, o braço próximo pode continuar projetado à direita da imagem ao abrir em direção ao observador; a aproximação e a perspectiva podem compensar a redução da projeção horizontal. A posição à direita, sozinha, não demonstra que o braço ainda aponta para a frente. O root aprovou testar esse par de endpoints porque o braço distante agora abre claramente e os dois braços mantêm pequena flexão aparente.

A folha gerada entre os endpoints (`sheet-v4-endpoints-three-arms-rejected.png`) conservou a antiga mão/alavanca distante enquanto adicionava sua versão aberta, produzindo três mãos em quadros intermediários. A edição textual seguinte também falhou. Uma edição com a região duplicada marcada em vermelho removeu essa duplicação das demais células intermediárias, mas a célula 2, no canto superior direito, ainda conserva a mão/alavanca extra.

O candidato `sheet-v6-annotated-repair-candidate.png` possui oito células visualmente utilizáveis: **0, 1, 3, 4, 5, 6, 7 e 8**. A célula 2 precisa ficar fora da montagem. Essa seleção está em `source-selection-v6-candidate.json`; a prova visual está em `output/animation-bc-qa/reverse-v6-eight-selected.png`. Ainda há um grande deslocamento do braço distante entre as primeiras poses fechadas e a primeira aberta; a cadência e os intermediários dessa seleção precisam de revisão antes da aprovação final. Nenhum novo ciclo do crucifixo inverso foi aprovado nesta seção.

**Correção da seleção anterior:** o root identificou na célula 1 um terceiro pegador/alavanca vazio à esquerda da cabeça, apesar de haver apenas duas mãos. A contagem anterior de mãos deixou esse objeto passar. Foram novamente ampliadas e contadas, separadamente, as mãos/braços e as alavancas/pegadores das células **0, 3, 4, 5, 6, 7 e 8**: essas sete passam com dois conjuntos completos. A seleção de oito células acima fica superada. A seleção de sete está em `source-selection-v6-seven-approved.json`, com prova `output/animation-bc-qa/reverse-v6-seven-selected.png`. Isso aprova as fontes selecionadas; ainda não aprova os intermediários ou a codificação.

### Interpolação da seleção de sete: dissolução material no trecho inicial

O novo ciclo de 36 PNGs tem digest binário `247406e0d671754e97cb736398cee81c7ce0d8803823d3ec32b8fdeffbafd37a`. Foram inspecionados novamente todos os 19 quadros de ida e as 18 sobreposições; os 17 quadros de volta são byte-exatos. O início foi aberto também em 512 px, quadros 5–9.

Os quadros 5–7 mostram a mão e a alavanca distante ficando pálidas/translúcidas na posição anterior. Em 7, a curva metálica permanece como um contorno quase branco contra o fundo claro; em 8 ela desaparece, antes de o braço/alavanca reaparecerem do lado esquerdo. A região aproximada de metal contra o fundo é `[285,60,344,161]`. Não há uma peça do corpo ou da máquina nessa área que explique o desvanecimento por oclusão. É uma dissolução da pose anterior durante o grande intervalo entre a fonte fechada e a primeira fonte aberta, não uma rotação rígida demonstrada com opacidade normal.

**Parecer deste novo digest: não promover ainda.** As fontes selecionadas corrigiram a terceira mão/alavanca, mas a interpolação criou uma falha de continuidade que não pode ser aprovada apenas pela contagem de membros nas âncoras. Evidência: `output/animation-bc-qa/reverse-v6-far-lever-fade.png` e `.json`; contato completo `output/bc-animations-review/reverse-pec-deck-v6-all19.png`. Os outros seis ciclos B permanecem aprovados e congelados.

Os valores abaixo são `SHA256(concatenação dos 36 hashes SHA256 em formato binário de 32 bytes, na ordem dos PNGs))`. Não são hashes de concatenação de strings hexadecimais nem hashes dos MP4s.

| ID | Digest | Estado |
| --- | --- | --- |
| `machine-shoulder-press` | `973c937d4303788faedd8129a5c39d44f11f6a8c6ad6d0afad99b5ccf2ffb5da` | Aprovado para codifica??o |
| `dumbbell-lateral-raise` | `c5582c2515464227a2ff0acac477f81366e4b0238296e8cb72a49a9693c714fb` | Aprovado para codifica??o |
| `cable-front-raise` | `39c715c82bcbb4a47b4d973c1f622dae5df28bdd4047a019c85777a0cdbd175e` | Aprovado para codifica??o |
| `dumbbell-shrug` | `5a9e9016c407cde9df21c4e7513a30457e035fafa2504269d1a61b0ed197ac10` | Aprovado para codifica??o |
| `reverse-pec-deck` | `2ed86eb0ec346a3337720109f5322b166797c1526a857fa1c83742678d47e10b` | Aprovado para codificação após a correção descrita abaixo |
| `standing-machine-calf-raise` | `ecdc6c01dc21cb902a86dc129bce84710c0a52a2233b0fdd98e2466f13a9a254` | Aprovado para codifica??o |
| `stair-calf-raise` | `d733edf7e90ddd53c19c69474cc64f7443aa581c67435b74b7778edf0b1a455b` | Aprovado para codifica??o |

Evidências: `output/bc-animations-review/<id>-all19.png`, `output/bc-animations-review/b-frames-digests.json` e `output/bc-animations/<id>/qa/transitions-onions.png`. Esses arquivos de diagnóstico ficam fora de `dist/`.

### Placa intermediária por composição de pixels das referências

A tentativa de gerar uma pose intermediária individual (`midpoint-v7-candidate.png`) retirou a mão/alavanca antiga, mas colocou a mão distante muito perto da primeira pose aberta. Ela não divide o intervalo inicial de modo suficiente. Para não gerar novamente a folha, a preparação técnica passou a usar essa imagem apenas como base limpa, com a peça metálica distante renderizada separadamente.

Em `docs/generated-frames-bc-v1/reverse-pec-deck/midpoint-native-v1/` foram entregues `clean-plate.png` RGB 512², `foreground-human-mask.png` binária 512² e o recorte RGBA de pele `hand-far-source.png`. A peça aberta à esquerda foi removida copiando pixels da célula 0 limpa da V6, alinhada pela base fixa (translação zero; correlação 0,9938). A região de substituição está registrada em uma máscara e no arquivo `composition.json`; fora dela os pixels da V7 são idênticos. A transição de 0,6 px mistura apenas as duas fontes. Foram alterados 6.833 pixels, sem pintar ou gerar anatomia.

A máscara humana contém cabelo, cabeça, pescoço, tronco superior e braço próximo; não contém máquina, encosto ou pegadores. O recorte da mão distante tem origem `[309,162]` e ponto de contato `[329,169]` no canvas 512², permitindo somente translação atrás da máscara humana. O script local `compose-clean-plate.py` reproduz a composição, e `composition.json` registra hashes de fontes, máscaras e saídas. A placa limpa e a máscara foram revisadas separadamente e disponibilizadas ao renderizador. Isso ainda não constitui aprovação do novo intermediário completo ou de seu ciclo.

### Aprovação final: referências mecânicas intermediárias e ciclo completo

A âncora central `midpoint-native-v1/midpoint.png` passou na revisão em 512². O digest dessa imagem é `a4df021f0560426a442744a055782b52ab324025814061349a04e6b1bd045a9d`. Os 12.927 pixels da máscara humana são byte-exatos em relação à placa limpa. A montagem acrescentou apenas 238 pixels mecânicos fora dessa máscara; o pegador e a mão distante ficam ocultos atrás da cabeça/ombro na projeção central. A verificação independente está em `midpoint-native-v1/qa/anchor-review.json`.

Para dividir novamente o deslocamento antes da interpolação, foram usadas mais duas projeções da mesma geometria rígida: `quarter-closed.png` e `quarter-open.png`. As três projeções reutilizam a mesma placa, máscara humana e recorte da mão. Não houve nova geração de imagem nem reconstrução humana em 3D. As duas referências também foram abertas em 512²: metal opaco, mão parcial ligada ao pegador quando visível e oclusão coerente quando passa atrás do humano.

A montagem final usa oito referências: célula V6 0 → quarter-closed → midpoint → quarter-open → células V6 3 → 4 → 5 → 8. O progresso é `[0,0.183735,0.36747,0.554217,0.740964,0.831325,0.927711,1]`. Foram inspecionados os **19 quadros de ida**, todos os recortes superiores e as **18 sobreposições**. Os quadros 5, 7, 10, 11, 12, 14, 16 e 19 também foram abertos integralmente em 512² para conferir opacidade, oclusão, reaparição e contatos das mãos. Os 17 quadros de volta são cópias byte-exatas das posições correspondentes da ida.

A alavanca distante agora se desloca solidamente até entrar atrás da cabeça; o trecho visível acima do cabelo permanece opaco e o pegador reaparece parcialmente à esquerda de forma coerente. Não foi identificado o desvanecimento contra o fundo claro observado na tentativa anterior, nem terceira mão/alavanca, inversão anatômica ou perda material do contato. Permanecem pequenas suavizações de contorno e diferenças de superfície nas transições entre fontes, aceitas para o piloto. Isso não equivale a uma simulação mecânica exata de um equipamento comercial.

**Parecer do ciclo final: PASS visual no escopo piloto; liberado para codificação.** Digest SHA256 de concatenação dos 36 hashes binários: `2ed86eb0ec346a3337720109f5322b166797c1526a857fa1c83742678d47e10b`. Evidências: `output/bc-animations-review/reverse-pec-deck-native-quarter-all19.png`, `reverse-pec-deck-native-quarter-upper19.png`, `reverse-pec-deck-native-quarter-digest.json` e `output/bc-animations/reverse-pec-deck/qa/transitions-onions.png`. O digest inicial rejeitado, anterior às correções, era `6c050aee1cbad70e6947a69b7297e9a35d97112864fed228b78da4f4c0e500b5`.
