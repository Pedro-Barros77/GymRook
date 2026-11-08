# Rodada 4 — fontes e exportação isoladas

`scripts/build-followup-animations.py` importa o mecanismo anterior apenas em memória, com novos caminhos. Os scripts e mídias anteriores não são alterados. O supino não pertence ao conjunto: o site deve selecionar os arquivos existentes de `animations-v2` e preservá-los sem recodificação.

Configuração: `docs/generated-frames-v4-followup/config.json`. Candidatos: `output/followup-round4/<id>/`. Mídia nova: `dist/assets/animations-v4/`. Relatório: `docs/followup-animations-build.json`.

## Gates

1. Guardar folha/poses e prompts em diretório próprio. O formato inicial é uma folha3×3,9poses somente de ida, sem retorno gerado separadamente. Revisar fonte e conferir execução/equipamento antes de liberar `prepareReady`.
2. Congelar a fonte com `sheetSha256`; configurar células e tempos. O ciclo tem36frames,12fps e3s. Se o ângulo projetado não variar linearmente entre poses, registrar tempos explícitos nas âncoras.
3. Preparar e revisar os recortes. Só então liberar `motionReady` e construir candidato.
4. Rever todos19quadros de ida,18sobreposições e ambos extremos no tamanho real; conferir oclusões e partes fixas. Volta usa17cópias byte a byte.
5. Congelar evidências de revisão em `docs/`, criar o índice final com fonte e digest dos PNGs e liberar `exportReady`. Exportar os mesmos PNGs com `--encode-only`.

```powershell
python scripts/build-followup-animations.py --preflight
python scripts/build-followup-animations.py --exercise preacher-curl --prepare-only
python scripts/build-followup-animations.py --exercise preacher-curl --no-encode
# Após a revisão dos PNGs reais e liberação do gate:
python scripts/build-followup-animations.py --exercise preacher-curl --encode-only
python scripts/verify-followup-animations.py --exercise preacher-curl
# Quando todos os IDs estiverem prontos:
python scripts/verify-followup-animations.py
```

`sourceKind: reviewed-png-loop` permite importar36PNG finais já revistos sem interpolação nem transformação. Isso não dispensa revisão da execução. Máscaras canônicas devem respeitar partes móveis e não podem esconder colisões. Se mãos, pernas ou máquina não fizerem sentido, corrigir a fonte; métricas de pixels não resolvem anatomia.

O adaptador recusa alteração dos seis scripts de mecanismo anterior. O verificador integral exige todas as mídias configuradas, o índice visual e as entradas congeladas, além de conferir arquivos originais contra o snapshot `backups/visual-v3-before-followup-20261107/`.

O workflow do Pages permanece Node.js + `dist/`; o Python é usado apenas para produção das mídias. Não executar o build do site antes de integrar todas as substituições selecionadas.
