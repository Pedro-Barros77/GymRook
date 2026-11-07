# Revisão visual das animações do treino C

Revisão de 7 de novembro de 2026. Escopo: continuidade e integração de um piloto ilustrativo colorido a 12 fps. Não é certificação profissional de biomecânica, execução nem de correspondência com uma máquina comercial específica.

## Material conferido

Foram vistos **todos os 19 quadros de ida dos sete movimentos** (133 posições), em contatos completos, e as **18 sobreposições entre vizinhos por exercício** (126 transições a 50%). As duplicações nas sobreposições são diagnósticas; não são fantasmas presentes nos PNGs de saída.

Os 17 quadros de retorno de cada ciclo foram comparados aos respectivos quadros de ida por igualdade dos bytes dos PNGs: quadros 20–36 reutilizam 18–2. Cada conjunto contém 36 PNGs de 512 × 512. A duração planejada é três segundos a 12 fps.

Além dos contatos, foram abertos integralmente os PNGs 9 da puxada alta, 15 e 19 do tríceps testa, 12 do mergulho, 15 do abdominal e 12 do tríceps corda, para conferir face/barra, antebraços/halteres, mãos/banco e contatos com o aparelho.

## Parecer por movimento

| Exercício | Achados no ciclo conferido | Parecer |
| --- | --- | --- |
| Puxada alta | Barra permanece à frente do rosto e desce ao alto do peito. Cabo conserva ligação central; bloco de peso sobe. Coxas, banco, pés e tronco continuam apoiados. Não foi identificada uma segunda barra ou membro extra nos intermediários. | Aprovado no escopo do piloto. |
| Remada convergente unilateral | Só o braço próximo executa a puxada. Braço e alça distantes permanecem estendidos, sem troca de lado; peito segue no apoio. A alavanca próxima acompanha o pivô sem formar uma nova curva impossível. | Aprovado no escopo do piloto. |
| Remada baixa | Pegador mantém contato com as duas mãos e com o cabo; desloca-se em direção ao abdômen. Pés continuam na plataforma e joelhos mantêm flexão suave. Não há grande balanço do tronco que transforme a ilustração em outro exercício. | Aprovado no escopo do piloto. |
| Tríceps na polia com corda | Cotovelos estendem, mãos permanecem nas pontas e a corda acompanha o movimento. A torre se mantém inteira e os pés não saltam. Não foram vistos punhos soltos nem corda duplicada no PNG final. | Aprovado no escopo do piloto. |
| Tríceps testa com halteres | A montagem usa somente as oito primeiras células aprovadas da fonte. Flexão dos cotovelos leva os halteres para perto da cabeça; o final rejeitado que girava os halteres não entra no ciclo. Nos 19 quadros não há rotação abrupta de 90°, antebraço invertido, peso atravessando o rosto ou halter extra. Existe pequena variação da posição dos braços superiores, aceitável nesta ilustração. | Aprovado no escopo do piloto, limitado às oito células selecionadas. |
| Tríceps no banco | Mãos continuam na borda do banco e pés apoiados; quadril desce próximo da borda enquanto os cotovelos flexionam. Banco e seus apoios permanecem estáveis. Não foi visto desprendimento das mãos, membro adicional ou mudança grande de anatomia. | Aprovado no escopo do piloto. |
| Abdominal na máquina | Pelve continua no assento, pés e rolos inferiores permanecem apoiados. A parte alta do tronco se aproxima da pelve com flexão visível; não é apenas um balanço grande do quadril. Almofada e alças acompanham o conjunto móvel, com torre e base preservadas. | Aprovado no escopo do piloto. |

Permanecem pequenas diferenças geradas de textura, reflexo e contorno entre as referências. Não foram identificados defeitos materiais de opacidade, membros extras ou desaparecimento de peças que exijam nova geração neste lote.

## Identidade dos PNGs aprovados

Fórmula usada: **SHA-256 da concatenação, em ordem de quadro 1 a 36, dos 32 bytes de cada hash SHA-256 do arquivo PNG**. Não é a concatenação de strings hexadecimais, nem o hash do MP4 ou dos pixels decodificados.

| ID | Digest aprovado |
| --- | --- |
| `lat-pulldown` | `30391ed7386dd3b203bd34232cf8c7cb0e9c83ae3a5edcd09efcc759580d73b6` |
| `unilateral-converging-row` | `b0ad7cb71b4d08cd2ed1f6afb64471a779f543f8d7bfefd59171242a40452ca8` |
| `seated-cable-row` | `724c0b714985dc358ba1fa2d62c68e9c73f1c4de7ca3540bd6432495792a784a` |
| `rope-triceps-pushdown` | `47cad6cf51176b5a8a8706cc22757c71357b877a24c5f5331f6853a0dd06ee20` |
| `dumbbell-lying-triceps-extension` | `7463b0d4b237453059e1d3001c4a5ab1277651c8480e5962405a20f279e284b6` |
| `bench-dip` | `33f2d925a4dbe8979a8cd3c6fc62ed2f89f1b0af2b092bed52c10d54ae3f9b19` |
| `machine-ab-crunch` | `77ab9ba90253d67d9d35ced12149638ae84248f35d49a53a86d562d60fe90af9` |

Evidências locais fora da distribuição: `output/bc-animations-review/<id>-c-all-19.jpg`, `<id>-c-onions-18.jpg` e `c-digests.json`. As métricas de costura são auxiliares; não substituíram a leitura das imagens.

**Parecer final: os sete conjuntos de PNGs acima estão aprovados visualmente para codificação.** Codificação, reprodução e integridade dos arquivos finais ainda devem ser verificadas separadamente, mantendo estes PNGs congelados.
