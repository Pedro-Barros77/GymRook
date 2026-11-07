/* GymRook — conteúdo em pt-BR. As séries abaixo reproduzem a ficha recebida. */
(() => {
  const exercises = {
    'incline-dumbbell-press': {
      name: 'Supino inclinado com halteres · 45°', nameEn: '45° incline dumbbell bench press',
      equipment: 'Banco regulável a 45° + dois halteres', equipmentEn: 'Adjustable incline bench + dumbbells',
      primary: ['Peitoral maior, com ênfase na porção clavicular'], secondary: ['Tríceps', 'Deltoide anterior'], muscleIds: ['chest', 'triceps', 'deltoidFront'],
      setup: ['Trave o encosto em 45°. Apoie os pés e mantenha quadril e costas no banco.', 'Comece com os halteres junto ao alto do peito, punhos alinhados aos antebraços.'],
      steps: ['Empurre os dois halteres para cima, mantendo-os sobre o alto do peito.', 'Desça devagar, com cotovelos sob os punhos, até a amplitude confortável.', 'Repita sem bater os halteres e sem tirar o quadril do banco.'],
      cues: ['Ombros apoiados no banco; peito aberto sem exagerar o arco lombar.', 'Solte o ar ao empurrar. Peça ajuda para posicionar ou guardar halteres pesados.'],
      mistakes: ['Dobrar os punhos para trás.', 'Abrir os cotovelos totalmente para os lados.', 'Descer além do controle ou usar impulso.']
    },
    'high-cable-crossover': {
      name: 'Crossover diagonal na polia alta', nameEn: 'High-to-low cable crossover',
      equipment: 'Duas polias altas + pegadores individuais', equipmentEn: 'Dual cable station + single handles',
      primary: ['Peitoral maior'], secondary: ['Deltoide anterior'], muscleIds: ['chest', 'deltoidFront'],
      setup: ['Coloque as polias acima dos ombros e segure um pegador em cada mão.', 'Dê um passo à frente; mantenha um pé adiantado e cotovelos levemente dobrados.'],
      steps: ['Leve as mãos em arco para baixo e para a frente, até se aproximarem à frente do corpo.', 'Abra os braços devagar até a amplitude confortável, sem deixá-los muito atrás do tronco.'],
      cues: ['Conserve a mesma dobra dos cotovelos.', 'Tronco estável; mãos podem se encontrar sem cruzar uma sobre a outra.'],
      mistakes: ['Transformar o movimento em um empurrão.', 'Balançar o corpo.', 'Deixar a carga puxar os braços excessivamente para trás.']
    },
    'pec-deck': {
      name: 'Crucifixo na máquina · peck deck', nameEn: 'Pec deck / machine chest fly',
      equipment: 'Máquina peck deck / voador', equipmentEn: 'Pec deck / chest fly machine',
      primary: ['Peitoral maior'], secondary: ['Deltoide anterior'], muscleIds: ['chest', 'deltoidFront'],
      setup: ['Ajuste o banco para os braços ficarem próximos à altura dos ombros.', 'Apoie costas e pés. Segure as alças ou apoie os antebraços, conforme a máquina.'],
      steps: ['Aproxime os braços à frente do peito, acompanhando o arco da máquina.', 'Volte lentamente, sem forçar a abertura atrás do tronco.', 'No bloco combinado, faça as 12 repetições e passe para a flexão.'],
      cues: ['Mantenha as costas apoiadas e os ombros sem subir.', 'A posição das alças varia entre máquinas: confira o ajuste com o professor.'],
      mistakes: ['Tirar as costas do encosto para fechar os braços.', 'Bater a pilha de pesos.', 'Forçar uma abertura desconfortável dos ombros.']
    },
    'push-up': {
      name: 'Flexão de braços', nameEn: 'Push-up',
      equipment: 'Peso corporal + piso firme', equipmentEn: 'Bodyweight + stable floor',
      primary: ['Peitoral maior', 'Tríceps'], secondary: ['Deltoide anterior', 'Abdômen, na estabilização'], muscleIds: ['chest', 'triceps', 'deltoidFront', 'abs'],
      setup: ['Apoie as mãos um pouco além da largura dos ombros.', 'Estenda as pernas e alinhe cabeça, tronco e quadril.'],
      steps: ['Dobre os cotovelos e aproxime o peito do chão, descendo o corpo inteiro junto.', 'Empurre o chão para voltar à posição inicial.', 'Após o peck deck, siga até o limite em que ainda consegue manter a técnica.'],
      cues: ['Cotovelos em diagonal para trás; evite abri-los totalmente.', 'Para aprender, combine com o professor uma versão com mãos elevadas em apoio firme.'],
      mistakes: ['Deixar o quadril cair ou subir primeiro.', 'Projetar só a cabeça para o chão.', 'Continuar quando já não consegue subir com o corpo alinhado.']
    },
    'cable-biceps-curl': {
      name: 'Rosca bíceps na polia', nameEn: 'Cable biceps curl',
      equipment: 'Polia baixa + barra de rosca', equipmentEn: 'Low cable pulley + curl bar',
      primary: ['Bíceps braquial', 'Braquial'], secondary: ['Braquiorradial'], muscleIds: ['biceps', 'forearms'],
      setup: ['De frente para a polia baixa, segure a barra com palmas para cima.', 'Fique ereto, joelhos soltos e cotovelos junto ao corpo.'],
      steps: ['Dobre os cotovelos para aproximar a barra dos ombros.', 'Estenda os braços devagar, mantendo os cotovelos próximos do lugar inicial.'],
      cues: ['Punhos alinhados aos antebraços.', 'Movimente o antebraço; deixe o tronco quieto.'],
      mistakes: ['Balançar o quadril para iniciar a subida.', 'Elevar os ombros.', 'Soltar a barra na volta.']
    },
    'preacher-curl': {
      name: 'Rosca Scott', nameEn: 'Preacher curl',
      equipment: 'Banco Scott + barra EZ · variante de referência', equipmentEn: 'Preacher bench + EZ curl bar · reference variant',
      primary: ['Bíceps braquial', 'Braquial'], secondary: ['Braquiorradial'], muscleIds: ['biceps', 'forearms'],
      setup: ['Ajuste o banco para apoiar a parte de trás dos braços no encosto inclinado.', 'Segure a barra com palmas para cima. Confirme se a ficha usa barra, halteres ou máquina.'],
      steps: ['Dobre os cotovelos e eleve a barra sem tirar os braços do apoio.', 'Desça lentamente, sem forçar o fim da extensão dos cotovelos.'],
      cues: ['Mantenha axilas próximas da borda e ombros estáveis.', 'A barra EZ é apenas a referência deste guia; o aparelho original não foi especificado.'],
      mistakes: ['Quicar a carga no ponto mais baixo.', 'Tirar os braços do banco.', 'Dobrar os punhos para completar a repetição.']
    },
    'reverse-cable-curl': {
      name: 'Rosca inversa na polia · rest-pause', nameEn: 'Reverse cable curl · rest-pause',
      equipment: 'Polia baixa + barra reta', equipmentEn: 'Low cable pulley + straight bar',
      primary: ['Braquiorradial', 'Braquial'], secondary: ['Bíceps braquial', 'Extensores do punho, na estabilização'], muscleIds: ['forearms', 'biceps'],
      setup: ['Fique de frente para a polia baixa, pés firmes e tronco ereto.', 'Segure a barra com as palmas para baixo, mãos próximas da largura dos ombros.'],
      steps: ['Dobre os cotovelos e eleve a barra sem levar os braços para a frente.', 'Desça de forma controlada, com os punhos alinhados.', 'Faça 5 repetições, apoie a carga e descanse 10 s. Repita até completar 4 blocos: isso é 1 série.', 'A ficha pede 2 séries. O descanso de 10 s é entre os blocos, não entre as séries completas.'],
      cues: ['Pegada pronada: dorso das mãos voltado para cima na subida.', 'A ficha diz carga alta; defina a carga com o professor para manter a execução em todos os blocos.'],
      mistakes: ['Deixar os punhos caírem ou dobrarem para trás.', 'Inclinar o tronco para levantar a barra.', 'Confundir os 4 blocos com 4 séries independentes.']
    },
    'floor-crunch': {
      name: 'Abdominal supra · crunch no solo', nameEn: 'Floor crunch',
      equipment: 'Colchonete', equipmentEn: 'Exercise mat',
      primary: ['Reto abdominal'], secondary: ['Oblíquos'], muscleIds: ['abs', 'obliques'],
      setup: ['Deite de costas, dobre os joelhos e apoie os pés.', 'Cruze os braços no peito ou apoie levemente as mãos junto à cabeça.'],
      steps: ['Solte o ar e aproxime as costelas da pelve, elevando a parte alta das costas.', 'Volte devagar, mantendo os pés apoiados. Não é preciso sentar.'],
      cues: ['Movimento curto e controlado; pescoço acompanha o tronco.', 'Supra é o nome usado na ficha, não um músculo separado.'],
      mistakes: ['Puxar a cabeça com as mãos.', 'Usar impulso para sentar.', 'Prender a respiração.']
    },
    'reverse-crunch': {
      name: 'Abdominal infra · crunch reverso', nameEn: 'Supine reverse crunch',
      equipment: 'Colchonete · variante sugerida', equipmentEn: 'Exercise mat · suggested variant',
      primary: ['Reto abdominal'], secondary: ['Oblíquos', 'Flexores do quadril'], muscleIds: ['abs', 'obliques'],
      setup: ['Deite de costas, braços ao lado do corpo e joelhos dobrados sobre o quadril.', 'Mantenha cabeça e ombros apoiados.'],
      steps: ['Enrole a pelve em direção às costelas e tire o quadril apenas um pouco do chão.', 'Desça a pelve lentamente e volte ao início sem embalar as pernas.'],
      cues: ['Pense em levantar o quadril, não em chutar os pés.', 'Sugestão para o infra não especificado: confirme com o professor antes de adotar.'],
      mistakes: ['Balançar as pernas para gerar impulso.', 'Levantar demais o quadril e apoiar o peso no pescoço.', 'Arquear a lombar na volta.']
    },
    'forearm-plank': {
      name: 'Prancha nos antebraços', nameEn: 'Forearm plank',
      equipment: 'Colchonete', equipmentEn: 'Exercise mat',
      primary: ['Abdômen, na estabilização'], secondary: ['Glúteos', 'Cintura escapular'], muscleIds: ['abs', 'obliques', 'glutes', 'deltoidFront'],
      setup: ['Apoie os cotovelos abaixo dos ombros e os antebraços no chão.', 'Estenda as pernas e apoie as pontas dos pés.'],
      steps: ['Eleve o corpo e mantenha cabeça, tronco e quadril alinhados.', 'Respire durante a sustentação. Termine quando não conseguir manter a posição.'],
      cues: ['Contraia levemente glúteos e abdômen.', 'Máximo na ficha significa sustentar com controle, sem compensar para prolongar o tempo.'],
      mistakes: ['Deixar a lombar afundar.', 'Elevar demais o quadril.', 'Prender a respiração.']
    },
    'machine-shoulder-press': {
      name: 'Desenvolvimento na máquina', nameEn: 'Machine shoulder press',
      equipment: 'Máquina de desenvolvimento de ombros', equipmentEn: 'Shoulder press machine',
      primary: ['Deltoide anterior', 'Deltoide lateral'], secondary: ['Tríceps'], muscleIds: ['deltoidFront', 'deltoidSide', 'triceps'],
      setup: ['Ajuste o banco para as alças começarem próximas à altura dos ombros.', 'Apoie costas e pés; segure as alças com punhos alinhados.'],
      steps: ['Empurre as alças para cima seguindo o percurso da máquina.', 'Desça devagar até a amplitude em que mantém ombros e tronco controlados.'],
      cues: ['Mantenha o tronco apoiado.', 'Aumente a carga entre séries somente dentro da execução combinada com o professor.'],
      mistakes: ['Arquear a lombar para empurrar.', 'Encolher os ombros.', 'Bater ou soltar a carga na volta.']
    },
    'dumbbell-lateral-raise': {
      name: 'Elevação lateral com halteres', nameEn: 'Dumbbell lateral raise',
      equipment: 'Dois halteres', equipmentEn: 'Dumbbells',
      primary: ['Deltoide lateral'], secondary: ['Supraespinal', 'Trapézio'], muscleIds: ['deltoidSide', 'traps'],
      setup: ['Fique ereto, com um halter ao lado de cada coxa.', 'Mantenha os cotovelos levemente dobrados e os joelhos soltos.'],
      steps: ['Eleve os braços pelos lados, ligeiramente à frente do tronco, até perto da altura dos ombros.', 'Desça lentamente.', 'Na isometria indicada na ficha, sustente o alto da elevação até perder a posição controlada.'],
      cues: ['Conduza com os braços, sem levantar os ombros.', 'Confirme com o professor em que momento entra a única isometria adicional.'],
      mistakes: ['Dar impulso com as pernas.', 'Girar os polegares forçadamente para baixo.', 'Sustentar a isometria encolhendo os ombros.']
    },
    'cable-front-raise': {
      name: 'Elevação frontal na polia', nameEn: 'Cable front raise',
      equipment: 'Polia baixa + barra curta · referência', equipmentEn: 'Low cable pulley + short bar · reference variant',
      primary: ['Deltoide anterior'], secondary: ['Peitoral maior, porção clavicular'], muscleIds: ['deltoidFront', 'chest'],
      setup: ['Use polia baixa; na referência do guia, fique de costas para ela com o cabo entre as pernas.', 'Segure a barra à frente das coxas, palmas para baixo e cotovelos levemente dobrados.'],
      steps: ['Eleve a barra à frente até perto da altura dos ombros.', 'Volte lentamente à frente das coxas, mantendo o tronco imóvel.'],
      cues: ['Confirme o acessório e a posição usados na sua academia.', 'Punhos alinhados; não precisa levar os braços acima da cabeça.'],
      mistakes: ['Inclinar o corpo para trás.', 'Usar impulso para iniciar.', 'Dobrar muito os cotovelos durante a subida.']
    },
    'dumbbell-shrug': {
      name: 'Encolhimento com halteres', nameEn: 'Dumbbell shrug',
      equipment: 'Dois halteres', equipmentEn: 'Dumbbells',
      primary: ['Trapézio superior'], secondary: ['Levantador da escápula', 'Antebraços, na pegada'], muscleIds: ['traps', 'forearms'],
      setup: ['Fique em pé, braços ao lado do corpo e halteres nas mãos.', 'Mantenha a cabeça alinhada e os cotovelos estendidos sem rigidez.'],
      steps: ['Eleve os ombros em direção às orelhas.', 'Baixe-os lentamente até a posição inicial.'],
      cues: ['Movimento vertical, sem fazer círculos.', 'Olhe à frente e mantenha a pegada firme.'],
      mistakes: ['Girar os ombros para frente e para trás.', 'Dobrar os cotovelos para erguer os pesos.', 'Projetar a cabeça para a frente.']
    },
    'reverse-pec-deck': {
      name: 'Crucifixo inverso na máquina', nameEn: 'Reverse pec deck / rear delt fly',
      equipment: 'Máquina peck deck ajustada para crucifixo inverso', equipmentEn: 'Rear delt / reverse pec deck machine',
      primary: ['Deltoide posterior'], secondary: ['Romboides', 'Trapézio médio'], muscleIds: ['deltoidRear', 'midBack', 'traps'],
      setup: ['Ajuste a máquina para o modo inverso e sente de frente para o encosto.', 'Apoie o peito; deixe as alças próximas à altura dos ombros.'],
      steps: ['Abra os braços para os lados e para trás, seguindo o arco das alças.', 'Retorne à frente lentamente sem perder o apoio do peito.'],
      cues: ['Cotovelos levemente dobrados e no mesmo ângulo.', 'Pescoço relaxado; mantenha o peito no apoio.'],
      mistakes: ['Puxar com impulso do tronco.', 'Encolher os ombros.', 'Dobrar bastante os cotovelos e transformar em remada.']
    },
    'standing-machine-calf-raise': {
      name: 'Panturrilha em pé na máquina', nameEn: 'Standing machine calf raise',
      equipment: 'Máquina de panturrilha em pé', equipmentEn: 'Standing calf raise machine',
      primary: ['Gastrocnêmio', 'Sóleo'], secondary: ['Estabilizadores do tornozelo'], muscleIds: ['calves'],
      setup: ['Ajuste os apoios e posicione a parte da frente dos pés na plataforma.', 'Deixe os calcanhares livres e os joelhos quase estendidos, sem travá-los.'],
      steps: ['Eleve os calcanhares, pressionando a plataforma com a parte da frente dos pés.', 'Desça lentamente até a amplitude confortável.', 'Após 15 repetições, siga para as 20 na escada.'],
      cues: ['Suba e desça sem quicar.', 'Distribua o apoio na parte da frente do pé, sem rolar os tornozelos para fora.'],
      mistakes: ['Impulsionar com joelhos ou quadril.', 'Fazer repetições rápidas e muito curtas.', 'Deixar os pés escorregarem da plataforma.']
    },
    'stair-calf-raise': {
      name: 'Panturrilha no degrau', nameEn: 'Calf raise on a step',
      equipment: 'Degrau firme + corrimão ou apoio', equipmentEn: 'Stable step + hand support',
      primary: ['Gastrocnêmio', 'Sóleo'], secondary: ['Estabilizadores do tornozelo'], muscleIds: ['calves'],
      setup: ['Apoie a parte da frente dos dois pés na borda de um degrau firme.', 'Segure um apoio estável e deixe os calcanhares livres.'],
      steps: ['Suba os calcanhares de forma controlada.', 'Desça lentamente até a amplitude confortável, mantendo o equilíbrio.'],
      cues: ['Use o apoio para equilibrar, sem puxar o corpo.', 'A referência é com os dois pés e peso corporal; carga extra não foi especificada.'],
      mistakes: ['Quicar no ponto mais baixo.', 'Ficar sem apoio em um degrau instável.', 'Deixar o tornozelo tombar para os lados.']
    },
    'lat-pulldown': {
      name: 'Puxada alta', nameEn: 'Lat pulldown',
      equipment: 'Puxador alto + barra longa · referência', equipmentEn: 'Lat pulldown machine + long bar · reference variant',
      primary: ['Latíssimo do dorso'], secondary: ['Bíceps', 'Trapézio inferior', 'Romboides'], muscleIds: ['lats', 'biceps', 'midBack', 'traps'],
      setup: ['Ajuste o apoio das coxas e segure a barra um pouco além da largura dos ombros.', 'Sente com os pés firmes e o peito elevado, sem exagerar o arco lombar.'],
      steps: ['Leve os cotovelos para baixo e puxe a barra à frente, em direção ao alto do peito.', 'Deixe a barra subir devagar enquanto estende os braços.'],
      cues: ['Uma pequena inclinação do tronco pode ficar constante.', 'Pegada de referência: palmas para a frente; confirme a variação da ficha.'],
      mistakes: ['Puxar a barra atrás da nuca.', 'Balançar o tronco para mover a carga.', 'Soltar a volta ou elevar os ombros sem controle.']
    },
    'unilateral-converging-row': {
      name: 'Remada convergente unilateral', nameEn: 'Single-arm converging machine row',
      equipment: 'Máquina de remada convergente com braços independentes', equipmentEn: 'Converging row machine with independent arms',
      primary: ['Latíssimo do dorso', 'Romboides'], secondary: ['Trapézio médio', 'Deltoide posterior', 'Bíceps'], muscleIds: ['lats', 'midBack', 'traps', 'deltoidRear', 'biceps'],
      setup: ['Ajuste banco e apoio peitoral para alcançar a alça sem arredondar o tronco.', 'Segure uma alça; mantenha os pés firmes e o peito apoiado.'],
      steps: ['Puxe o cotovelo para trás, acompanhando o trajeto da máquina.', 'Retorne devagar sem girar o tronco.', 'Faça 10 de um lado, aguarde os 30 s da ficha e execute o outro lado.'],
      cues: ['Deixe a escápula acompanhar o movimento, com controle.', 'Carga alta na ficha: o peito deve continuar apoiado.'],
      mistakes: ['Girar o corpo para terminar a puxada.', 'Elevar o ombro.', 'Soltar o braço para a frente.']
    },
    'seated-cable-row': {
      name: 'Remada baixa na polia', nameEn: 'Seated cable row',
      equipment: 'Polia baixa + pegador triângulo · referência', equipmentEn: 'Seated cable row station + V handle · reference variant',
      primary: ['Latíssimo do dorso', 'Romboides', 'Trapézio médio'], secondary: ['Bíceps', 'Deltoide posterior'], muscleIds: ['lats', 'midBack', 'traps', 'biceps', 'deltoidRear'],
      setup: ['Sente, apoie os pés e deixe os joelhos levemente dobrados.', 'Segure o pegador e mantenha o tronco ereto.'],
      steps: ['Puxe o pegador em direção ao abdômen, levando os cotovelos para trás.', 'Estenda os braços devagar, sem arredondar a lombar.'],
      cues: ['O tronco permanece estável; não use uma grande inclinação para mover o peso.', 'São cinco séries: 20, 15, 12, 10 e 8 repetições, com aumento de carga.'],
      mistakes: ['Remar com balanço da lombar.', 'Encolher os ombros.', 'Dobrar os punhos para puxar mais.']
    },
    'rope-triceps-pushdown': {
      name: 'Tríceps na polia com corda', nameEn: 'Rope triceps pushdown',
      equipment: 'Polia alta + corda', equipmentEn: 'High cable pulley + rope attachment',
      primary: ['Tríceps braquial'], secondary: ['Antebraços, na pegada'], muscleIds: ['triceps', 'forearms'],
      setup: ['De frente para a polia alta, segure as pontas da corda.', 'Aproxime os cotovelos do tronco e mantenha joelhos soltos.'],
      steps: ['Estenda os cotovelos, levando a corda em direção às coxas.', 'Deixe as pontas se afastarem naturalmente ao final e volte devagar.'],
      cues: ['Braços ficam próximos do corpo; o movimento vem dos cotovelos.', 'Punhos firmes, sem dobrar para baixo.'],
      mistakes: ['Empurrar com o peso do tronco.', 'Levar os cotovelos para frente e para trás.', 'Soltar a carga na subida.']
    },
    'dumbbell-lying-triceps-extension': {
      name: 'Tríceps testa com halteres', nameEn: 'Lying dumbbell triceps extension',
      equipment: 'Banco reto + dois halteres', equipmentEn: 'Flat bench + dumbbells',
      primary: ['Tríceps braquial'], secondary: ['Estabilizadores dos ombros'], muscleIds: ['triceps', 'deltoidFront'],
      setup: ['Deite no banco, pés apoiados, segurando um halter em cada mão.', 'Estenda os braços sobre o peito, com as palmas voltadas uma para a outra.'],
      steps: ['Dobre os cotovelos e desça os halteres ao lado da cabeça, com cuidado.', 'Estenda os cotovelos para retornar, sem bater os halteres.'],
      cues: ['Braços ficam relativamente estáveis; antebraços fazem o arco.', 'Escolha uma carga que permita controlar a aproximação da cabeça.'],
      mistakes: ['Abrir muito os cotovelos.', 'Deixar os pesos caírem na descida.', 'Mover os ombros para transformar em supino.']
    },
    'bench-dip': {
      name: 'Tríceps no banco', nameEn: 'Bench dip',
      equipment: 'Banco firme + piso', equipmentEn: 'Stable bench + floor',
      primary: ['Tríceps braquial'], secondary: ['Peitoral maior', 'Deltoide anterior'], muscleIds: ['triceps', 'chest', 'deltoidFront'],
      setup: ['Sente na borda e apoie as mãos ao lado do quadril.', 'Deslize o quadril pouco à frente do banco, com pés apoiados e joelhos dobrados.'],
      steps: ['Dobre os cotovelos para trás e desça apenas até a amplitude confortável dos ombros.', 'Empurre o banco para subir, mantendo o quadril próximo da borda.'],
      cues: ['A versão com joelhos dobrados é a referência de aprendizagem.', 'Peça ao professor para conferir sua amplitude; não force a descida se houver desconforto no ombro.'],
      mistakes: ['Afastar muito o quadril do banco.', 'Descer excessivamente para alcançar uma profundidade fixa.', 'Encolher os ombros ou abrir os cotovelos.']
    },
    'machine-ab-crunch': {
      name: 'Abdominal na máquina · crunch sentado', nameEn: 'Seated machine abdominal crunch',
      equipment: 'Máquina abdominal sentada · identificação provisória', equipmentEn: 'Seated abdominal crunch machine · provisional identification',
      primary: ['Reto abdominal'], secondary: ['Oblíquos'], muscleIds: ['abs', 'obliques'],
      setup: ['Primeiro identifique a máquina com o professor: modelos têm apoios e ajustes diferentes.', 'No modelo sentado, ajuste banco, apoios e carga conforme a placa do aparelho.'],
      steps: ['Com os pés e o quadril apoiados, aproxime as costelas da pelve pelo movimento do tronco.', 'Retorne devagar, acompanhando a máquina sem deixar a carga despencar.'],
      cues: ['As mãos seguram as alças; evite fazer a força principalmente com os braços.', 'Sugestão provisória para o aparelho não especificado na ficha.'],
      mistakes: ['Usar a máquina sem conferir os ajustes.', 'Puxar só com os braços.', 'Continuar no máximo depois de perder o controle do tronco.']
    },
    'leg-extension': {
      name: 'Cadeira extensora', nameEn: 'Leg extension',
      equipment: 'Máquina extensora', equipmentEn: 'Leg extension machine',
      primary: ['Quadríceps'], secondary: [], muscleIds: ['quads'],
      setup: ['Alinhe os joelhos ao eixo da máquina e apoie as costas no encosto.', 'Regule o rolo na parte baixa das canelas, acima dos tornozelos.'],
      steps: ['Estenda os joelhos, elevando o rolo de forma controlada.', 'Dobre os joelhos devagar para voltar à posição inicial.'],
      cues: ['Quadril permanece no assento.', 'A ficha tem 10 séries de 10; combine carga e recuperação com o professor.'],
      mistakes: ['Chutar o rolo com impulso.', 'Levantar o quadril do banco.', 'Soltar o peso na descida.']
    },
    'hack-squat': {
      name: 'Agachamento hack', nameEn: 'Hack squat',
      equipment: 'Máquina hack de agachamento', equipmentEn: 'Hack squat machine',
      primary: ['Quadríceps', 'Glúteo máximo'], secondary: ['Adutores'], muscleIds: ['quads', 'glutes', 'adductors'],
      setup: ['Apoie costas e ombros; posicione os pés na plataforma, em largura confortável.', 'Aprenda a destravar e travar a máquina antes de iniciar.'],
      steps: ['Destrave e dobre joelhos e quadril, mantendo os calcanhares apoiados.', 'Desça até a amplitude em que mantém o controle e a pelve apoiada.', 'Empurre a plataforma para subir; trave a máquina ao terminar.'],
      cues: ['Joelhos acompanham a direção dos pés.', 'A posição dos pés e a profundidade dependem do modelo e do seu ajuste.'],
      mistakes: ['Deixar os joelhos caírem para dentro.', 'Tirar os calcanhares da plataforma.', 'Chegar ao fundo perdendo o apoio da pelve.']
    },
    'lying-leg-curl': {
      name: 'Mesa flexora', nameEn: 'Lying leg curl',
      equipment: 'Máquina flexora deitada', equipmentEn: 'Lying leg curl machine',
      primary: ['Isquiotibiais, posteriores da coxa'], secondary: ['Gastrocnêmio'], muscleIds: ['hamstrings', 'calves'],
      setup: ['Deite de barriga para baixo e alinhe os joelhos ao eixo da máquina.', 'Regule o rolo atrás da parte baixa das pernas, acima dos calcanhares.'],
      steps: ['Dobre os joelhos e aproxime os calcanhares dos glúteos.', 'Estenda as pernas devagar sem deixar a pilha de pesos bater.'],
      cues: ['Quadril e tronco permanecem apoiados.', 'Segure as alças para manter a posição, sem puxar o corpo.'],
      mistakes: ['Levantar o quadril para vencer a carga.', 'Arquear a lombar.', 'Fazer a volta sem controle.']
    },
    'dumbbell-stiff-leg-deadlift': {
      name: 'Stiff com halteres', nameEn: 'Dumbbell stiff-leg deadlift',
      equipment: 'Dois halteres', equipmentEn: 'Dumbbells',
      primary: ['Isquiotibiais, posteriores da coxa', 'Glúteo máximo'], secondary: ['Eretores da coluna, na estabilização', 'Antebraços, na pegada'], muscleIds: ['hamstrings', 'glutes', 'lowerBack', 'forearms'],
      setup: ['Fique em pé, com halteres à frente das coxas e pés próximos da largura do quadril.', 'Mantenha uma pequena flexão dos joelhos, sem travá-los; confirme a variação do stiff com o professor.'],
      steps: ['Leve o quadril para trás e incline o tronco, mantendo os halteres próximos das pernas.', 'Desça só até onde conserva a posição da coluna e sente alongar os posteriores.', 'Traga o quadril à frente para ficar em pé, sem inclinar o tronco para trás.'],
      cues: ['O movimento vem do quadril; o joelho muda pouco de ângulo.', 'Não é necessário alcançar o chão.'],
      mistakes: ['Arredondar a lombar para descer mais.', 'Afastar os halteres das pernas.', 'Dobrar bastante os joelhos e transformar em agachamento.']
    },
    'machine-hip-abduction': {
      name: 'Cadeira abdutora', nameEn: 'Seated hip abduction',
      equipment: 'Máquina abdutora', equipmentEn: 'Seated hip abduction machine',
      primary: ['Glúteo médio', 'Glúteo mínimo'], secondary: ['Tensor da fáscia lata'], muscleIds: ['abductors', 'glutes'],
      setup: ['Sente com costas e pés apoiados conforme o aparelho.', 'Posicione os apoios na parte externa das coxas e escolha uma abertura confortável.'],
      steps: ['Afaste as coxas, empurrando os apoios para fora.', 'Volte lentamente, sem deixar a carga fechar as pernas de uma vez.'],
      cues: ['Abdução é abrir, afastando da linha central do corpo.', 'Depois das 10 repetições, siga para as 10 na adutora.'],
      mistakes: ['Balançar o tronco.', 'Forçar uma abertura excessiva.', 'Deixar a pilha de pesos bater.']
    },
    'machine-hip-adduction': {
      name: 'Cadeira adutora', nameEn: 'Seated hip adduction',
      equipment: 'Máquina adutora', equipmentEn: 'Seated hip adduction machine',
      primary: ['Adutores da coxa'], secondary: [], muscleIds: ['adductors'],
      setup: ['Sente com costas apoiadas e regule a abertura inicial sem forçar.', 'Posicione os apoios na parte interna das coxas.'],
      steps: ['Aproxime as coxas, empurrando os apoios para dentro.', 'Abra lentamente até a posição inicial.'],
      cues: ['Adução é fechar, aproximando da linha central do corpo.', 'Mantenha o quadril no banco durante a abertura e o fechamento.'],
      mistakes: ['Usar uma abertura inicial desconfortável.', 'Fechar com impacto.', 'Inclinar o tronco para ajudar.']
    },
    'alternating-lunge': {
      name: 'Afundo alternado', nameEn: 'Alternating forward lunge',
      equipment: 'Peso corporal ou halteres, conforme a ficha do professor', equipmentEn: 'Bodyweight or dumbbells, as specified by your coach',
      primary: ['Quadríceps', 'Glúteo máximo'], secondary: ['Adutores', 'Glúteo médio', 'Abdômen, na estabilização'], muscleIds: ['quads', 'glutes', 'adductors', 'abductors', 'abs'],
      setup: ['Fique em pé, pés na largura do quadril e espaço livre à frente.', 'Carga e direção não foram detalhadas: o guia usa alternância com passo à frente como referência.'],
      steps: ['Dê um passo à frente e dobre os dois joelhos, baixando o corpo com controle.', 'Empurre o chão com a perna da frente para voltar.', 'Alterne os lados até somar 10 repetições em cada perna.'],
      cues: ['Mantenha os pés em duas linhas paralelas, sem cruzá-los.', 'O joelho da frente acompanha o pé; o tronco fica estável.'],
      mistakes: ['Dar um passo tão estreito que perde o equilíbrio.', 'Deixar o joelho cair para dentro.', 'Contar 10 no total quando a ficha pede 10 por perna.']
    }
  };

  const pilotIds = ['incline-dumbbell-press', 'pec-deck', 'push-up', 'reverse-cable-curl'];
  Object.entries(exercises).forEach(([id, exercise]) => {
    exercise.id = id;
    exercise.pilot = pilotIds.includes(id);
    exercise.media = exercise.pilot ? {
      gif: `assets/animations/${id}.gif`,
      poster: `assets/animations/${id}-poster.webp`,
      frameCount: 16,
      render: 'generated'
    } : null;
    if (id === 'pec-deck') {
      exercise.media = {
        video: 'assets/animations-pec-deck-v5/pec-deck.mp4',
        gif: 'assets/animations-pec-deck-v5/pec-deck.gif',
        poster: 'assets/animations-pec-deck-v5/pec-deck-poster.webp',
        fps: 24,
        frameCount: 72,
        render: 'generated-interpolated',
        legacy: {
          gif: 'assets/animations-pec-deck-v4/pec-deck.gif',
          poster: 'assets/animations-pec-deck-v4/pec-deck-poster.webp',
          frameCount: 72
        }
      };
    }
    if (id === 'reverse-cable-curl') {
      exercise.media.experimental = {
        video: `assets/animations-interpolated/${id}.mp4`,
        gif: `assets/animations-interpolated/${id}.gif`,
        poster: `assets/animations-interpolated/${id}-poster.webp`,
        fps: 24,
        frameCount: 72,
        render: 'generated-interpolated'
      };
    }
  });

  window.GYMROOK_DATA = {
    restNote: 'Descanso informado: revezar entre três amigos; se o revezamento for rápido, no máximo 1 minuto. É o registro da ficha, não uma garantia de recuperação adequada para qualquer pessoa. Confirme o ajuste com o professor.',
    safetyNote: 'Guia de consulta para aprender a ficha. Confira carga, ajustes e execução com o professor. As demonstrações geradas são ilustrativas e precisam de validação técnica; interrompa uma repetição se houver dor ou perda de controle.',
    workouts: [
      {
        id: 'A', name: 'Peito e bíceps', subtitle: 'Chest & biceps',
        blocks: [
          { id: 'a-incline', title: 'Supino inclinado com halteres · 45°', prescription: '4 × 10', note: 'Aumentar a carga a cada série.', exerciseIds: ['incline-dumbbell-press'] },
          { id: 'a-crossover', title: 'Crossover diagonal na polia alta', prescription: '4 × 15', note: '', exerciseIds: ['high-cable-crossover'] },
          { id: 'a-chest-combo', title: 'Peck deck + flexão de braços', prescription: '4 × (12 + falha)', note: 'Faça 12 no peck deck e, em seguida, flexões até a falha. Complete a dupla quatro vezes. Use a perda da técnica como limite.', exerciseIds: ['pec-deck', 'push-up'] },
          { id: 'a-curl', title: 'Rosca bíceps na polia', prescription: '3 × 15', note: '', exerciseIds: ['cable-biceps-curl'] },
          { id: 'a-scott', title: 'Rosca Scott', prescription: '3 × 8–12', note: 'Aparelho/acessório não especificado; o guia mostra a referência com banco e barra EZ.', exerciseIds: ['preacher-curl'] },
          { id: 'a-rest-pause', title: 'Rosca inversa · rest-pause', prescription: '2 séries · 4 blocos de 5', note: 'Carga alta. Em cada série: 5 repetições → 10 s → 5 → 10 s → 5 → 10 s → 5. Descanso entre séries completas conforme orientação do professor.', exerciseIds: ['reverse-cable-curl'] },
          { id: 'a-abs', title: 'Supra + infra + prancha', prescription: '2 voltas · 20 + 20 + máximo', note: '20 supra, 20 infra e prancha pelo tempo máximo com técnica. Sugestão para o infra: crunch reverso deitado, com joelhos dobrados.', exerciseIds: ['floor-crunch', 'reverse-crunch', 'forearm-plank'] }
        ]
      },
      {
        id: 'B', name: 'Ombros e panturrilhas', subtitle: 'Shoulders & calves',
        blocks: [
          { id: 'b-press', title: 'Desenvolvimento na máquina', prescription: '3 × 10', note: 'Aumentar a carga a cada série.', exerciseIds: ['machine-shoulder-press'] },
          { id: 'b-lateral', title: 'Elevação lateral com halteres', prescription: '4 × 15 + 1 isometria', note: 'Isometria no pico até a falha. A ficha não indica em qual série entra a sustentação adicional; confirmar com o professor.', exerciseIds: ['dumbbell-lateral-raise'] },
          { id: 'b-front', title: 'Elevação frontal na polia', prescription: '3 × 12', note: '', exerciseIds: ['cable-front-raise'] },
          { id: 'b-shrug', title: 'Encolhimento com halteres', prescription: '3 × 20', note: '', exerciseIds: ['dumbbell-shrug'] },
          { id: 'b-reverse-fly', title: 'Crucifixo inverso na máquina', prescription: '4 × 12', note: '', exerciseIds: ['reverse-pec-deck'] },
          { id: 'b-calves', title: 'Panturrilha na máquina + no degrau', prescription: '3 voltas · 15 + 20', note: '15 em pé na máquina e, em seguida, 20 no degrau.', exerciseIds: ['standing-machine-calf-raise', 'stair-calf-raise'] }
        ]
      },
      {
        id: 'C', name: 'Costas e tríceps', subtitle: 'Back & triceps',
        blocks: [
          { id: 'c-pulldown', title: 'Puxada alta', prescription: '4 × 12', note: 'Aumentar a carga a cada série.', exerciseIds: ['lat-pulldown'] },
          { id: 'c-unilateral-row', title: 'Remada convergente unilateral', prescription: '3 × 10', note: 'Carga alta. Intervalo de 30 segundos entre os lados.', exerciseIds: ['unilateral-converging-row'] },
          { id: 'c-cable-row', title: 'Remada baixa na polia', prescription: '5 séries · 20 / 15 / 12 / 10 / 8', note: 'Aumentar a carga a cada série.', exerciseIds: ['seated-cable-row'] },
          { id: 'c-rope', title: 'Tríceps na polia com corda', prescription: '3 × 12', note: '', exerciseIds: ['rope-triceps-pushdown'] },
          { id: 'c-extension', title: 'Tríceps testa com halteres', prescription: '3 × 15', note: '', exerciseIds: ['dumbbell-lying-triceps-extension'] },
          { id: 'c-dip', title: 'Tríceps no banco', prescription: '3 × 20', note: '', exerciseIds: ['bench-dip'] },
          { id: 'c-abs', title: 'Abdominal na máquina', prescription: '3 × máximo', note: 'Máximo de repetições com técnica. Referência provisória: máquina de crunch sentado; identifique o modelo com o professor.', exerciseIds: ['machine-ab-crunch'] }
        ]
      },
      {
        id: 'D', name: 'Pernas', subtitle: 'Legs',
        blocks: [
          { id: 'd-extension', title: 'Cadeira extensora', prescription: '10 × 10', note: '', exerciseIds: ['leg-extension'] },
          { id: 'd-hack', title: 'Agachamento hack', prescription: '4 × 8–10', note: '', exerciseIds: ['hack-squat'] },
          { id: 'd-curl', title: 'Mesa flexora', prescription: '3 × 12', note: '', exerciseIds: ['lying-leg-curl'] },
          { id: 'd-stiff', title: 'Stiff com halteres', prescription: '3 × 10', note: '', exerciseIds: ['dumbbell-stiff-leg-deadlift'] },
          { id: 'd-hip-combo', title: 'Abdutora + adutora', prescription: '3 × (10 + 10)', note: '10 repetições abrindo as pernas e 10 fechando, nos respectivos aparelhos.', exerciseIds: ['machine-hip-abduction', 'machine-hip-adduction'] },
          { id: 'd-lunge', title: 'Afundo alternado', prescription: '2 × 10 por perna', note: 'Cada série soma 20 repetições: 10 de cada lado.', exerciseIds: ['alternating-lunge'] }
        ]
      }
    ],
    exercises,
    glossary: [
      { term: 'Série · set', definition: 'Um grupo de repetições. 4 × 10 significa quatro séries de dez repetições.' },
      { term: 'Repetição · rep', definition: 'Um movimento completo de ida e volta, com controle.' },
      { term: 'Combinação · superset', definition: 'Execute os movimentos na ordem indicada e depois repita a dupla ou sequência pelo número de voltas da ficha.' },
      { term: 'Falha · failure', definition: 'Ponto em que não se completa outra repetição. Neste guia, pare ao perder a técnica; não force compensações para prolongar a série.' },
      { term: 'Máximo · max', definition: 'O maior número de repetições ou tempo que você sustenta com técnica, conforme o exercício.' },
      { term: 'Rest-pause', definition: 'Dividir uma série em blocos com pausas curtas. Nesta ficha: quatro blocos de cinco, com 10 segundos entre eles; duas séries completas.' },
      { term: 'Isometria · isometric hold', definition: 'Sustentar uma posição sem movimentar a articulação. Na elevação lateral, a ficha pede uma sustentação no pico.' },
      { term: 'Carga crescente', definition: 'A ficha pede aumentar o peso de uma série para a seguinte. Combine os incrementos com o professor para preservar a execução.' },
      { term: 'Pegada supinada · underhand grip', definition: 'Palmas voltadas para cima ou para a frente, como na rosca direta.' },
      { term: 'Pegada pronada · overhand grip', definition: 'Palmas voltadas para baixo, como na rosca inversa.' },
      { term: 'Pegada neutra · neutral grip', definition: 'Palmas voltadas uma para a outra.' },
      { term: 'Supra e infra', definition: 'Nomes comuns para variantes abdominais. Não são músculos separados: ambas trabalham o reto abdominal, com participação de outros músculos conforme a execução.' },
      { term: 'Abdução e adução', definition: 'Abdução afasta da linha central do corpo; adução aproxima. Na cadeira: abrir e fechar as pernas, respectivamente.' },
      { term: 'Músculos destacados', definition: 'O mapa é esquemático e mostra regiões principais e auxiliares. Não representa intensidade exata, ativação medida ou todos os estabilizadores.' }
    ],
    sources: [
      { title: 'ACE · Incline Chest Press', url: 'https://www.acefitness.org/resources/everyone/exercise-library/25/incline-chest-press/' },
      { title: 'ACE · Pec deck e crossover: orientação de execução', url: 'https://www.acefitness.org/certifiednewsarticle/2884/ace-sponsored-research-top-3-most-effective-chest-exercises/' },
      { title: 'NASM · Push-up', url: 'https://www.nasm.org/resource-center/exercise-library/push-up' },
      { title: 'ACE · Crunch', url: 'https://www.acefitness.org/resources/everyone/exercise-library/52/crunch/' },
      { title: 'ACE · Reverse Ab Crunch', url: 'https://www.acefitness.org/resources/everyone/exercise-library/76/reverse-crunch/' },
      { title: 'ACE · Abdominais superiores e inferiores', url: 'https://www.acefitness.org/continuing-education/prosource/august-2014/4934/can-you-train-upper-and-lower-abs-separately/' },
      { title: 'ACE · Biblioteca de exercícios', url: 'https://www.acefitness.org/resources/everyone/exercise-library/' },
      { title: 'Life Fitness · Instruções de máquinas Circuit Series', url: 'https://kb.cybexintl.com/Product_Info/Life_Fitness_Circuit_Series_Machine_Use_Instructions.pdf' },
      { title: 'NASM · Dumbbell Romanian Deadlift: referência para o movimento do quadril', url: 'https://www.nasm.org/resource-center/exercise-library/dumbbell-romanian-deadlift' }
    ]
  };
})();
