# GymRook 1.1

Publicação de 9 de novembro de 2026. O catálogo bilíngue, os mapas musculares e as 31 animações aprovadas da versão 1.0 não foram alterados.

## Registro de treinos

- Iniciar e finalizar uma sessão A/B/C/D, com horário de início/fim e duração total.
- Cabeçalho fixo com tempo total e descanso independente. Os tempos são calculados a partir de instantes salvos, preservando a contagem ao reabrir ou bloquear a tela.
- Três séries de dez repetições como configuração inicial editável, com carga opcional por série, adição/remoção de séries e botão de lápis para editar.
- Salvamento automático, confirmação explícita da edição e marcação de conclusão fora do modo de edição.
- Referência das séries da sessão anterior. Sessões concluídas preservam suas cargas, repetições e conclusões mesmo se a configuração mudar depois.
- Um treino ativo por aparelho/navegador, com link para retomá-lo ao consultar outra ficha.

## Histórico e progressão

Calendário mensal com os dias de treino, várias sessões no mesmo dia e detalhes de início, fim, duração e exercícios/séries concluídos. Sessões que atravessam a meia-noite aparecem no dia local de início, informando a data de término quando diferente.

Os ajustes de séries/cargas geram um ponto por exercício e data local. Editar novamente no mesmo dia substitui esse ponto. Os gráficos permitem comparar a maior carga registrada em uma série, o total de repetições planejadas ou a quantidade de séries, com a configuração completa abaixo de cada dia. Marcar conclusão ou confirmar uma configuração idêntica não gera um ponto.

## Dados e backup

IndexedDB mantém os registros sem login ou envio de dados a um servidor. Um único backup automático é criado/substituído no armazenamento privado do site (OPFS), com cópia independente em IndexedDB como alternativa. Ele acompanha as alterações após o primeiro início de treino.

O backup interno pode ser apagado junto com os dados do site. Exportação/importação JSON permite manter uma cópia fora do navegador ou transferir os registros para outro aparelho. A importação valida o conteúdo antes da confirmação/substituição e cancela edições pendentes para impedir gravações antigas depois da restauração.

O navegador não oferece sobrescrita silenciosa de arquivos em Downloads/Arquivos de maneira uniforme no Android/iPhone. O vínculo a um arquivo externo aparece apenas nos navegadores com suporte, depende da autorização inicial e pode exigir nova autorização. O app informa falhas de gravação e mantém os registros do treino salvos.

Detalhes técnicos e formato: [local-data.md](local-data.md).

## Verificação

- `npm run build` e `npm run check`: integridade de mídia/manifest, regressão dos 31 exercícios, persistência simulada transacional, integração de interface e service worker.
- Casos adicionais: duas abas concorrentes, falha de gravação, estado inválido e recuperação, término em outro dia, edição inválida, navegação com salvamento pendente e importação com autosave pendente.
- `npm run check:browser`: Edge instalado, com perfil isolado, HTTP local e interface de 360 px. Verificou IndexedDB e OPFS reais, recarga, descanso independente, conclusão, histórico, restauração, gráficos e ausência de rolagem horizontal. Capturas das telas de treino, histórico, progressão e dados foram inspecionadas.

O teste de navegador é opcional e não instala software. Por padrão usa o Edge no Windows; `GYMROOK_BROWSER` permite informar outro executável Chromium instalado. Os artefatos e o perfil de teste ficam em `output/browser-qa/`, ignorado pelo Git. Não houve teste em aparelhos físicos Android/iPhone nem autorização de um arquivo externo em uma interface real.
