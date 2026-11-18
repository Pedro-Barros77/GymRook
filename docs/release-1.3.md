# GymRook 1.3

Publicação de 18 de novembro de 2026.

- Histórico: edição da data e do horário de início e término dos treinos concluídos, com recálculo da duração e do dia no calendário.
- Exercícios: contador de séries concluídas no topo, com check verde quando todas estão marcadas.
- Listagem: os mesmos contadores por exercício e destaque verde nos cards concluídos da sessão em andamento. Conjugados e circuitos têm fundo azul.
- Descrição privada permanente por exercício, independente das cargas e da progressão.
- Notas por exercício naquela sessão, inicialmente vazias a cada treino e incluídas no histórico. Ambas as anotações são opcionais, locais e aceitam até 4.000 caracteres.
- Os campos de anotação ficam no fim da tela do exercício, depois do card **Suas séries**.
- No topo do último exercício, botão de finalizar com confirmação. O botão no fim da listagem continua disponível.
- Edição de séries não gera mais aviso global de sucesso. Outras notificações de sucesso desaparecem após alguns segundos; erros permanecem visíveis.

Os registros e backups da versão anterior continuam compatíveis. Exportações novas incluem as anotações. As notas privadas fixas não são copiadas para o histórico das sessões.

## Testar

Execute `npm start` e abra `http://127.0.0.1:4173/`. O cabeçalho identifica `1.3`. Para o navegador receber a versão nova do service worker, mantenha a página aberta com conexão por alguns segundos, feche todas as abas desse endereço e reabra se ainda aparecer a interface antiga. Depois, atualize o conteúdo offline.

O endereço local e o GitHub Pages têm armazenamentos separados. Para testar com o histórico real, exporte os dados do site publicado e importe a cópia no endereço local. Nenhum dado do site publicado é alterado por esse teste.

Confira um treino com duração muito longa no histórico e corrija seus horários. Inicie outro treino, marque séries e navegue entre os exercícios e a listagem para conferir os indicadores. Preencha os dois tipos de anotação, reabra o exercício e finalize pelo último item. Confira as notas no histórico e o campo vazio ao iniciar uma nova sessão.

Verificações automatizadas: `npm run build`, `npm run check` e, opcionalmente com Edge instalado, `npm run check:browser`. O teste de navegador usa um perfil separado, sem acessar dados pessoais do navegador principal.
