# Alavancas rígidas — material v3 aprovado

Estes são os 37 quadros de ida das duas alavancas de equipamento, em PNG RGBA 512×512. O fundo é transparente. Todos os pixels com `y >=164` têm alpha 0; mãos e corpo não são desenhados nem deformados por este renderizador. A composição com o clean plate e o retorno espelhado pertence ao pipeline `build-pec-deck-v5.py`.

O material v3 foi escolhido após comparação das quatro poses 1, 12, 20 e 37. OsPNG finais dessas poses reproduzem exatamente os hashes das prévias aprovadas, incluídos em `motion-37.json`. As versões experimentais e suas provas anteriores permanecem em `.cache/qa-equipment-continuity/`.

## Reprodução

Na raiz do projeto:

```powershell
python scripts/render-pec-deck-rigid-levers.py
```

Para conferir sem sobrescrever estes arquivos:

```powershell
python scripts/render-pec-deck-rigid-levers.py --output output/rigid-levers-rebuild
```

Uma seleção opcional para inspeção rápida:

```powershell
python scripts/render-pec-deck-rigid-levers.py --output output/rigid-levers-preview --frames 1,12,20,37
```

O CLI também aceita `--canonical-source` e `--motion-report`. Os padrões são os snapshots incluídos nesta pasta, portanto a reprodução não depende de arquivos de cache. Ambiente utilizado: Python 3.14.2, NumPy 2.5.4 e Pillow 13.0.0. O render é local e não precisa de modelos externos, serviços ou GPU.

## Fontes e método

- `canonical-source-512.png`: cópia exata do canonical gerado pose08, alinhado como `output/pec-deck-v4/anchors/anchor_14.png`.
- `motion-37.json`: snapshot das posições das mãos e intervalos do relatório v4 usado na aprovação. O renderizador usa essas posições somente para determinar o yaw de cada alavanca em torno do pivô fixo.
- `canonical-material-atlas.png`: perfil RGB transversal extraído uma vez do aço do canonical; aplicado continuamente à peça inteira. O material não é gerado novamente por frame.
- `metadata.json`: geometria, iluminação, fonte, câmera, instâncias e transformações por quadro.
- `manifest.json`: hashes dos 37PNG, limites de alpha, hash da malha e hash do gerador.

A peça é um único tubo retangular curvo com bevel; o mesmo buffer de vértices é compartilhado entre instâncias e quadros. A espessura permanece visível quando a peça passa pelo ângulo de perfil. As faces largas mantêm normais planas, os bevels recebem highlights estreitos e a luz fica fixa. Os colares são anéis com projeção local constante de 10°, para mostrar o aro superior. Essa projeção não muda entre frames. A instância distante tem escala fixa de perspectiva fraca.

Hash da geometria v3: `402075a2ffcf037b7dcf6a87b3d6601c67ab829943d452e2b957ab073a88e477`.

A câmera dos braços é ortográfica e a altura do colar fica próxima de 149 px; os desenhos independentes originais variam alguns pixels. O material aproveita a cor gerada e iluminação determinística; não é uma reconstrução calibrada de refletância. O compositor deve retirar o metal antigo com o clean plate antes de adicionar estas camadas.
