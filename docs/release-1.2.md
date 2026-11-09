# GymRook 1.2

Publicação de 9 de novembro de 2026.

- Botão **Iniciar treino** verde com play em SVG e **Finalizar treino** vermelho com stop quadrado em SVG.
- Botão vermelho com lixeira para excluir cada treino finalizado, com confirmação que identifica a ficha, data e horário. Outras sessões do mesmo dia permanecem no calendário.
- Botão vermelho com lixeira para excluir os ajustes de um dia de um exercício. O gráfico é atualizado e a configuração atual passa a ser a do último ajuste restante. Se nenhum ajuste restar, volta ao padrão de três séries de dez e nenhuma carga registrada.
- Sessões já finalizadas preservam suas cargas, repetições e conclusões quando ajustes são excluídos. O treino em andamento recebe a configuração restaurada e mantém a conclusão apenas nas séries que não mudaram.
- As exclusões são transacionais, informam erros de gravação e preservam a data/filtro selecionados na interface.

O catálogo, as animações e a exportação/importação manual permanecem disponíveis. O site não inclui dados demonstrativos nem os insere automaticamente nos navegadores.

Verificação: testes do armazenamento e da interface cobrem cancelamento, exclusão, recarga, falhas de gravação, sessões no mesmo dia, restauração da configuração anterior, exclusão de todos os ajustes e preservação de outros exercícios. O teste opcional de navegador usa um perfil isolado do Edge com interface de 360 px.
