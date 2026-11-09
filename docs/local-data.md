# Dados pessoais no aparelho

O catálogo e as animações permanecem estáticos. O módulo `dist/store.js` armazena os registros pessoais em IndexedDB (`gymrook-personal`, versão 1, object store `records`), sem chamadas de rede. As atualizações do service worker não apagam esse banco.

O registro `state` contém `schemaVersion`, `updatedAt`, configurações de séries por exercício (`settings`), sessões (`sessions`) e progressão (`progression`). Cargas usam quilogramas. `weights` é um array alinhado a `reps`: `[]` significa sem carga informada, e `null` permite uma lacuna antes de uma carga de outra série. Valores `null` no final são removidos. As configurações iniciais são três séries de dez repetições e nenhuma carga informada.

Uma sessão mantém o instante de início, o instante de término, o início do descanso atual e uma cópia independente das séries e conclusões. O descanso não altera o início do treino. Alterações de configuração durante uma sessão atualizam apenas aquele exercício e desmarcam somente as séries cujos valores mudaram. Sessões concluídas preservam seus valores anteriores.

A progressão tem uma entrada por exercício e dia local (`YYYY-MM-DD`). Uma nova edição no mesmo dia substitui o ponto daquele dia. Confirmar valores que já estavam salvos não altera a data de edição nem cria um ponto, mesmo em outro dia. A simples marcação de uma série e os timers também não criam pontos de progressão.

Todas as alterações fazem leitura, modificação e escrita na mesma transação IndexedDB. A memória só muda após a confirmação da transação. Abas concorrentes recebem notificações por BroadcastChannel; voltar o foco à janela também recarrega os registros e a configuração do arquivo vinculado. Cada exercício aceita até 30 séries, 10000 repetições e 10000 kg por série.

## Backup diário

Ao iniciar um treino, o aplicativo cria ou substitui um único backup `gymrook-backup.json` no sistema de arquivos privado do site (OPFS), quando disponível. As alterações seguintes mantêm essa cópia atualizada, incluindo o treino recém-iniciado. Há também um único registro `daily-backup` independente em IndexedDB, usado como recuperação e alternativa quando OPFS não está disponível. Não há um arquivo acumulado para cada edição ou dia.

Essa cópia automática fica no armazenamento privado do navegador. **Ela não equivale a um arquivo protegido em Downloads e também pode desaparecer se os dados do site forem apagados.** A solicitação de armazenamento persistente reduz a chance de remoção automática quando o navegador a concede.

Quando o navegador oferece `showSaveFilePicker`, o usuário pode vincular um arquivo externo. O identificador do arquivo fica em IndexedDB e nunca vai para o JSON. O aplicativo substitui esse arquivo enquanto a permissão de escrita estiver concedida; se o navegador exigir nova autorização, o status informa isso e um clique pode solicitá-la novamente. Negar a permissão ou uma falha no arquivo externo não apaga o treino nem impede o backup local. As gravações de backup são serializadas entre abas usando Web Locks, com alternativa por concessão temporária em IndexedDB quando a API não existe.

Android e iPhone não oferecem suporte uniforme para substituir arquivos públicos automaticamente. Nesses navegadores, a exportação manual continua disponível; o navegador ou o sistema determina se o destino é Downloads, Arquivos ou outro local. Não são disparados downloads automáticos nem há promessa de sobrescrita silenciosa nessas pastas.

O JSON exportado é `{ "app": "GymRook", "formatVersion": 1, "exportedAt": "ISO", "state": { ... } }`. A importação aceita arquivos de até 20 MB e valida todo o conteúdo antes de substituir os dados, incluindo identificadores, datas, limites de séries, valores numéricos, duplicatas e no máximo uma sessão ativa. `validateBackup(json)` permite fazer essa verificação completa antes da confirmação na interface. A interface deve informar que importar substitui os dados atuais antes de chamar o método.

Se IndexedDB abre, mas o registro atual está inválido, `ready` rejeita sem apagar esse registro, `canRestore()` retorna `true` e `getInitializationError()` informa a falha. Nesse caso, `getDailyBackup()` e `importBackup(json)` continuam disponíveis para recuperação; depois da importação, recarregue a página para inicializar novamente a interface e os eventos. Se o próprio banco não abre, `canRestore()` retorna `false`.

## Verificação

`node scripts/check-store.mjs` exercita sessões e retomada, timers de descanso, cargas opcionais, conclusões, progressão por dia, falha de transação, validação de importação, snapshot diário único, alternativa sem OPFS, permissão de arquivo externo, falha de escrita e gravações concorrentes em duas instâncias. A simulação transacional não substitui testes em um navegador real.
