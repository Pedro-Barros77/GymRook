# Dados pessoais no aparelho

O catálogo e as animações permanecem estáticos. O módulo `dist/store.js` armazena os registros pessoais em IndexedDB (`gymrook-personal`, versão 1, object store `records`), sem chamadas de rede. As atualizações do service worker não apagam esse banco.

O registro `state` contém `schemaVersion`, `updatedAt`, configurações de séries por exercício (`settings`), observações permanentes (`exerciseNotes`), sessões (`sessions`) e progressão (`progression`). Cargas usam quilogramas. `weights` é um array alinhado a `reps`: `[]` significa sem carga informada, e `null` permite uma lacuna antes de uma carga de outra série. Valores `null` no final são removidos. As configurações iniciais são três séries de dez repetições e nenhuma carga informada.

Uma sessão mantém o instante de início, o instante de término, o início do descanso atual e uma cópia independente das séries e conclusões. O descanso não altera o início do treino. Alterações de configuração durante uma sessão atualizam apenas aquele exercício e desmarcam somente as séries cujos valores mudaram. Sessões concluídas preservam seus valores anteriores.

A progressão tem uma entrada por exercício e dia local (`YYYY-MM-DD`). Uma nova edição no mesmo dia substitui o ponto daquele dia. Confirmar valores que já estavam salvos não altera a data de edição nem cria um ponto, mesmo em outro dia. A simples marcação de uma série e os timers também não criam pontos de progressão.

Todas as alterações fazem leitura, modificação e escrita na mesma transação IndexedDB. A memória só muda após a confirmação da transação. Abas concorrentes recebem notificações por BroadcastChannel; voltar o foco à janela também recarrega os registros. Cada exercício aceita até 30 séries, 10000 repetições e 10000 kg por série.

## Observações e horários

`getExerciseNote(exerciseId)` retorna a observação permanente ou texto vazio. `updateExerciseNote(exerciseId, text)` salva até 4000 caracteres de texto simples, preservando quebras de linha e espaços; texto vazio remove a anotação. O mapa `exerciseNotes` é independente das séries e da progressão, portanto excluir um ponto de carga não apaga a observação.

Cada exercício de uma sessão tem seu próprio campo `notes`. `updateSessionExerciseNote(exerciseId, text, expectedSessionId?)` altera apenas a sessão em andamento e verifica seu identificador dentro da transação. Quando o identificador é omitido, o método captura o treino ativo no momento da chamada, impedindo que uma gravação atrasada chegue a outro treino. Uma sessão nova começa com suas observações vazias, sem copiar o texto permanente ou o texto de um treino anterior. Sessões concluídas conservam suas observações. Nenhuma gravação de observação cria um ponto no gráfico ou muda a configuração de séries.

`finishSession(expectedSessionId?)` aceita o identificador mostrado na confirmação de término. Se outra aba já trocou o treino ativo, a gravação é recusada em vez de finalizar esse outro treino. A chamada sem argumento continua compatível com versões anteriores.

`updateSessionTimes(sessionId, {startedAt, endedAt})` corrige os horários de um treino concluído. Os valores devem ser datas ISO com fuso explícito, dia e horário existentes e término igual ou posterior ao início. Datas futuras e treinos que atravessam a meia-noite são permitidos, sem restrição de sobreposição com outras sessões. Os horários são normalizados para UTC; exercícios, cargas, conclusões, observações e progressão não mudam. O treino em andamento não pode ser editado por esse método.

Esses campos são adições ao formato existente: `schemaVersion`, `formatVersion` e a versão do banco permanecem em `1`. Backups e registros anteriores sem `exerciseNotes` ou sem `session.exercises[id].notes` são aceitos e normalizados para mapa vazio e texto vazio, respectivamente.

## Exclusão de registros

`deleteSession(sessionId)` exclui apenas o treino concluído identificado. Outro treino no mesmo dia continua no calendário. O treino em andamento não pode ser excluído por esse método, e a exclusão de uma sessão não altera as configurações nem os pontos de progressão.

`deleteProgression(exerciseId, date)` exclui somente o ponto daquele exercício e dia. As configurações atuais voltam ao ponto restante mais recente, ordenado por dia e horário de edição. Sem pontos restantes, o exercício volta a três séries de dez repetições, sem carga informada. Essa restauração não cria um novo ponto de progressão.

Se o exercício estiver no treino em andamento, a configuração restaurada também passa a valer nessa sessão. Apenas as séries cujos valores mudaram perdem a marcação de conclusão. Os valores de sessões já concluídas permanecem intactos. Alvos inexistentes, identificadores inválidos e datas inválidas geram erros; falhas de gravação mantêm os registros anteriores.

## Exportação e importação manuais

O aplicativo salva os registros de treino automaticamente em IndexedDB, mas não cria arquivos nem cópias de backup automáticas. Para guardar uma cópia fora do navegador, o usuário escolhe exportar seus dados. A interface baixa o JSON retornado por `exportBackup()`; o navegador ou o sistema determina o destino do arquivo.

**Limpar os dados do site pode apagar os registros locais.** A solicitação de armazenamento persistente reduz a chance de remoção automática quando o navegador a concede; uma exportação manual permite guardar uma cópia independente.

O JSON exportado é `{ "app": "GymRook", "formatVersion": 1, "exportedAt": "ISO", "state": { ... } }`. A importação aceita arquivos de até 20 MB e valida todo o conteúdo antes de substituir os dados, incluindo identificadores, datas, limites de séries, valores numéricos, duplicatas e no máximo uma sessão ativa. `validateBackup(json)` permite fazer essa verificação completa antes da confirmação na interface. A interface deve informar que importar substitui os dados atuais antes de chamar o método.

Se IndexedDB abre, mas o registro atual está inválido, `ready` rejeita sem apagar esse registro, `canRestore()` retorna `true` e `getInitializationError()` informa a falha. Nesse caso, `importBackup(json)` continua disponível para recuperação a partir de um arquivo exportado; depois da importação, recarregue a página para inicializar novamente a interface e os eventos. Se o próprio banco não abre, `canRestore()` retorna `false`.

Na primeira abertura após uma versão que mantinha backups automáticos, a aplicação remove apenas os registros obsoletos `daily-backup`, `backup-meta`, `external-file` e `backup-lease` do seu banco e tenta remover o antigo arquivo privado `gymrook-backup.json`. O registro principal `state` e os arquivos externos que o usuário havia vinculado permanecem intactos. Essa limpeza ocorre somente quando há registros antigos; perfis novos não acessam OPFS.

## Verificação

`node scripts/check-store.mjs` exercita sessões e retomada, timers de descanso, cargas opcionais, conclusões, progressão por dia, falha de transação, exportação e importação manuais, recuperação de estado inválido e gravações concorrentes em duas instâncias. Verifica observações permanentes e de sessão, limite de texto, gravações atrasadas para outra sessão, confirmação de término com identificador, compatibilidade com dados antigos e correção de horários com validação de calendário. Verifica exclusões de sessões e de pontos antigos, intermediários, mais recentes e de toda a progressão de um exercício, incluindo restauração de configuração, proteção do treino ativo, preservação de outros registros, recarga e falhas atômicas. Também verifica que treinos não criam backups e que a limpeza de cópias antigas preserva o estado principal e arquivos externos. A simulação transacional não substitui testes em um navegador real.
