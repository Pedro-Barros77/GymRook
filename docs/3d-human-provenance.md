# Modelo humano das cenas 3D

O personagem usa uma malha humana real, com topologia, esqueleto e pesos do MakeHuman. A pele e as roupas são deformadas pelo mesmo esqueleto em todos os quadros; nenhuma pose da animação é redesenhada por geração de imagens.

## Origem e licença

- Projeto oficial: <https://github.com/makehumancommunity/makehuman>
- Revisão fixa: `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`.
- Malha de origem: `makehuman/data/3dobjs/base.obj`.
- Esqueleto: `makehuman/data/rigs/default.mhskel`.
- Pesos: `makehuman/data/rigs/default_weights.mhw`.
- Modificadores de forma: alvos oficiais masculinos adultos, musculatura, proporções e ajustes dos membros.

Os arquivos acima são **assets gráficos CC0-1.0**, conforme o capítulo C de `assets/3d/human/LICENSE.upstream.md` e o texto em `assets/3d/human/LICENSE.ASSETS.md`. Essa licença dos assets é distinta da licença AGPL do programa MakeHuman; nenhum código do programa foi incorporado ao adaptador.

Confirmação institucional: <https://www.makehumancommunity.org/about/license.html>.

Os URLs fixos, tamanhos e hashes SHA-256 de cada arquivo estão em `assets/3d/human/asset-sources.json`. A malha, o esqueleto e os pesos inicialmente obtidos de `master` foram comparados byte a byte com a revisão fixa acima.

## Adaptação original para o guia

`scripts/three_d/human.py` aplica os alvos de forma, converte os eixos para metros e cria uma malha masculina de 1,80 m. O rig mantém os 163 ossos do esqueleto de origem e seus pesos de deformação. O corpo tem subdivisão de superfície, preservação de volume e material de pele bronzeada uniforme. Cabelo curto, sobrancelhas e olhos são elementos fixos do mesmo personagem.

O shorts foi criado a partir do helper gráfico de roupa da própria malha CC0, com corte na coxa, folga e espessura. Os tênis são malhas originais modeladas para cobrir os pés; as faces da pele ocultas pelos tênis são retiradas para evitar que dedos atravessem o calçado. Roupas, tênis e olhos também seguem o rig.

Materiais não usam texturas aleatórias por quadro. A continuidade vem da geometria e dos materiais fixos, não de alinhamento posterior de imagens.

## Contrato do módulo

```python
from human import create_human, REST_JOINTS, SEGMENT_LENGTHS

athlete = create_human()
athlete.pose(joints, grip=1.0,
             hand_roll={'left': 0.0, 'right': 0.0},
             palm_normals={'left': (0, 0, -1), 'right': (0, 0, -1)})
athlete.keyframe(frame)
```

Coordenadas em metros: X positivo é o lado esquerdo anatômico, Y aponta à frente e Z para cima. `pose_positions()` é um alias de `pose()`. `athlete.armature`, `athlete.body`, `athlete.objects`, `athlete.rest_joints`, `athlete.grip_centers` e `athlete.palm_centers` estão disponíveis para a composição e conferência da cena.

`joints` aceita os centros `pelvis`, `chest`, `neck`, `head` e, para cada lado `left`/`right`, `shoulder`, `elbow`, `wrist`, `hip`, `knee`, `ankle` e `toe`. `left_hand`/`right_hand` são os centros dos pegadores. O centro de um pegador cilíndrico fica na concavidade do punho fechado, cerca de 9,6 cm do centro do punho anatômico. Para mãos abertas (`grip=0`), usa-se o centro plano da palma, sem o deslocamento do punho fechado; os dedos são estendidos no plano da palma.

`palm_normals` permite escolher explicitamente a orientação da palma. Para uma barra pronada, a palma aponta para o lado oposto ao dorso da mão; a direção varia conforme o ângulo do antebraço. Mãos, dedos e polegares usam articulações fixas, com oposição do polegar para fechar a pegada.

## Verificações

O módulo foi criado e executado no Blender 4.5.15 LTS em modo de renderização offline. O teste criou a malha, os 163 ossos e os objetos auxiliares; também renderizou posições aberta e fechada no crucifixo para conferir a deformação. Foram corrigidos o contato da pele com o tênis, a referência da palma fechada e a abertura dos dedos para apoio no solo.

O rig garante continuidade geométrica. A escolha das poses e a revisão técnica da execução continuam sendo responsabilidades da cena de cada exercício e de sua validação pelo professor.
