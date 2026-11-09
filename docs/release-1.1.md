# GymRook 1.1

Publicação de 9 de novembro de 2026. O catálogo bilíngue, os mapas musculares e as 31 animações aprovadas da versão 1.0 não foram alterados.

## Registro de treinos

- Iniciar e finalizar uma sessão A/B/C/D, com horário de início/fim e duração total.
- Cabeçalho fixo com tempo total e descanso independente. Os tempos são calculados a partir de instantes salvos, preservando a contagem ao reabrir ou bloquear a tela.
- Três séries de dez repetições como configuração inicial editável, com carga opcional por série, adição/remoção de séries e botão de lápis para editar.
- Cards da listagem com imagem, nome e equipamento para consulta rápida. As séries ficam somente dentro do exercício, como último card de conteúdo depois de **Como fazer**.
- Salvamento automático, confirmação explícita da edição e marcação de conclusão fora do modo de edição.
- Referência das séries da sessão anterior. Sessões concluídas preservam suas cargas, repetições e conclusões mesmo se a configuração mudar depois.
- Um treino ativo por aparelho/navegador, com link para retomá-lo ao consultar outra ficha.

## Histórico e progressão

Calendário mensal com os dias de treino, várias sessões no mesmo dia e detalhes de início, fim, duração e exercícios/séries concluídos. Sessões que atravessam a meia-noite aparecem no dia local de início, informando a data de término quando diferente.

Os ajustes de séries/cargas geram um ponto por exercício e data local. Editar novamente no mesmo dia substitui esse ponto. Os gráficos permitem comparar a maior carga registrada em uma série, o total de repetições planejadas ou a quantidade de séries, com a configuração completa abaixo de cada dia. Marcar conclusão ou confirmar uma configuração idêntica não gera um ponto.

## Dados e backup

IndexedDB mantém os registros sem login ou envio de dados a um servidor. A exportação manual de um arquivo JSON permite guardar uma cópia em Downloads ou Arquivos e transferir os registros para outro aparelho.

A importação valida o conteúdo antes da confirmação/substituição e cancela edições pendentes para impedir gravações antigas depois da restauração. Limpar os dados do site pode apagar o histórico local; o arquivo exportado permanece no local escolhido pelo usuário.

Não há backup automático, cópia privada redundante ou arquivo externo vinculado. Ao atualizar a partir da implementação anterior, apenas as cópias internas obsoletas e seus metadados são removidos; os registros de treino e eventuais arquivos externos do usuário são preservados.

Detalhes técnicos e formato: [local-data.md](local-data.md).

## Verificação

- `npm run build` e `npm run check`: integridade de mídia/manifest, regressão dos 31 exercícios, persistência simulada transacional, integração de interface e service worker.
- Casos adicionais: duas abas concorrentes, falha de gravação, estado inválido e recuperação, término em outro dia, edição inválida, navegação com salvamento pendente, importação com autosave pendente e ausência de gravações automáticas de backup.
- `npm run check:browser`: Edge instalado, com perfil isolado, HTTP local e interface de 360 px. Exercita IndexedDB real, recarga, descanso independente, conclusão, histórico, exportação/restauração manual, gráficos e ausência de rolagem horizontal. Gera capturas das telas para inspeção visual.

O teste de navegador é opcional e não instala software. Por padrão usa o Edge no Windows; `GYMROOK_BROWSER` permite informar outro executável Chromium instalado. Os artefatos e o perfil de teste ficam em `output/browser-qa/`, ignorado pelo Git. Não houve teste em aparelhos físicos Android/iPhone.
