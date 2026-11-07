# Alavancas rígidas — material v3, conexão v4

Estes são os 37 quadros de ida das duas alavancas, em PNG RGBA 512×512. Todos os pixels com `y >= 164` têm alpha zero. Mãos e corpo não são desenhados nem deformados pelo renderizador. O pipeline `build-pec-deck-v5.py` compõe estas camadas sobre o clean plate e espelha o retorno.

A conexão v4 usa o eixo do cilindro preto observado em cada quadro original, em vez do centro da mão. Isso corrige o desalinhamento entre colar, conector e pegador. O material v3 e a malha de metal permanecem iguais à versão aprovada anterior. O cilindro de borracha também tem uma única malha fixa; sua inclinação muda por rotação rígida.

## Reprodução

Na raiz do projeto:

```powershell
python scripts/render-pec-deck-rigid-levers.py
```

Para conferir sem sobrescrever estes arquivos:

```powershell
python scripts/render-pec-deck-rigid-levers.py --output output/rigid-levers-rebuild
```

Uma seleção rápida das quatro poses aprovadas:

```powershell
python scripts/render-pec-deck-rigid-levers.py --output output/rigid-levers-preview --frames 1,12,25,37
```

O CLI aceita `--canonical-source`, `--motion-report` e `--axis-fits`. Os padrões são snapshots incluídos nesta pasta; a reprodução não depende de cache. Ambiente utilizado: Python 3.14.2, NumPy 2.5.4 e Pillow 13.0.0. O render é local e não precisa de serviços, modelos externos ou GPU.

## Fontes e geometria

- `canonical-source-512.png`: cópia exata do canonical gerado pose08, alinhado como `anchor_14` da versão v4.
- `motion-37.json`: snapshot dos 37 quadros de ida e hashes das quatro prévias de conexão aprovadas. O renderizador verifica esses hashes quando usa as fontes aprovadas.
- `shaft-axis-fits.json`: medidas brutas do cilindro preto em linhas 158–173, extrapoladas a y149 e y164. Registra componentes de cor, linhas utilizadas, resíduos e casos de fundo escuro fundido ao pegador.
- `shaft-axis-fits-smoothed.json`: mesmos dados com regularização temporal fraca, limitada a 0,8 px de deslocamento na interface y164. Inclui os caminhos e hashes dos 37 originais v4 arquivados.
- `canonical-material-atlas.png` e `rubber-material-atlas.png`: perfis RGB extraídos uma vez das imagens geradas, reaproveitados em todos os quadros.
- `metadata.json` e `manifest.json`: hashes, fontes, geometria constante, transformações e rotações dos conectores por quadro.

A peça de metal é um único tubo retangular curvo com bevel, compartilhado entre instâncias e quadros. Apenas seu yaw muda; a largura física continua visível no ângulo de perfil. As faces largas mantêm normais planas, os bevels recebem highlights estreitos e a luz fica fixa. Os colares são anéis com projeção local constante de 10°.

O conector usa um cilindro fixo de raio 8 e altura 14, com rotação Z rígida para acompanhar o eixo preto real. Ele se estende além da interface durante o supersampling; o recorte de alpha em y164 só ocorre depois do antialiasing, evitando uma fenda na última linha visível. A instância distante tem escala fixa de perspectiva fraca.

Hash da malha de metal: `402075a2ffcf037b7dcf6a87b3d6601c67ab829943d452e2b957ab073a88e477`.

Hash da malha de borracha: `ab456da5cf1328836e8829362fd1c34dd1edd2b25d166cc3b1ba383accfbd998`.

A versão anterior completa, com conexão v3, está preservada em `../rigid-levers-v3/`. Seu gerador exato é `scripts/render-pec-deck-rigid-levers-v3.py`; consulte `../rigid-levers-v3/ARCHIVE.md` para reproduzir essa comparação.
