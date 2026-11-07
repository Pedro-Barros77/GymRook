# Máscaras da alavanca antiga sobre a torre

37 máscaras L8, 512×512, copiadas sem alteração das mattes revisadas. Somente a silhueta ANTIGA da alavanca próxima dos quadros v4 é marcada, incluindo seu anel e a borracha superior. A geometria rígida nova não participa destas máscaras.

ROI permitido: `[124,0,180,164]`, com limite direito exclusivo. y0–49 é sempre zero; o primeiro pixel marcado começa em y56. Quadros13–37 são completamente vazios. A composição final com doadores temporais ainda exige revisão visual.

`annotations.json` guarda os contornos e medidas efetivos de cada fonte. `proofs/` contém os12 overlays revisados e a sobreposição de contornos anterior/atual/próximo. `manifest.json` registra os hashes dos37 PNGs e dos respectivos v4 originais arquivados.

Reprodução sem cache, na raiz do projeto:

```powershell
python docs/generated-frames-v5/pec-deck/old-near-tower-masks/generate-old-masks.py --output output/old-near-tower-masks-rebuild
```

O gerador local só lê estas anotações e o manifesto; verifica igualdade de cada hash. O código exato usado na etapa de revisão também foi arquivado como `generator-frozen-at-review.py`. Esse arquivo histórico documenta o processo de inspeção original; o comando acima é a reprodução independente de cache.
