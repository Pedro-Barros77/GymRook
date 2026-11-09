# GymRook

Guia estático de musculação em português brasileiro, preparado para celular e GitHub Pages, com registro pessoal de treinos no aparelho. Não exige conta, API, banco remoto ou serviço pago. Os nomes dos exercícios e dos equipamentos também aparecem em inglês.

## Abrir

Com Node.js 22 ou superior:

```sh
npm start
```

Abra **http://127.0.0.1:4173/**. Não é necessário executar `npm install`.

O modo offline exige HTTP em localhost ou HTTPS na hospedagem. Abrir `dist/index.html` diretamente não ativa o service worker.

## Estado atual

Versão **1.2**, identificada ao lado de **Treinos** no cabeçalho. [Notas da versão](docs/release-1.2.md). O catálogo e todas as animações aprovadas da versão 1.0 permanecem preservados.

O botão **Iniciar treino** abre uma sessão com tempo total no cabeçalho fixo. O descanso tem cronômetro independente, sem pausar o treino. Na tela de cada exercício, o card **Suas séries** fica no fim do conteúdo, depois de **Como fazer**, com repetições e carga opcional editáveis; fora da edição, tocar em uma série marca sua conclusão. A listagem mantém apenas os cards de consulta com imagem, nome e equipamento. A configuração inicial editável é 3 × 10 e não substitui a programação da ficha. **Finalizar treino** fica depois dos exercícios.

**Histórico** mostra os treinos por dia em um calendário, com início, fim, duração e séries/exercícios concluídos. **Progressão** agrupa alterações por exercício e dia local, com gráficos de maior carga por série, total de repetições ou quantidade de séries. Editar várias vezes no mesmo dia atualiza o mesmo ponto; concluir uma série ou confirmar valores idênticos não cria um novo ponto.

**Iniciar treino** tem botão verde com ícone de play; **Finalizar treino** tem botão vermelho com ícone de stop. É possível excluir um treino finalizado ou um ajuste diário pelos botões vermelhos de lixeira, com confirmação. Ao excluir um ajuste, a configuração atual volta ao último ajuste restante; sem ajustes, volta ao padrão inicial. Excluir um treino não remove a progressão, e excluir ajustes preserva os registros das sessões já finalizadas.

**Seus dados** reúne exportação e importação manual de arquivos JSON. Use **Exportar dados atuais** para guardar uma cópia em Downloads ou Arquivos e restaurá-la quando precisar ou transferir os registros para outro aparelho. O app não gera backups automáticos nem mantém arquivos vinculados. Apagar os dados do site pode remover o histórico deste navegador; o arquivo exportado fica no local escolhido pelo usuário. [Formato e limites do armazenamento](docs/local-data.md).

Os 31 itens das fichas A, B, C e D têm demonstrações distintas e coloridas em MP4 a **12 fps**, GIF de compatibilidade e pôster no card. Os ciclos duram três segundos, com 36 quadros; o afundo alternado dura seis segundos, com 72 quadros. A prancha mostra uma sustentação isométrica estável.

A revisão atual restaura o supino anterior de `animations-v2` e encerra novas alterações nessa demonstração, conforme pedido. A Scott na máquina foi refeita com nova arte e pegada supinada. Supra e infra voltam a ser distintos: crunch do tronco e elevação das pernas deitado. A panturrilha em pé usa máquina inclinada, com calcanhares descendo abaixo e subindo acima do apoio; o abdominal sentado usa alças altas junto ao pescoço.

A panturrilha sentada e a remada unilateral na polia permanecem nas fichas B/C. Nomes, equipamentos, instruções e mapas acompanham as substituições. As versões anteriores continuam em disco e no backup local.

As [fontes e configuração](docs/generated-frames-v4-followup/config.json) registram poses geradas pelo `image_gen` integrado, interpolação local Practical-RIFE e composição raster. O infra conserva o mesmo desenho das pernas durante a rotação; partes estáticas reutilizam pixels canônicos. A tentativa Blender não participa das demonstrações. A revisão visual confere proporções projetadas, contatos, peças fixas, bilateralidade e emendas; ela não certifica biomecânica ou execução.

Detalhes: [estado da mídia](docs/current-media-status.md).

## Conteúdo disponível

- Ficha ABCD completa: 26 blocos e 31 itens de consulta, com a programação recebida.
- Nomes e equipamentos bilíngues; mapas musculares detalhados de frente e costas, com legenda e nomes.
- Preparação, execução, pontos de atenção, erros comuns e glossário.
- Demonstrações para os 31 exercícios, todas com MP4 a 12 fps, GIF de compatibilidade e pôster; a prancha mantém a postura isométrica.
- Cards inteiramente clicáveis com imagem e equipamento em português e inglês.
- Botões Anterior/Próximo no topo e no fim dos detalhes. Séries, repetições e observações ficam nos detalhes.
- Tela inicial prática, sem marca, slogan ou apresentação comercial.
- Reprodução manual, iniciada no pôster. Não há autoplay.
- Download explícito do guia para consulta offline, com progresso e confirmação de conclusão.
- Manifest e ícones para adicionar à tela inicial no Android e iPhone.
- Registro local de sessões, cronômetros, séries e cargas, com retomada após reabrir.
- Calendário de treinos, progressão por dia e exportação/importação de backups.

## Conferir o guia

1. Abra qualquer treino e selecione um card pela imagem e pelo equipamento.
2. Confira a identificação dos equipamentos, os músculos e as instruções.
3. Reproduza as demonstrações e observe a posição baixa, a posição alta e a emenda do loop.
   Na prancha, observe a postura sustentada; ela não faz repetições de subida e descida.
4. Volte ao início e escolha **Baixar para usar offline**. Mantenha o guia aberto até a confirmação.
5. Desative a conexão e reabra o mesmo endereço no mesmo navegador. Confira também a reprodução das demonstrações.

No Android, use o menu do Chrome para instalar/adicionar à tela inicial. No iPhone, use Compartilhar → Adicionar à Tela de Início no Safari; abra o app instalado e faça o download nele também. Dados offline podem ser removidos pelo usuário ou pelo sistema para recuperar espaço. A aplicação confere a presença dos arquivos ao verificar a disponibilidade offline.

## Decisões de conteúdo

As respostas sobre crossover na polia alta, desenvolvimento na máquina, elevação frontal, tríceps corda, mergulho no banco e isometria no pico estão incorporadas.

O supra usa **crunch no solo**, elevando a parte alta do tronco, e o infra usa **elevação das pernas deitado**, com cabeça e ombros apoiados. Permanecem 20 repetições de cada, seguidas da prancha. O abdominal da ficha C usa máquina com alças altas e a Scott usa máquina seletorizada. O modelo real e seus ajustes devem ser identificados com o professor.

O descanso de revezamento entre três amigos e o máximo de um minuto quando o revezamento for rápido aparecem como orientação recebida. Os dez segundos do rest-pause e os trinta segundos entre lados da remada permanecem separados dessa nota.

Fontes e decisões: [docs/content-decisions.md](docs/content-decisions.md). As demonstrações continuam sendo um piloto para revisão técnica; testes de arquivos, código ou continuidade não validam anatomia ou execução.

## Produzir a revisão atual

```sh
python scripts/build-followup-animations.py --prepare-only
# Rever fontes, proporções e mecânica antes de liberar motionReady na configuração.
python scripts/build-followup-animations.py --no-encode
# Rever quadros e emendas antes de exportar os PNGs congelados.
python scripts/build-followup-animations.py --encode-only
python scripts/verify-followup-animations.py
npm run build
npm run check
```

O runtime de interpolação já está em cache local; a publicação no Pages usa somente Node.js e `dist/`. As fontes e os quadros anteriores ficam preservados. O snapshot local completo desta rodada está em `backups/visual-v3-before-followup-20261107/`, com manifesto SHA-256. `--encode-only` exige a liberação `exportReady` e confere as fontes e os PNGs congelados antes de codificar. Reconstruir os quadros exige uma nova revisão visual. O supino restaurado fica fora do novo pipeline.

A seleção atual e seus limites estão em [docs/followup-animations-review.md](docs/followup-animations-review.md). As instruções de produção abaixo registram versões históricas; seus quadros e exceções de tempo não descrevem a seleção atual.

## Fontes visuais preservadas

- [GIFs e pôsteres dos demais pilotos e versão anterior do voador](dist/assets/animations/)
- [Mídia v4 do voador](dist/assets/animations-pec-deck-v4/)
- [Mídia v5 do voador](dist/assets/animations-pec-deck-v5/)
- [Quinze poses e configuração da v4](docs/generated-frames-v4/pec-deck/landmarks.json)
- [Prompts da v4](docs/prompts/pec-deck-v4.json)
- [Prompts adicionais da v4](docs/prompts/pec-deck-v4-additional.json)
- [Prompt da correção da borda](docs/prompts/pec-deck-v4-edge-repair.json)
- [Relatório de revisão da v4](docs/pec-deck-v4-review.md)
- [Fontes da v5](docs/generated-frames-v5/pec-deck/), [prompt da edição](docs/prompts/pec-deck-v5-structure.json) e [auditoria visual](docs/pec-deck-v5-review.md)
- [Fontes e configuração do treino D](docs/generated-frames-d-v1/config.json) e [índice de prompts](docs/prompts/leg-animations-v1.json)
- [Fontes e configuração dos treinos B/C](docs/generated-frames-bc-v1/config.json) e [índice de prompts](docs/prompts/bc-animations-v1.json)
- [Revisão visual do treino B](docs/bc-animations-v1-review-b.md) e [do treino C](docs/bc-animations-v1-review-c.md)
- [Fontes das poses coloridas](docs/generated-frames-v2/)
- [Nova perspectiva do crucifixo](docs/generated-frames-v3/)
- [Prompts da revisão do crucifixo](docs/prompts/pec-deck-perspective-v3.json)
- [Prompts de geração e revisão](docs/prompts/animation-prompts-v2.json)
- [Fontes da primeira versão](docs/generated-frames/)
- [Prompts da primeira versão](docs/prompts/animation-prompts.json)
- [Fontes das miniaturas](docs/generated-thumbnails/)
- [Prompts das miniaturas](docs/prompts/thumbnail-prompts.json)
- [Montagem e tamanhos dos GIFs](docs/animation-build.json)

O `image_gen` integrado produziu as ilustrações. As folhas coloridas dos pilotos originais contêm 16 poses em uma grade 4 × 4. A montagem recorta as células, corrige pequenos deslocamentos globais pela posição dos pés e usa uma paleta compartilhada sem pontilhado por quadro. Isso reduz variações de codificação; não corrige toda mudança de anatomia, objetos ou perspectiva entre poses.

O mapa muscular é uma ilustração vetorial original, com silhueta contínua, contornos curvos e grupos destacados. As cores não indicam porcentagem de ativação.

Para reconstruir as imagens existentes:

```sh
python -m pip install Pillow numpy opencv-python-headless
python scripts/assemble-animations.py
python scripts/assemble-thumbnails.py
npm run build
```

Essas dependências são apenas de produção. O site em funcionamento não usa Python.

Para montar a v4 do crucifixo a partir das fontes e da configuração registradas, sem alterar os outros pilotos:

```sh
python scripts/build-pec-deck-v4.py --config docs/generated-frames-v4/pec-deck/landmarks.json --film-intervals 0
npm run build
```

O backend padrão é Practical-RIFE 4.25 em CPU, escala 1. O backend anterior pode ser selecionado explicitamente com `--backend rife-ncnn-v4.6`; a primeira tentativa com sete poses foi rejeitada por imagens fantasma e arquivada em `output/pec-deck-v4-rife-rejected/`.

A v5 usa uma única edição limpa gerada pelo `image_gen` integrado e os arquivos preservados da v4. A sequência de produção prepara a placa canônica, as máscaras RGBA efetivas e as alavancas antes da composição e codificação:

```sh
python scripts/prepare-pec-deck-v5-plate.py
python scripts/prepare-pec-deck-v5-cleanups.py
python scripts/render-pec-deck-rigid-levers.py
python scripts/build-pec-deck-v5.py
```

O renderizador usa por padrão os ajustes registrados do eixo das hastes. As máscaras efetivas em `docs/generated-frames-v5/pec-deck/effective-tower-masks/` preservam a limpeza revisada sem substituir toda a área superior da cabeça por um retângulo, abordagem rejeitada por criar uma emenda de exposição. Os arquivos distribuídos `pec-deck.*` ficam em `dist/assets/animations-pec-deck-v5/`.

Para produzir as animações do treino D, a [configuração](docs/generated-frames-d-v1/config.json) especifica as folhas, recortes e tempos: nove poses na ida para cada um dos seis ciclos espelhados; o afundo usa 16 poses para um ciclo completo com as duas pernas. O processo usa Python 3.14 com Pillow, NumPy, OpenCV e imageio-ffmpeg, além do runtime local isolado Python 3.11 com PyTorch e o modelo Practical-RIFE 4.25 já em cache. Os caminhos locais do runtime e modelo estão na configuração. Não há download durante a montagem.

```sh
python scripts/build-leg-animations.py --prepare-only
python scripts/build-leg-animations.py --no-encode
# Após revisar os quadros intermediários e as emendas:
python scripts/build-leg-animations.py --encode-only
python scripts/verify-leg-animations.py
```

O primeiro comando extrai e registra as poses; o segundo interpola usando `scripts/rife-batch.py` sem publicar a mídia. `--encode-only` confere os hashes da configuração, das fontes e dos PNGs registrados e codifica os quadros já revisados sem interpolar novamente. O comando sem opções reconstrói os quadros e requer nova revisão antes de usar o resultado. O verificador confere os arquivos e ciclos; não substitui revisão visual ou técnica. O site e sua publicação no Pages usam apenas os arquivos prontos e Node.js para as verificações: não instalam Python nem usam API.

A interpolação final usa Practical-RIFE 4.25. No afundo, os quadros 18 e 42 usam tempo efetivo 0,9 para corrigir a opacidade do tênis; uma tentativa com FILM foi rejeitada e não integra a mídia ativa. A aprovação visual e seus limites estão em [docs/leg-animations-v1-review.md](docs/leg-animations-v1-review.md).

Para os treinos B/C, o adaptador reutiliza o mecanismo do treino D sem alterá-lo. Cada ciclo usa 19 quadros de ida e 17 cópias byte a byte na volta. A seleção do tríceps testa usa apenas as células 0 a 7 da folha. A interpolação usa o runtime local Practical-RIFE 4.25 em CPU, sem gerar uma imagem nova por quadro. As fontes e os tempos estão em [config.json](docs/generated-frames-bc-v1/config.json).

```sh
python scripts/build-bc-animations.py --prepare-only
python scripts/build-bc-animations.py --no-encode
# Após revisar os quadros intermediários e as emendas:
python scripts/build-bc-animations.py --encode-only
python scripts/verify-bc-animations.py
```

O verificador B/C também reutiliza as verificações técnicas do treino D. A revisão visual e a verificação das 14 mídias exportadas passaram. No crucifixo inverso, oito referências combinam cinco poses geradas com três projeções de equipamento rígido sobre o mesmo corpo raster, usando máscara humana opaca e recorte de mão, sem criar uma nova malha humana. A configuração exige SHA-256 para os três PNGs externos; geometria, máscaras e procedência estão em [midpoint-native-v1](docs/generated-frames-bc-v1/reverse-pec-deck/midpoint-native-v1/).

## Backups e teste 3D arquivado

O snapshot [backups/2d-v2-20261106/](backups/2d-v2-20261106/) preserva 21 arquivos: GIFs/pôsteres, dados anteriores, montagem, prompts e todas as oito folhas fonte PNG. Seu manifesto contém hashes SHA-256 e `RESTORE.md` explica a restauração.

O backup verificado [da v4 antes da alteração estrutural](backups/pec-deck-v4-before-structure-20261107/) contém 173 arquivos, cerca de 111 MB. Uma tentativa anterior baseada em uma faixa de painel foi rejeitada e está preservada no backup do projeto.

```sh
python scripts/backup-2d.py --verify
```

Nenhum quadro anterior foi descartado. O teste Blender rejeitado também permanece separado:

- [Cenas Blender](assets/3d/scenes/)
- [Documentação da tentativa 3D](docs/3d-rendering.md)
- [Procedência e licença do modelo humano](docs/3d-human-provenance.md)
- Mídias da tentativa rejeitada em `backups/3d-trial-20261106/animations-3d/`, fora da pasta publicada.
- Scripts em `scripts/three_d/` e renders locais em `output/3d/`.

Esses arquivos não constituem uma versão aprovada de execução de exercícios. Os testes daquela tentativa demonstram apenas suas propriedades técnicas medidas.

## Experimento de interpolação

O teste usa as nove poses da fase ascendente da rosca, estabilizadas por detalhes fixos da torre. A altura visual da barra redistribui o tempo entre as referências; uma curva periódica desacelera nos extremos. RIFE-v4.6 produz os instantes intermediários. A volta reutiliza exatamente os mesmos quadros, em ordem inversa, em vez das poses de retorno geradas separadamente. O corpo articulado do teste Blender não participa desse processo.

O resultado está em [dist/assets/animations-interpolated/](dist/assets/animations-interpolated/). Os quadros e relatórios locais estão em `output/generated-motion/reverse-cable-curl/`. O MP4 tem 72 quadros em três segundos, a 24 fps; o GIF é uma cópia de compatibilidade. Os originais não foram alterados.

Para reproduzir o teste com a ferramenta portátil já preparada em `.cache/interpolation/`:

```sh
python scripts/prepare-generated-motion.py
python scripts/interpolate-generated.py
python scripts/verify-generated-motion.py
npm run build
npm run check
```

O interpolador e seus modelos ficam apenas no computador de produção. O site recebe as mídias prontas, sem GPU, conta ou API. A versão Windows usa o separador decimal regional em `-s`; o script detecta esse detalhe automaticamente. Fontes oficiais, licenças e limites: [docs/interpolation-options.md](docs/interpolation-options.md).

Este é um experimento de movimento com comparação explícita. Não remove a necessidade de corrigir poses de referência inadequadas, e diferenças de textura ou forma podem continuar aparecendo de maneira gradual entre quadros.

## Verificar e publicar

```sh
npm run build
npm run check
```

O build atualiza `dist/asset-manifest.json` e a versão do service worker a partir dos arquivos distribuídos. A suíte verifica os 31 movimentos, imagens, formatos, manifestos e operações de cache: instalação, isolamento entre projetos, download completo, falha e recuperação, divergência de versão, perda parcial do cache e consulta sem rede.

Para a v5, a codificação e `scripts/verify-3d.py` passaram: MP4 H.264/yuv420p de 512 × 512, 72 quadros a 24 fps em três segundos; GIF de 72 quadros em 3.000 ms e loop contínuo; e pôster WebP de 512 × 512. O digest dos PNGs corresponde à revisão congelada (`f80dd9538e59e20105b05d915fbe7409272c5261e0614044f07bd0bf3b428d56`), e quatro arquivos da v4 continuam idênticos. A verificação de movimento também confirmou 16 arquivos originais preservados.

Para o treino D, `scripts/verify-leg-animations.py` passou: os sete MP4s H.264/yuv420p de 512 × 512 foram decodificados integralmente a 12 fps; os GIFs têm seis ciclos de 36 quadros e 3.000 ms e um de 48 quadros e 4.000 ms. As 21 mídias somam 28.161.046 bytes. Naquela entrega, os 53 assets anteriores permaneceram byte a byte idênticos; os 24 exercícios fora do treino D e os textos, prescrições e blocos da ficha estavam iguais.

Na entrega do treino D, `npm run build` e `npm run check` passaram: o build registrou 81 arquivos, 54,67 MB e versão de cache `af7ac858a8220dad`; a suíte verificou os 31 movimentos, 11 animados, interface em DOM em memória e operações offline, incluindo falhas e recuperação. Em HTTP local na porta 4173, o guia respondeu 200, os sete MP4s do treino D responderam 206 a requisições Range de 1.024 bytes e os sete pôsteres responderam 200 a requisições HEAD. Não houve teste de layout em navegador real ou em telefone. Continuidade e integridade de arquivos não validam anatomia ou execução.

Para B/C, `scripts/verify-bc-animations.py` passou: os 14 MP4s H.264/yuv420p e GIFs foram verificados em 512 × 512, 12 fps, 36 quadros e três segundos, sem perda de quadros nos GIFs. As 42 mídias somam 52.006.455 bytes; o manifesto está completo, com 14 de 14 movimentos. Os 75 assets anteriores permanecem byte a byte idênticos; os quatro pilotos originais, as instruções e prescrições dos 31 exercícios e os blocos de treino permanecem iguais.

As verificações da revisão atual e o tamanho do pacote estão registrados em [docs/current-media-status.md](docs/current-media-status.md). Os resultados acima sobre versões anteriores são históricos.

O código oferece suporte a vídeos MP4, usados na v5 do crucifixo, nos treinos B/C/D e no teste opcional da rosca. Seus controles começam pausados, interrompem a reprodução ao navegar/trocar de versão e tratam falhas de `play()`. O service worker suporta HTTP Range (206), sufixos e erros 416 sem substituir o vídeo completo por um fragmento.

`scripts/check-ui.mjs` percorre os quatro treinos e os 31 detalhes em um DOM em memória. Confere cards, etiquetas bilíngues, mapas, navegação e controles de mídia. Não substitui inspeção visual ou teste em aparelho real. Não houve validação desta versão em Android ou iPhone real.

Para GitHub Pages:

O passo a passo do primeiro deploy está em [Publicar o piloto no GitHub Pages](docs/deploy-github-pages.md).

1. Envie o projeto para um repositório no GitHub com branch `main`, ou ajuste a branch em `.github/workflows/pages.yml`.
2. Em **Settings → Pages → Build and deployment**, escolha **GitHub Actions**.
3. Execute o workflow **Publicar GymRook no GitHub Pages**, ou envie um commit para `main`.

O workflow verifica o guia e publica `dist/`. Os caminhos e o escopo do service worker são relativos para funcionar em `https://usuario.github.io/GymRook/`. Nenhum repositório remoto foi criado nem publicação externa foi feita nesta sessão.

Referências: [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site), [cache de PWAs](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Caching).
