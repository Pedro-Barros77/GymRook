# Revisão das demonstrações — 7 de novembro de 2026

Os oito pontos pedidos foram tratados, e a ficha A foi completada. O guia ativo contém 31 demonstrações a 12 fps: 18 versões desta rodada e 13 versões anteriores mantidas. A prancha representa sustentação isométrica. As fontes foram produzidas pelo `image_gen` integrado; não houve chamada a API externa de geração.

## Evidência visual

O root examinou as fontes e os contatos dos quadros finais. A revisão independente abriu os 19 quadros canônicos de ida e as 18 sobreposições entre vizinhos dos novos movimentos dinâmicos; a volta usa os mesmos PNGs em ordem inversa, conferidos por hash. O afundo foi revisto também nos últimos passos e na passagem ao início.

- Flexora e stiff receberam novas poses em perfil, com medidas sobre as imagens geradas; foram revistos apoio, membros e alavancas. [QA temporal](generated-frames-v2-fixes/qa-leg-temporal.json).
- O afundo reutiliza a postura em pé no encerramento e tem uma breve pausa legítima antes de reiniciar. [Análise da emenda](generated-frames-v2-fixes/alternating-lunge/loop-analysis.json).
- Lateral, crucifixo inverso, remada no cabo, abdominal e os cinco novos movimentos A dinâmicos passaram pela revisão independente de quadros e transições. [Relatório](generated-frames-v2-fixes/upper-independent-motion-review.json).
- No crucifixo inverso, o banco acompanha a orientação da máquina; os dois braços abrem juntos. Há espaço livre entre mãos/alavancas e a torre. A projeção dos cotovelos foi comparada a um guia físico: um ângulo aparente maior no início não prova grande flexão do cotovelo no espaço. As medidas e a incerteza estão na pasta da fonte.
- No abdominal, assento e encosto vertical ficam parados. O apoio frontal se move com o tronco; a torre de resistência é fechada, sem placas expostas se deformando.
- A panturrilha sentada foi refeita até o joelho acompanhar a subida mantendo o antepé no apoio. Os 19 PNGs finais da v5 mostram cerca de 1,21% de faixa no proxy da tíbia, 2,70% no do fêmur, 0,27% no raio da alavanca e 0,36 px no pivô. Esses valores são medidas projetadas de referências superficiais, não medidas de ossos ou validação biomecânica. O ponto de textura rastreado no sapato se move cerca de 5,34 px; a revisão da sola curva não encontrou fresta entre pé e apoio. [Medições e limites](generated-frames-v2-fixes/seated-plate-calf-raise/qa-two-key-v5-temporal-measurements.json).
- A prancha usa uma única postura estável, com identificação de isometria. Os dois pilotos anteriores de 72 quadros usam amostragem dos quadros ímpares para preservar os três segundos a 12 fps; supino e flexão reutilizam as poses aprovadas.

No Scott, há um pequeno deslocamento aparente do cotovelo ao longo do apoio, estimado em 15 px com incerteza de 8 px porque o centro está ocluso. O contato continua visível, sem deformação ou duplicação clara. Foi aceito para o piloto e registrado, sem afirmar que a junta permanece geometricamente exata.

## Verificação técnica concluída

- `scripts/verify-final-animations.py`: **18/18 PASS**, com decodificação integral dos MP4s H.264/yuv420p de 512 × 512, 12 fps reais, duração, GIFs, pôsteres e fontes/PNGs congelados. Os quatro tipos de ciclo têm regras próprias: ida/volta, ciclo alternado, decimação e isometria.
- As 54 mídias novas somam 54.564.157 bytes. Os 660 PNGs aprovados permaneceram byte a byte iguais durante a exportação; agregado BIN32 `9777a02492052f07adc232d5e445a20e3ac32a4d36d7ba1f3caa4e7371cadd8a`.
- `npm run build` e `npm run check`: **PASS**, 31 exercícios e mapas, 179 arquivos versionados, 156,36 MiB, versão `fa4a7521fef8d86c`. Navegação, reprodução manual, download completo/incompleto, troca de versão, consulta offline e Range foram verificados.
- HTTP local: os 31 MP4s responderam **206** com os 1.024 bytes pedidos; os 31 pôsteres responderam **200** a HEAD; manifesto servido com a versão correta. Registro local: `output/final-animations/http-check.json`.
- `git diff --check`: sem erros de whitespace. A interface foi exercitada em DOM em memória; não houve teste desta revisão em navegador gráfico ou telefone real.

O relatório técnico local está em `output/final-animations/technical-verification.json`, SHA-256 `879667a8b86327c6d1762d32148dc91d6b83ee6c91c66114405e2ece39ecaa61`. O [manifesto publicado das mídias](../dist/assets/animations-v2/manifest.json) tem cobertura completa, com revisão e hashes por exercício.

## Preservação e publicação

O backup `backups/visual-v1-before-fixes-20261107/` preserva 2.862 arquivos, com manifesto SHA-256. A verificação final também comparou 2.003 arquivos originais no workspace: todos intactos. Estudos rejeitados e a v4 da panturrilha foram arquivados; os arquivos anteriores não foram apagados.

Fontes selecionadas: [configuração](generated-frames-v2-fixes/config.json). Prompts e histórico: [índice](prompts/final-animations-v2.json) e pastas por exercício. O código, as fontes e as mídias estão prontos localmente para o fluxo existente do GitHub Pages; esta rodada não executou commit ou push.

As revisões visuais e os testes verificam o guia ilustrativo. Não certificam execução de exercício, anatomia exata ou adequação individual do treino.
