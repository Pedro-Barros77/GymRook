# Revisão da perspectiva do crucifixo — 7 de novembro de 2026

Escopo: somente coerência visual da orientação do personagem, banco/máquina e alavancas do crucifixo. Esta análise não valida anatomia nem execução técnica.

## Fontes conferidas

- `docs/generated-frames-v3/pec-deck-closed-reference.png`.
- As nove poses concêntricas em `docs/generated-frames-v3/pec-deck.png`, grade 3 × 3, índices 0–8 na ordem de leitura.
- `output/pec-deck-v3/contact.png`, montagem do candidato de animação.

## Veredito de perspectiva

**Aprovado para o ajuste de orientação solicitado.** A pose fechada agora aponta para a direita da imagem, acompanhando a direção de rosto, banco e pernas. As mãos fechadas se projetam à direita do esterno. As duas alavancas terminam adiante nessa mesma diagonal, em vez de convergirem para uma posição frontal diante da câmera.

Na referência fechada de 1254 px, o centro aproximado do esterno está em x=690 e o centro dos pegadores em x=925. O braço próximo avança aproximadamente de x=585 no pivô para x=880 no pegador; o afastado, de x=820 para x=950. Esses valores são estimativas visuais de projeção, não medidas tridimensionais.

Na folha, a pose final 8 mantém essa orientação. Considerando as coordenadas locais da célula de aproximadamente 418 px, o esterno fica perto de x=230, os pegadores próximos de x=290 e x=315; os pivôs ficam perto de x=198 e x=284. Assim, ambos os pegadores fechados estão à direita dos respectivos pivôs, e o centro das mãos está à direita do tórax.

As poses abertas e intermediárias preservam o eixo geral do conjunto. É esperado que o pegador próximo comece à esquerda do personagem na abertura e cruze em direção à diagonal frontal durante o fechamento; não seria correto exigir que ele estivesse à direita em todas as poses. Não identifiquei uma troca completa para uma máquina orientada de frente durante esse arco.

## Diferença residual a registrar

A passagem **7 → 8** tem deslocamento do pegador próximo muito maior que os passos anteriores: aproximadamente 60–70 px horizontais na célula, contra mudanças anteriores bem menores. A posição final está orientada corretamente, mas a distribuição das poses é desigual e ainda pode produzir um avanço brusco no último trecho. Não descrever este candidato como um ajuste de suavidade ou como animação plenamente contínua.

Se a suavidade desse trecho for tratada depois, usar a pose fechada atual como referência e criar intermediários específicos ou redistribuir o tempo; não retornar à pose frontal antiga para reduzir o salto.
