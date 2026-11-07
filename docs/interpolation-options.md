# Interpolação das ilustrações geradas

Este documento registra uma ferramenta local de produção e seus limites. Não altera as imagens originais nem certifica a execução dos exercícios.

## Opção escolhida para o teste

**RIFE ncnn Vulkan**, distribuição oficial de `nihui/rife-ncnn-vulkan`, release `20221029`, com o modelo `rife-v4.6`. O executável é portátil e usa Vulkan; dispensa instalar PyTorch e CUDA. O material fica em `.cache/interpolation/`, fora do site publicado.

Fontes primárias:

- [Repositório e comandos oficiais](https://github.com/nihui/rife-ncnn-vulkan)
- [Release oficial 20221029](https://github.com/nihui/rife-ncnn-vulkan/releases/tag/20221029)
- [Código do programa e seleção de timestep](https://github.com/nihui/rife-ncnn-vulkan/blob/master/src/main.cpp)
- [Modelo v4.6 no repositório oficial](https://github.com/nihui/rife-ncnn-vulkan/tree/master/models/rife-v4.6)
- [Projeto RIFE original](https://github.com/hzwer/arXiv2020-RIFE)

O pacote Windows oficial tem 431.540.241 bytes e reúne executável e modelos. A versão atual do repositório consultada foi `a7532fc3f9f8f008cd6eecd6f2ffe2a9698e0cf7`. O modelo v4.6 tem dois arquivos: `flownet.bin` (10.614.320 bytes) e `flownet.param` (16.532 bytes).

## Contrato da ferramenta

```powershell
& '.cache/interpolation/rife-ncnn-vulkan-20221029-windows/rife-ncnn-vulkan.exe' `
  -0 'anchor-a.png' -1 'anchor-b.png' -o 'between.png' `
  -m '.cache/interpolation/rife-ncnn-vulkan-20221029-windows/rife-v4.6' `
  -s '0,25' -g 0 -j '1:1:1' -z
```

`-s` aceita um tempo estritamente entre zero e um. A família v4 permite tempos arbitrários; os modelos anteriores aceitam apenas o ponto médio. O nome do diretório precisa conter `rife-v4`, pois o programa o usa para selecionar a arquitetura. Para os extremos zero e um, copie os respectivos quadros de referência sem executar interpolação.

`-g` seleciona a GPU; deve ser confirmado pelo log local. `-z` ativa a média das duas direções temporais. `-x` acrescenta variantes espaciais e aumenta o custo. O modo de diretório com `-n` não cria por si só uma curva periódica: seu mapeamento é linear e limita o último trecho. Para este projeto, é mais controlável escolher explicitamente os pares e o tempo de cada quadro.

**Detalhe confirmado neste Windows em português:** o programa interpreta os argumentos decimais conforme a localidade. `-s 0.25` resultou em erro; `-s '0,25'` funcionou. Um chamador Python deve usar `f'{t:.8f}'.replace('.', ',')` para esse ambiente, sem mudar a configuração regional do computador.

## Teste local concluído

O pacote foi baixado do release oficial, extraído e executado em modo de linha de comando. A GPU selecionada foi o dispositivo zero, NVIDIA GeForce RTX 4070 SUPER. Três tempos diferentes — 0,25, 0,5 e 0,75 — produziram PNGs válidos e distintos de 480 × 480 usando duas poses reais do supino da folha gerada. Os resultados foram diferentes de uma simples mistura das duas imagens; a proximidade em pixels de cada extremo variou na ordem esperada. Isso comprova o funcionamento da ferramenta, sem certificar anatomia ou fidelidade do movimento.

Os chamados levaram aproximadamente 1,6 a 3,9 segundos por imagem com a opção temporal `-z`, incluindo inicialização do programa. As entradas e os resultados estão em `.cache/interpolation/smoke/`. O teste não mudou nenhum arquivo do guia.

Verificações de origem:

- SHA-256 do pacote: `d8e4d772d26cd8006ef0ad0bc82eb191b53c68677d1ae2f42506d74cbbbea606`.
- Os bytes de `flownet.bin` coincidem com o objeto Git oficial `70de38ecc5b6f1b63afa56108bf76911f04ce630`.
- `flownet.param` coincide com o objeto Git oficial `3cb69d4ae09b085a2b5b51eb3c2e93745f805644` depois de normalizar apenas as quebras de linha CRLF/LF do pacote Windows.
- O release antigo não fornece digest do executável na API consultada. O hash local do executável e todos os tamanhos estão no relatório, sem apresentar esse registro como um checksum oficial independente.

## Ordem recomendada para o piloto

1. Escolher apenas poses coerentes e em ordem monotônica na fase de esforço.
2. Registrar a câmera usando partes realmente imóveis do aparelho, sem usar braços ou pesos como referência.
3. Corrigir a emenda do ciclo; reutilizar o mesmo movimento na volta evita uma segunda sequência de poses inconsistentes.
4. Interpolar os intervalos entre essas referências em uma cadência de 24 fps.
5. Rever mãos, cotovelos, cabos, pesos e sobreposições, inclusive quadro a quadro.

## Limites

A rede estima quadros intermediários; não conhece a execução correta do exercício. Ela não corrige pivôs, proporções, trajetórias ou perspectiva errados nas referências. Variações de textura entre imagens geradas ainda podem virar uma transformação gradual. Oclusões e deslocamentos grandes podem produzir duplicações, bordas elásticas ou membros deformados.

Por isso, um vídeo mais suave não deve ser apresentado como validação anatômica. O resultado continua experimental até passar pela revisão visual e pela revisão técnica de execução. A comparação com os quadros de referência originais precisa permanecer disponível.

## Licenças

O repositório `nihui/rife-ncnn-vulkan` declara MIT, copyright 2020 nihui. O projeto RIFE original declara MIT, copyright Megvii Inc. As licenças são preservadas em `.cache/interpolation/`. O modelo v4.6 é distribuído no repositório e no pacote oficial; não foi encontrada uma licença separada por arquivo de pesos. Esta configuração usa a distribuição oficial apenas como ferramenta local e não redistribui executável ou pesos no PWA.

Os hashes do pacote, executável e pesos, junto com o resultado do teste local, estão registrados em `.cache/interpolation/setup-summary.json`.
