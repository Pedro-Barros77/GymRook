# Auditoria visual das folhas geradas

Revisão de 6 de novembro de 2026. Fontes: as quatro folhas de 16 poses em `docs/generated-frames-v2/`, grade 4 × 4, 1254 × 1254 px. Índices abaixo começam em zero e seguem a ordem de leitura. Cada célula tem aproximadamente 313,5 px; as regiões sugeridas são normalizadas e devem ser ajustadas depois do recorte.

Esta é uma auditoria de coerência visual para decidir um experimento de interpolação. Não valida biomecânica, prescrição ou segurança de execução. Interpolar uma sequência não corrige uma pose errada nem uma máquina com geometria inconsistente.

## Melhor primeiro piloto

**Rosca inversa na polia.** A sequência ascendente `0, 1, 2, 3, 4, 5, 6, 7, 8` mostra elevação visualmente monotônica da barra. A pessoa está em pé, o tronco tem pouca movimentação e existe uma torre estática com bordas retas úteis para estabilização. O movimento da carga selecionada também é visível.

Para fechar o ciclo, usar a volta exata dessas mesmas poses: `0 → … → 8 → … → 0`, sem usar as poses de retorno 9–15 geradas independentemente. Isso não exige duplicar um quadro parado: os novos instantes devem ser amostrados numa fase periódica suave, com velocidade chegando a zero nos extremos. A primeira pose não precisa ser repetida como último quadro.

As posições não são uniformemente espaçadas: a mudança entre 2 e 3 é visivelmente maior do que entre vários pares seguintes. Não tratar cada índice como um mesmo deslocamento. Medir a altura do centro da barra nos nove quadros e usar essa progressão como coordenada de movimento antes de distribuir 72 amostras em três segundos.

Problemas residuais da rosca: pequenas alterações da posição relativa entre rosto, tronco e torre; diferença de contorno e luz da pele; mudança da aparência dos suportes e dos detalhes da barra. Uma transformação global pode estabilizar a torre, mas não garantir que o corpo fique imóvel relativamente a ela. O resultado deve ser inspecionado quanto a punhos, cotovelos, dedos, cabo e barra, principalmente nos quadros intermediários inventados pelo interpolador.

## Regiões de ancoragem sugeridas

Retângulos no formato `(x0, y0, x1, y1)`, em frações da célula recortada. São áreas candidatas visuais, não pontos rastreados/medidos automaticamente nesta auditoria.

| Exercício | Área candidata | Retângulo aproximado | Observação |
| --- | --- | --- | --- |
| Rosca inversa | Travessa superior da torre | `(0.62, 0.01, 0.90, 0.09)` | Não contém braço nem bloco móvel. |
| Rosca inversa | Coluna externa direita | `(0.86, 0.10, 0.92, 0.87)` | Usar faixa estreita da estrutura, evitando o interior da torre. |
| Rosca inversa | Base no chão | `(0.60, 0.89, 0.96, 0.99)` | Preferível como âncora principal a sapatos redesenhados. |
| Supino | Pé traseiro e longarina do banco | `(0.64, 0.75, 0.90, 0.89)` | Há mudança local da geometria; conferir resíduos depois do ajuste. |
| Supino | Apoio dianteiro do banco | `(0.27, 0.82, 0.45, 0.97)` | Pode combinar com a longarina para estimar translação/rotação pequenas. |
| Crucifixo | Base inferior da máquina | `(0.08, 0.85, 0.88, 0.99)` | Excluir os sapatos. Não resolve a perspectiva dos braços. |
| Flexão | Ponta do tênis à direita | `(0.90, 0.70, 0.99, 0.88)` | Pequena área; muda de contorno e orientação do pé. |

Evitar o bloco de pesos, cabos, pegadores, braços móveis e sombras variáveis na estimação do movimento global. Fundos claros quase uniformes não são bons pontos de ancoragem. O alinhamento deve usar várias estruturas estáticas e reportar erro residual, em vez de se apoiar apenas numa coincidência local de um sapato.

## Demais sequências

### Supino inclinado

Há uma diferença evidente entre as poses próximas da posição baixa no início e no fim da folha. O retorno 9–15 muda a relação dos braços/halteres com o tronco e não reencontra exatamente a pose inicial. Usar somente a ida e espelhá-la no tempo é o primeiro tratamento razoável para o recuo da emenda.

A seleção proposta `0, 1, 2, 3, 5, 6, 7, 8` pode evitar uma pose redundante, mas **não deve ser aprovada por índice sem medir separadamente os dois halteres**: a folha não representa uma única trajetória rígida perfeitamente uniforme e algumas mudanças incluem rotação da pegada e do tronco, não só subida. Para o experimento, preferir inicialmente 0–8 completos, medir as duas trajetórias e descartar um quadro somente se houver regressão comprovada. Menos quadros âncora criam intervalos maiores para o interpolador inventar.

O banco e o corpo também têm pequenas mudanças de escala/posição aparente. Fixar os pés não corrige uma alteração local do ângulo do encosto ou da forma do ombro. Classificação: segundo piloto possível, depois da rosca.

### Crucifixo máquina

É o candidato menos adequado para iniciar. A geometria aparente dos braços, suportes superiores e relação do banco/torre com o personagem muda ao longo da folha. A aproximação dos pegadores parece seguir uma abertura frontal, enquanto a orientação do conjunto sugere uma vista em três quartos. É uma inconsistência de desenho/perspectiva, não apenas tremor do recorte.

Congelar câmera/recorte ou aplicar homografia global não reconstrói os pivôs e o arco correto das alavancas. Interpolação provavelmente tornará essa mudança mais suave, preservando o erro de mecanismo e podendo dobrar detalhes retos. Exige uma nova base visual/poses corrigidas ou revisão específica das partes móveis antes de ser promovido como demonstração.

### Flexão

Sem equipamento, tem menos estruturas mecânicas para conflitar. Porém a elevação do tronco, inclinação do quadril, posição da cabeça e contorno dos pés não são idênticos entre poses visualmente equivalentes de ida/volta. O retorno exato da ida também ajuda aqui. Dedos e contato com o chão são regiões de alto risco para borrões/duplicações de fluxo óptico. É um teste alternativo simples, mas oferece menos âncoras estáticas de alta qualidade que a rosca.

## Critérios para avaliar o experimento

1. Comparar lado a lado original e interpolado, com enquadramento e velocidade controlados.
2. Confirmar que a torre/base fica estável e que a estabilização não desloca o corpo artificialmente.
3. Examinar as nove poses originais preservadas e os intermediários novos. Mais quadros não substituem revisão da trajetória.
4. Rejeitar dedos extras, duplicação de cabo/barra, cotovelos que dobram no sentido errado, mudança de pegada e interpenetração.
5. Conferir a emenda do loop e os extremos em velocidade normal e lenta.
6. Manter o piloto interpolado como experimento até aprovação visual e técnica; o guia principal pode continuar usando as fontes anteriores preservadas.
