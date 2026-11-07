# GymRook

Guia estático de musculação em português brasileiro, preparado para celular e GitHub Pages. Não exige conta, API, banco de dados ou serviço pago. Os nomes dos exercícios e dos equipamentos também aparecem em inglês.

## Abrir

Com Node.js 22 ou superior:

```sh
npm start
```

Abra **http://127.0.0.1:4173/**. Não é necessário executar `npm install`.

O modo offline exige HTTP em localhost ou HTTPS na hospedagem. Abrir `dist/index.html` diretamente não ativa o service worker.

## Estado atual

As demonstrações piloto de supino inclinado, flexão e rosca inversa mantêm os GIFs coloridos de 16 quadros gerados por imagem. O crucifixo na máquina usa a versão **v5**: MP4 e GIF de 72 quadros, a 24 fps, em um ciclo de três segundos. O GIF v4 de 72 quadros está disponível no detalhe por **Ver versão anterior**; a v3 permanece preservada em disco.

A v4 parte de 15 poses em resolução integral na diagonal aprovada, estabilizadas globalmente. O tempo considera as duas mãos. Practical-RIFE 4.25 interpola a ida; o primeiro intervalo usa FILM para evitar uma mão duplicada. Uma pequena correção gerada por imagem limpa a borda da alavanca no quadro 19. A volta reutiliza os quadros em ordem espelhada. Os pesos usam o mesmo sprite de nove placas sobre o fundo vazio `tower-clean`, com transição suave da máscara. O corpo articulado da tentativa Blender não participa desse processo. A revisão está em [docs/pec-deck-v4-review.md](docs/pec-deck-v4-review.md).

A **v5** mantém o corpo e o movimento da v4, com 37 quadros de ida e 35 espelhados. Ela substitui a coluna gerada que desaparecia nos quadros 11–14 por uma coluna canônica fixa e usa uma mesma malha rígida 3D para as alavancas do aparelho, com material prateado derivado da fonte. O conector preto acompanha o eixo da haste. Limpezas RGBA seletivas removem o metal antigo e harmonizam apenas o fundo ou a pele antes ocluídos; uma correção de borda antisserrilhada de até dois pixels é restrita ao suporte fixo. A área a partir de `y=164` permanece idêntica à v4; não há novos quadros humanos nem deformação da geometria do corpo. A revisão visual foi aprovada após examinar 37 quadros canônicos e 36 sobreposições entre vizinhos: [auditoria v5](docs/pec-deck-v5-review.md). Isso não certifica anatomia ou execução.

A rosca inversa conserva o teste opcional **Testar versão suavizada**, com retorno ao GIF original. A interpolação pode criar artefatos; fluidez e estabilidade não validam anatomia, contato físico ou execução. As demonstrações permanecem em revisão técnica.

Detalhes: [estado da mídia](docs/current-media-status.md).

## Conteúdo disponível

- Ficha ABCD completa: 26 blocos e 31 movimentos, com a programação recebida.
- Nomes e equipamentos bilíngues; mapas musculares detalhados de frente e costas, com legenda e nomes.
- Preparação, execução, pontos de atenção, erros comuns e glossário.
- Quatro demonstrações coloridas nos blocos piloto: supino inclinado com halteres, voador + flexão e rosca inversa na polia com rest-pause. O voador usa MP4 com GIF de compatibilidade e oferece a versão anterior.
- Imagens estáticas originais nos outros 27 movimentos, cuja animação permanece em preparação.
- Cards inteiramente clicáveis com imagem e equipamento em português e inglês.
- Botões Anterior/Próximo no topo e no fim dos detalhes. Séries, repetições e observações ficam nos detalhes.
- Tela inicial prática, sem marca, slogan ou apresentação comercial.
- Reprodução manual, iniciada no pôster. Não há autoplay.
- Download explícito do guia para consulta offline, com progresso e confirmação de conclusão.
- Manifest e ícones para adicionar à tela inicial no Android e iPhone.

## Conferir o guia

1. Abra o treino A e consulte os três blocos piloto.
2. Confira a identificação dos equipamentos, os músculos e as instruções.
3. Reproduza as demonstrações e observe a posição baixa, a posição alta e a emenda do loop.
   No voador, use **Ver versão anterior** para comparar com a v4. Na rosca inversa, use **Testar versão suavizada** para comparar com o original.
4. Volte ao início e escolha **Baixar para usar offline**. Mantenha o guia aberto até a confirmação.
5. Desative a conexão e reabra o mesmo endereço no mesmo navegador. Confira também a reprodução das demonstrações.

No Android, use o menu do Chrome para instalar/adicionar à tela inicial. No iPhone, use Compartilhar → Adicionar à Tela de Início no Safari; abra o app instalado e faça o download nele também. Dados offline podem ser removidos pelo usuário ou pelo sistema para recuperar espaço. A aplicação confere a presença dos arquivos ao verificar a disponibilidade offline.

## Decisões de conteúdo

As respostas sobre crossover na polia alta, desenvolvimento na máquina, elevação frontal, tríceps corda, mergulho no banco e isometria no pico estão incorporadas.

As referências propostas para os abdominais não especificados são **crunch reverso deitado com joelhos dobrados** para o infra e **crunch sentado na máquina** para o abdominal máquina. O modelo real e seus ajustes devem ser identificados com o professor. Outras variantes de referência, incluindo Scott e pegadas não especificadas, estão indicadas nos textos.

O descanso de revezamento entre três amigos e o máximo de um minuto quando o revezamento for rápido aparecem como orientação recebida. Os dez segundos do rest-pause e os trinta segundos entre lados da remada permanecem separados dessa nota.

Fontes e decisões: [docs/content-decisions.md](docs/content-decisions.md). As demonstrações continuam sendo um piloto para revisão técnica; testes de arquivos, código ou continuidade não validam anatomia ou execução.

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
- [Fontes das poses coloridas](docs/generated-frames-v2/)
- [Nova perspectiva do crucifixo](docs/generated-frames-v3/)
- [Prompts da revisão do crucifixo](docs/prompts/pec-deck-perspective-v3.json)
- [Prompts de geração e revisão](docs/prompts/animation-prompts-v2.json)
- [Fontes da primeira versão](docs/generated-frames/)
- [Prompts da primeira versão](docs/prompts/animation-prompts.json)
- [Fontes das miniaturas](docs/generated-thumbnails/)
- [Prompts das miniaturas](docs/prompts/thumbnail-prompts.json)
- [Montagem e tamanhos dos GIFs](docs/animation-build.json)

O `image_gen` integrado produziu as ilustrações. As folhas coloridas contêm 16 poses em uma grade 4 × 4. A montagem recorta as células, corrige pequenos deslocamentos globais pela posição dos pés e usa uma paleta compartilhada sem pontilhado por quadro. Isso reduz variações de codificação; não corrige toda mudança de anatomia, objetos ou perspectiva entre poses.

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

`npm run build` e `npm run check` passaram: o build registrou 59 arquivos, 27,80 MB e versão de cache `becf6b95b6040fef`; a suíte verificou 31 movimentos, quatro pilotos, interface em DOM em memória e operações offline. Em HTTP local na porta 4173, a página respondeu 200 e uma requisição Range ao novo MP4 respondeu 206 com 1.024 bytes. A revisão visual da v5 está na auditoria; não houve teste de layout em navegador real ou em telefone. Continuidade e integridade de arquivos não validam anatomia ou execução.

O código oferece suporte a vídeos MP4, usados na v5 do crucifixo e no teste opcional da rosca. Seus controles começam pausados, interrompem a reprodução ao navegar/trocar de versão e tratam falhas de `play()`. O service worker suporta HTTP Range (206), sufixos e erros 416 sem substituir o vídeo completo por um fragmento.

`scripts/check-ui.mjs` percorre os quatro treinos e os 31 detalhes em um DOM em memória. Confere cards, etiquetas bilíngues, mapas, navegação e controles de mídia. Não substitui inspeção visual ou teste em aparelho real. Não houve validação desta versão em Android ou iPhone real.

Para GitHub Pages:

O passo a passo do primeiro deploy está em [Publicar o piloto no GitHub Pages](docs/deploy-github-pages.md).

1. Envie o projeto para um repositório no GitHub com branch `main`, ou ajuste a branch em `.github/workflows/pages.yml`.
2. Em **Settings → Pages → Build and deployment**, escolha **GitHub Actions**.
3. Execute o workflow **Publicar GymRook no GitHub Pages**, ou envie um commit para `main`.

O workflow verifica o guia e publica `dist/`. Os caminhos e o escopo do service worker são relativos para funcionar em `https://usuario.github.io/GymRook/`. Nenhum repositório remoto foi criado nem publicação externa foi feita nesta sessão.

Referências: [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site), [cache de PWAs](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Caching).
