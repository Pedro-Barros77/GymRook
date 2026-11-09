# Dados pessoais no aparelho

O catálogo e as animações permanecem estáticos. O módulo `dist/store.js` armazena os registros pessoais em IndexedDB (`gymrook-personal`, versão 1, object store `records`), sem chamadas de rede. As atualizações do service worker não apagam esse banco.

O registro `state` contém `schemaVersion`, `updatedAt`, configurações de séries por exercício (`settings`), sessões (`sessions`) e progressão (`progression`). Cargas usam quilogramas. `weights` é um array alinhado a `reps`: `[]` significa sem carga informada, e `null` permite uma lacuna antes de uma carga de outra série. Valores `null` no final são removidos. As configurações iniciais são três séries de dez repetições e nenhuma carga informada.

Uma sessão mantém o instante de início, o instante de término, o início do descanso atual e uma cópia independente das séries e conclusões. O descanso não altera o início do treino. Alterações de configuração durante uma sessão atualizam apenas aquele exercício e desmarcam somente as séries cujos valores mudaram. Sessões concluídas preservam seus valores anteriores.

A progressão tem uma entrada por exercício e dia local (`YYYY-MM-DD`). Uma nova edição no mesmo dia substitui o ponto daquele dia. Confirmar valores que já estavam salvos não altera a data de edição nem cria um ponto, mesmo em outro dia. A simples marcação de uma série e os timers também não criam pontos de progressão.

Todas as alterações fazem leitura, modificação e escrita na mesma transação IndexedDB. A memória só muda após a confirmação da transação. Abas concorrentes recebem notificações por BroadcastChannel; voltar o foco à janela também recarrega os registros. Cada exercício aceita até 30 séries, 10000 repetições e 10000 kg por série.

## Exportação e importação manuais

O aplicativo salva os registros de treino automaticamente em IndexedDB, mas não cria arquivos nem cópias de backup automáticas. Para guardar uma cópia fora do navegador, o usuário escolhe exportar seus dados. A interface baixa o JSON retornado por `exportBackup()`; o navegador ou o sistema determina o destino do arquivo.

**Limpar os dados do site pode apagar os registros locais.** A solicitação de armazenamento persistente reduz a chance de remoção automática quando o navegador a concede; uma exportação manual permite guardar uma cópia independente.

O JSON exportado é `{ "app": "GymRook", "formatVersion": 1, "exportedAt": "ISO", "state": { ... } }`. A importação aceita arquivos de até 20 MB e valida todo o conteúdo antes de substituir os dados, incluindo identificadores, datas, limites de séries, valores numéricos, duplicatas e no máximo uma sessão ativa. `validateBackup(json)` permite fazer essa verificação completa antes da confirmação na interface. A interface deve informar que importar substitui os dados atuais antes de chamar o método.

Se IndexedDB abre, mas o registro atual está inválido, `ready` rejeita sem apagar esse registro, `canRestore()` retorna `true` e `getInitializationError()` informa a falha. Nesse caso, `importBackup(json)` continua disponível para recuperação a partir de um arquivo exportado; depois da importação, recarregue a página para inicializar novamente a interface e os eventos. Se o próprio banco não abre, `canRestore()` retorna `false`.

Na primeira abertura após uma versão que mantinha backups automáticos, a aplicação remove apenas os registros obsoletos `daily-backup`, `backup-meta`, `external-file` e `backup-lease` do seu banco e tenta remover o antigo arquivo privado `gymrook-backup.json`. O registro principal `state` e os arquivos externos que o usuário havia vinculado permanecem intactos. Essa limpeza ocorre somente quando há registros antigos; perfis novos não acessam OPFS.

## Verificação

`node scripts/check-store.mjs` exercita sessões e retomada, timers de descanso, cargas opcionais, conclusões, progressão por dia, falha de transação, exportação e importação manuais, recuperação de estado inválido e gravações concorrentes em duas instâncias. Também verifica que treinos não criam backups e que a limpeza de cópias antigas preserva o estado principal e arquivos externos. A simulação transacional não substitui testes em um navegador real.
