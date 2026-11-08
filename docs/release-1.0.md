# GymRook 1.0

8 de novembro de 2026.

Publica o guia ABCD com as animações aprovadas e acrescenta **1.0** ao lado de **Treinos**, em texto discreto no cabeçalho. A versão do projeto em `package.json` passa a `1.0.0`.

Os 31 exercícios têm demonstrações distintas a 12 fps. O supino usa os arquivos anteriores preservados; as quatro animações da revisão complementar estão em `dist/assets/animations-v4/`. Fontes, prompts e quadros anteriores continuam no projeto; os backups locais permanecem fora do Git e do deploy.

Validação local: `npm run build`, `npm run check` e `git diff --check`. O pacote tem 223 arquivos e 217.390.243 bytes; o build local gerou o cache `340cfce2fc43d3df`. A suíte conferiu cards, mapas, navegação, reprodução manual e operações offline em DOM em memória, sem teste em telefone real.

O push em `main` aciona o workflow existente do GitHub Pages, que executa novamente o build e as checagens antes de publicar `dist/`.
