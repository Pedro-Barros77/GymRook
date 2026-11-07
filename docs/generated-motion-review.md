# Revisão visual do piloto suavizado — rosca inversa

Revisão de 6 de novembro de 2026. Esta avaliação é visual e limitada a imagens estáticas; não certifica anatomia, biomecânica, prescrição ou execução correta.

## Material inspecionado

- `output/generated-motion/reverse-cable-curl/contact-sheet.jpg`.
- A folha das nove âncoras estabilizadas, `anchors-contact.png`.
- Quadros PNG reais 11–13, 17–19, 23–25, 29–31, 35–37, 71–72 e 1–2.
- Metadados de preparação e interpolação, incluindo origem das âncoras, progressão pela altura da barra e 72 amostras a 24 fps.

O ciclo usa as poses ascendentes da folha original e retorna por essas mesmas imagens, em ordem inversa. Não usa os quadros de retorno redesenhados separadamente da folha original.

## Resultado prático

**Não identifiquei um artefato visual grosseiro que impeça disponibilizar este teste como opção explícita, mantendo o GIF original como padrão.** Isso não equivale a aprovar a demonstração como guia técnico nem a recomendar a promoção automática da versão suavizada.

Nas amostras inspecionadas:

- Não apareceram braços adicionais, duplicação evidente do tronco ou uma segunda barra separada.
- A barra continua visualmente reconhecível e a ligação principal do cabo permanece contínua.
- A torre e a base apresentam enquadramento muito próximo entre os quadros. Não há o deslocamento grosseiro visto entre as poses de retorno independentes anteriores.
- Os quadros 35–37 se aproximam gradualmente da posição superior; a pausa aparente ali corresponde a uma mudança pequena de pose perto do extremo.
- Os quadros 71–72 e 1–2 reencontram a mesma postura baixa. Não observei uma troca abrupta para outro desenho da posição inferior.
- O modelo preserva a aparência musculosa e os materiais da versão gerada anterior.

## Diferenças residuais visíveis

1. **Conector da barra/cabo:** nos trechos 11–13 e 17–19, o pequeno engate metálico muda um pouco de espessura e contorno. Essa região já varia entre as âncoras; o intermediário suaviza a mudança, mas não reconstrói uma peça rígida de geometria comprovada.
2. **Mãos e empunhaduras:** há leve perda de nitidez nas bordas dos dedos durante algumas transições. Não contei dedos adicionais nas amostras examinadas, mas essa é uma área que merece inspeção ampliada e em movimento.
3. **Pele, roupa e detalhes do aparelho:** permanecem pequenas mudanças de contorno e sombreado herdadas das âncoras. A estabilização global não transforma esses detalhes em uma única cena física.
4. **Movimento percebido:** a inspeção de quadros não substitui assistir ao MP4 em velocidade normal e lenta. Não posso concluir por essa revisão estática que o tremor percebido ou toda mudança de velocidade foi eliminado.

O erro médio estático mostrado na folha de âncoras varia aproximadamente entre 1,7 e 4,2 unidades de intensidade de 8 bits, excluindo a referência com erro zero. Isso é diferença de imagem nas regiões escolhidas, não uma medida em pixels do deslocamento nem prova de estabilidade perfeita.

## Recomendação

Disponibilizar apenas na rosca inversa como **“Testar versão suavizada”**, com retorno fácil à versão original. O texto deve identificá-la como um experimento de estabilização e interpolação de imagens geradas. Não anunciar “execução validada”, “anatomia corrigida” ou “continuidade perfeita”.

Antes de torná-la padrão: assistir ao ciclo completo no celular, examinar mãos/engate/cabo em movimento lento, comparar com a fonte e submeter a trajetória a revisão técnica. Não aplicar automaticamente ao crucifixo, cuja perspectiva e geometria dos braços precisam de tratamento próprio.
