/* Original, scalable anatomical illustration for the exercise guide.
 * The silhouettes are schematic surface anatomy, not a measured activation map.
 * Curved muscle bellies, separate tendons and paired regions stay fixed between exercises.
 */
(() => {
  'use strict';
  const COLORS = { rest: '#30332f', primary: '#ef5148', secondary: '#e9a29d' };
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const escape = value => String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const array = value => Array.isArray(value) ? value : [];
  const aliases = {
    chest: /peitoral|peito|chest|pector/,
    deltoidFront: /deltoide anterior|ombro anterior|anterior do ombro|cintura escapular/,
    deltoidSide: /deltoide lateral|ombro lateral/,
    deltoidRear: /deltoide posterior|ombro posterior/,
    biceps: /biceps/,
    brachialis: /^braquial(?:\s|,|$)/,
    triceps: /triceps/,
    forearms: /antebraco|forearm|braquiorradial|punho|pegada/,
    brachioradialis: /braquiorradial|antebraco|forearm/,
    wristFlexors: /flexores do punho|antebraco|forearm|pegada/,
    wristExtensors: /extensores do punho|antebraco|forearm|pegada/,
    abs: /abdomen|abdomina|abdominal/,
    obliques: /obliquo|abdomen/,
    lats: /latissimo|grande dorsal|dorsal|latissimus/,
    traps: /trapezio|trapezius/,
    midBack: /romboide|meio das costas|rhomboid/,
    lowerBack: /lombar|eretores|erector/,
    glutes: /gluteo|gluteus/,
    quads: /quadriceps|reto femoral|vasto/,
    hamstrings: /posterior.*coxa|isquiotibi|semitend|semimembr|biceps femoral|hamstring/,
    calves: /panturrilha|gastrocnemio|soleo|calf/,
    adductors: /adutor|adductor/,
    abductors: /abdutor|abductor|gluteo medio|gluteo minimo/
  };

  function levelFor(exercise, group, region) {
    const active = array(exercise.muscleIds);
    if (!active.includes(group)) return 'rest';
    if (array(exercise.primaryMuscleIds).includes(group)) return 'primary';
    if (array(exercise.secondaryMuscleIds).includes(group)) return 'secondary';
    const regex = aliases[region] || aliases[group];
    const matches = values => regex && array(values).some(value => regex.test(normalize(value)));
    if (matches(exercise.primary)) return 'primary';
    if (matches(exercise.secondary)) return 'secondary';
    // The finer arm regions should not inherit a neighbouring muscle's emphasis.
    if (region === 'brachialis' || region === 'wristFlexors' || region === 'wristExtensors') return 'rest';
    return 'primary';
  }

  window.GYMROOK_ANATOMY = exercise => {
    exercise = exercise || {};
    function muscle(group, d, region = group, mirrored = true) {
      const level = levelFor(exercise, group, region);
      const attributes = `data-muscle="${group}" data-region="${region}" data-emphasis="${level}" fill="${COLORS[level]}"`;
      const shape = `<path ${attributes} d="${d}"/>`;
      return mirrored ? `${shape}<path ${attributes} transform="scale(-1 1)" d="${d}"/>` : shape;
    }
    const neutral = (d, mirrored = true) => muscle('structure', d, 'structure', mirrored);
    const line = (d, width = 1.5, mirrored = true) => `<path d="${d}" fill="none" stroke="#fff" stroke-width="${width}" stroke-linecap="round"/>${mirrored ? `<path transform="scale(-1 1)" d="${d}" fill="none" stroke="#fff" stroke-width="${width}" stroke-linecap="round"/>` : ''}`;

    const silhouette = neutral('M-15 99 C-21 122-33 128-58 134 C-87 131-99 146-103 165 C-106 182-112 204-115 223 C-117 232-115 239-112 245 C-125 261-131 287-128 311 L-119 316-108 310 C-98 292-89 269-93 252 C-87 243-79 234-74 217 C-70 204-70 192-73 183 L-64 179 C-64 193-61 204-57 218 C-49 243-44 270-42 291 C-49 307-57 318-61 336 C-70 362-70 392-64 419 C-59 443-53 463-51 474 C-49 483-51 494-56 506 C-67 524-67 548-60 570 C-54 589-48 607-46 620 L-46 629 C-51 638-56 647-55 655 C-48 660-35 661-24 655 C-21 650-26 638-28 631 L-28 612 C-24 593-18 573-16 551 C-12 529-16 508-23 494 C-26 487-28 483-27 478 C-23 463-20 448-18 435 C-11 399-8 370-4 353 L0 350 4 353 C8 370 11 399 18 435 C20 448 23 463 27 478 C28 483 26 487 23 494 C16 508 12 529 16 551 C18 573 24 593 28 612 L28 631 C26 638 21 650 24 655 C35 661 48 660 55 655 C56 647 51 638 46 629 L46 620 C48 607 54 589 60 570 C67 548 67 524 56 506 C51 494 49 483 51 474 C53 463 59 443 64 419 C70 392 70 362 61 336 C57 318 49 307 42 291 C44 270 49 243 57 218 C61 204 64 193 64 179 L73 183 C70 192 70 204 74 217 C79 234 87 243 93 252 C89 269 98 292 108 310 L119 316 128 311 C131 287 125 261 112 245 C115 239 117 232 115 223 C112 204 106 182 103 165 C99 146 87 131 58 134 C33 128 21 122 15 99 C5 103-5 103-15 99Z', false);
    const head = neutral('M0 23 C-18 23-28 32-29 49 L-28 61 C-31 57-35 59-34 67 C-33 75-30 80-26 80 C-23 92-13 101 0 103 C13 101 23 92 26 80 C30 80 33 75 34 67 C35 59 31 57 28 61 L29 49 C28 32 18 23 0 23Z', false);
    const hands = side => `<g transform="translate(-119 313) rotate(17) scale(1.08)" stroke-width="1.5">
      ${neutral('M-9 0 C-14 7-15 17-12 26 L-8 33 C-2 37 6 34 10 27 L12 13 C12 7 8 3 5 0Z', false)}
      ${neutral('M-11 8 C-17 11-22 15-26 21 C-29 25-27 28-24 27 L-12 19Z', false)}
      ${neutral('M-11 24 C-14 31-16 40-16 47 C-16 51-13 51-11 47 L-5 31Z', false)}
      ${neutral('M-5 29 C-8 37-8 47-8 53 C-8 57-4 57-3 53 L2 31Z', false)}
      ${neutral('M2 29 C0 38 0 48 1 53 C2 57 5 56 6 52 L7 29Z', false)}
      ${neutral('M8 26 C7 33 9 42 11 46 C13 50 16 48 15 44 L13 23Z', false)}
      ${side === 'front' ? line('M-8 12 C-3 15 2 17 8 14 M-7 21 C-3 24 1 25 6 22', 1.1, false) : line('M-9 13-8 26 M-3 10-3 28 M3 10 4 27 M8 12 10 24', 1.2, false)}
    </g>`;
    const bothHands = side => `${hands(side)}<g transform="scale(-1 1)">${hands(side)}</g>`;

    const front = [
      silhouette, head,
      // Neck: sternocleidomastoid and visible upper trapezius.
      neutral('M-23 99 C-22 110-15 122-5 133 C-8 121-10 112-11 104 C-16 105-20 102-23 99Z'),
      muscle('traps', 'M-26 111 C-34 124-47 128-61 135 C-49 135-33 139-18 142 C-19 132-23 120-26 111Z'),
      neutral('M-6 117 C-4 120-2 125 0 129 C2 125 4 120 6 117 C7 126 6 134 0 139 C-6 134-7 126-6 117Z', false),
      // Pectoralis major: separate clavicular and broad sternal portions.
      muscle('chest', 'M-5 141 C-19 135-37 134-51 140 C-57 142-61 145-62 148 C-44 147-24 149-5 153Z'),
      muscle('chest', 'M-59 151 C-47 155-28 158-5 158 C-4 168-3 181-6 191 C-18 197-35 192-47 185 C-56 179-62 168-63 160 C-64 155-62 152-59 151Z'),
      // Three-dimensional shoulder caps: the central strip is lateral deltoid.
      muscle('deltoidFront', 'M-63 138 C-72 142-81 153-87 169 C-80 174-72 179-65 184 C-61 169-59 152-63 138Z'),
      muscle('deltoidSide', 'M-68 136 C-85 135-97 148-99 165 C-100 175-98 185-94 193 C-93 174-85 151-68 136Z'),
      // Serratus slips are surface landmarks, not an extra promised target.
      neutral('M-62 187 C-58 191-55 194-49 196 L-46 204 C-55 201-61 197-62 187Z'),
      neutral('M-58 201 C-54 205-50 207-44 209 L-42 217 C-51 214-57 210-58 201Z'),
      neutral('M-54 215 C-49 219-45 221-41 223 L-39 231 C-47 228-52 223-54 215Z'),
      // Upper arms: biceps belly, thin brachialis and lateral triceps visible in front.
      muscle('biceps', 'M-80 176 C-90 181-99 194-101 211 C-103 225-104 237-101 245 C-91 244-82 233-77 217 C-73 202-72 186-80 176Z'),
      muscle('biceps', 'M-75 191 C-71 205-73 220-80 233 C-83 238-86 241-90 242 C-83 229-81 214-81 202Z', 'brachialis'),
      muscle('triceps', 'M-98 181 C-105 193-112 210-112 226 C-112 234-110 239-107 243 C-103 230-102 214-98 202Z'),
      neutral('M-105 244 C-109 245-111 249-109 253 C-106 255-102 252-100 249Z'),
      // Forearm bellies narrow into distinct wrist tendons.
      muscle('forearms', 'M-109 249 C-121 258-127 275-127 291 C-127 298-126 304-123 309 C-118 294-110 276-105 264 C-105 257-106 252-109 249Z', 'brachioradialis'),
      muscle('forearms', 'M-99 253 C-96 266-103 289-116 311 C-114 313-112 314-110 312 C-99 296-91 276-94 261 C-95 257-96 254-99 253Z', 'wristFlexors'),
      muscle('forearms', 'M-105 267 C-107 281-114 300-120 312 C-120 301-116 287-111 275 C-109 271-107 268-105 267Z', 'wristExtensors'),
      neutral('M-118 311-123 310-124 316-118 318Z'),
      // Rectus abdominis is drawn as paired, curved segments with a linea alba gap.
      muscle('abs', 'M-5 199 C-11 195-18 197-22 202 L-22 214 C-15 216-8 215-4 212Z'),
      muscle('abs', 'M-4 220 C-10 217-18 219-22 222 L-22 236 C-15 238-9 238-4 235Z'),
      muscle('abs', 'M-4 243 C-11 241-18 242-22 247 L-22 260 C-16 262-10 263-4 260Z'),
      muscle('abs', 'M-4 268 C-11 265-18 267-22 272 C-22 287-15 302-4 313Z'),
      muscle('obliques', 'M-42 207 C-35 210-29 217-27 226 L-27 268 C-34 261-39 249-42 235 C-44 225-45 216-42 207Z'),
      muscle('obliques', 'M-43 243 C-38 258-31 274-26 284 L-10 316 C-22 309-33 300-40 288 C-44 274-45 258-43 243Z'),
      neutral('M-25 295 C-20 305-12 315-5 321 L-5 334 C-15 325-25 314-32 307Z'),
      neutral('M-40 293 C-48 302-52 316-53 329 C-42 325-31 319-22 319 C-27 311-35 302-40 293Z'),
      neutral('M-18 326 C-13 320-8 318 0 318 C8 318 13 320 18 326 C16 338 9 347 0 350 C-9 347-16 338-18 326Z', false),
      // Hip flexor landmarks, sartorius and adductor/gracilis bands.
      muscle('abductors', 'M-52 320 C-60 329-64 345-63 361 C-58 350-52 341-46 336Z'),
      neutral('M-52 337 C-44 347-34 367-29 386 C-24 405-21 427-21 443 C-25 425-29 405-35 386 C-41 367-50 350-56 343 C-55 340-53 338-52 337Z'),
      muscle('adductors', 'M-12 338 C-23 344-29 358-31 374 L-25 399 C-17 386-12 363-8 344Z'),
      muscle('adductors', 'M-7 348 C-11 376-16 412-21 443 L-24 451 C-24 422-17 379-7 348Z'),
      // Three separately shaped visible quadriceps heads.
      muscle('quads', 'M-54 344 C-63 353-69 377-66 400 C-64 424-55 453-45 468 C-42 455-45 437-49 416 C-53 395-53 371-48 352 C-49 348-51 345-54 344Z'),
      muscle('quads', 'M-38 351 C-46 361-49 382-45 405 C-42 427-36 448-35 464 C-28 452-22 433-21 410 C-20 387-25 362-31 353 C-33 350-36 349-38 351Z'),
      muscle('quads', 'M-24 416 C-18 428-15 443-18 457 C-20 468-28 477-34 474 C-39 470-34 453-29 441 C-27 431-27 423-24 416Z'),
      neutral('M-43 478 C-49 481-49 490-43 494 C-39 497-34 495-31 491 C-27 484-32 477-37 476Z'),
      // Anterior shin includes tibialis, peroneal contour and visible calf edge.
      muscle('calves', 'M-50 494 C-61 503-67 521-64 539 C-62 557-52 574-43 588 C-41 573-44 555-47 538 C-50 520-49 507-46 499Z'),
      neutral('M-39 497 C-32 508-27 528-29 548 C-31 571-33 596-32 620 C-34 624-36 625-38 623 C-42 606-43 586-47 564 C-51 542-50 516-39 497Z'),
      neutral('M-49 548 C-49 571-43 597-41 619 C-42 624-44 627-46 627 C-51 603-55 574-49 548Z'),
      neutral('M-25 546 C-21 567-26 596-30 620 C-31 624-33 626-35 627 C-34 602-30 569-25 546Z'),
      neutral('M-45 626 C-47 634-52 642-54 650 C-51 655-43 657-35 654 L-22 650 C-24 642-28 635-29 627 C-34 631-40 632-45 626Z'),
      // Dorsal foot tendons and individual toe ends.
      line('M-42 633 C-43 641-46 647-49 651 M-36 633-37 652 M-31 634-29 650', 1.35),
      neutral('M-51 652 C-55 653-55 658-52 661 C-48 661-47 657-47 654Z'),
      neutral('M-45 654 C-47 657-46 662-43 662 C-40 661-40 657-41 655Z'),
      neutral('M-38 654 C-40 658-38 663-35 662 C-32 660-33 656-34 654Z'),
      neutral('M-31 652 C-33 656-31 661-28 659 C-26 657-27 654-28 652Z'),
      neutral('M-25 650 C-27 654-24 658-21 655 C-19 653-21 650-22 649Z'),
      bothHands('front')
    ].join('');

    const back = [
      silhouette, head,
      // Trapezius has broad upper fibres and a tapering lower insertion.
      muscle('traps', 'M-11 104 C-15 115-19 126-27 133 C-40 139-53 140-67 145 C-52 148-35 154-20 166 C-12 173-7 184-3 194 L-3 135 C-4 124-7 113-11 104Z'),
      neutral('M-29 116 C-35 127-48 131-61 137 C-47 135-35 131-24 127Z'),
      // Rear and lateral shoulder portions, with an acromial tendon seam.
      muscle('deltoidRear', 'M-68 148 C-78 152-85 166-90 182 C-82 178-74 173-65 172 L-51 172 C-53 161-58 153-68 148Z'),
      muscle('deltoidSide', 'M-73 140 C-89 140-99 153-100 169 C-100 181-97 189-94 194 C-94 176-85 151-73 140Z'),
      neutral('M-61 148 C-52 151-43 159-35 168 L-22 176 C-34 171-47 167-54 162Z'),
      muscle('midBack', 'M-50 177 C-39 175-27 180-14 191 L-13 211 C-27 207-39 199-50 190Z'),
      muscle('midBack', 'M-54 184 C-59 186-62 193-62 202 C-49 206-35 209-22 211 C-35 201-46 192-54 184Z'),
      // Latissimus borders sweep toward the thoracolumbar fascia.
      muscle('lats', 'M-61 207 C-57 230-48 249-32 263 L-7 284 C-12 269-17 251-19 231 L-19 216 C-34 215-49 211-61 207Z'),
      muscle('lowerBack', 'M-8 223 C-16 237-18 255-17 274 L-12 297 C-10 291-6 286-3 282 L-3 230Z'),
      neutral('M-21 270 C-27 281-37 289-45 295 C-30 293-17 297-7 306 L-3 291 C-9 285-15 277-21 270Z'),
      // Triceps long and lateral heads.
      muscle('triceps', 'M-79 180 C-89 185-98 201-101 220 C-102 230-101 239-99 244 C-88 241-79 230-75 216 C-71 202-72 186-79 180Z'),
      muscle('triceps', 'M-97 185 C-106 196-113 213-112 228 C-112 235-109 241-106 244 C-102 231-103 215-98 201Z'),
      muscle('biceps', 'M-74 196 C-70 209-74 227-83 239 C-86 242-88 242-89 241 C-81 227-79 212-74 196Z', 'brachialis'),
      neutral('M-103 244 C-108 244-111 248-109 252 C-106 255-102 252-100 249Z'),
      muscle('forearms', 'M-109 249 C-121 258-127 275-127 291 C-127 299-125 305-123 309 C-118 294-110 275-105 263 C-105 257-106 252-109 249Z', 'brachioradialis'),
      muscle('forearms', 'M-99 253 C-96 267-103 291-116 311 C-114 313-112 314-110 312 C-99 296-91 276-94 261 C-95 257-96 254-99 253Z', 'wristExtensors'),
      muscle('forearms', 'M-105 267 C-108 282-115 301-120 312 C-120 301-115 284-111 275 C-109 271-107 268-105 267Z', 'wristFlexors'),
      neutral('M-118 311-123 310-124 316-118 318Z'),
      // Gluteal upper edge and separate gluteus maximus bellies.
      muscle('abductors', 'M-46 298 C-56 304-62 318-60 332 C-59 338-57 341-54 343 C-51 326-45 313-37 305 C-40 301-43 299-46 298Z'),
      muscle('glutes', 'M-5 304 C-21 296-43 304-52 321 C-59 334-55 347-43 353 C-31 359-13 353-4 339 C-3 327-3 313-5 304Z'),
      neutral('M-4 342 C-10 349-15 356-17 364 L0 355 17 364 C15 356 10 349 4 342Z', false),
      // Posterior thigh: biceps femoris and both medial hamstring bellies.
      muscle('hamstrings', 'M-51 354 C-60 372-63 397-59 419 C-56 442-50 463-45 478 C-38 463-39 443-43 420 C-46 398-47 376-43 359Z'),
      muscle('hamstrings', 'M-37 358 C-42 379-41 404-37 424 C-34 444-34 461-38 477 C-30 469-26 452-26 431 C-26 407-28 382-31 360Z'),
      muscle('hamstrings', 'M-22 355 C-16 364-12 381-13 401 C-13 424-19 449-26 468 C-27 448-23 429-23 409 C-23 388-25 369-27 360Z'),
      muscle('adductors', 'M-9 359 C-9 383-12 411-17 435 L-22 456 C-20 428-16 389-9 359Z'),
      neutral('M-44 480 C-48 485-47 492-42 496 C-37 493-31 488-29 481 L-34 478Z'),
      // Gastrocnemius medial/lateral heads, soleus edges, Achilles tendon.
      muscle('calves', 'M-47 497 C-61 504-67 522-63 540 C-60 557-50 572-42 581 C-38 567-39 551-41 535 C-44 519-44 507-43 500Z'),
      muscle('calves', 'M-36 496 C-24 494-16 508-16 525 C-16 546-28 571-39 586 C-39 570-35 554-35 539 C-35 522-35 508-36 496Z'),
      muscle('calves', 'M-62 541 C-60 562-49 588-44 606 C-43 611-42 615-41 618 C-39 599-42 583-49 565 C-54 553-58 545-62 541Z'),
      muscle('calves', 'M-18 544 C-19 568-29 593-34 611 C-35 616-36 619-38 622 C-36 598-31 574-23 553 C-21 549-19 546-18 544Z'),
      neutral('M-40 583 C-40 597-41 613-39 628 L-33 628 C-34 611-35 597-36 585Z'),
      neutral('M-43 628 C-46 637-47 646-43 653 C-39 659-30 660-25 654 L-26 644 C-29 637-29 632-29 627 C-33 632-39 632-43 628Z'),
      line('M-39 636 C-41 643-39 649-34 653 M-30 638 C-30 644-29 649-28 653', 1.2),
      bothHands('back')
    ].join('');

    const description = [
      array(exercise.primary).length ? `Principais: ${array(exercise.primary).join(', ')}.` : '',
      array(exercise.secondary).length ? `Auxiliares: ${array(exercise.secondary).join(', ')}.` : ''
    ].join(' ');
    return `<svg class="anatomy-svg anatomy-detailed" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 700" role="img" aria-label="Mapa anatômico de frente e costas. ${escape(description)}" style="display:block;width:100%;height:auto;aspect-ratio:640/700;background:#fff;overflow:visible">
      <title>Músculos envolvidos no exercício</title>
      <desc>${escape(description)} Os destaques indicam regiões musculares, sem medir intensidade de ativação.</desc>
      <g class="gr-anatomical-drawing" stroke="#fff" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">
        <g data-view="front" transform="translate(160 4)">${front}</g>
        <g data-view="back" transform="translate(480 4)">${back}</g>
      </g>
      <g fill="#70766e" font-family="system-ui,-apple-system,sans-serif" font-size="12" font-weight="600" letter-spacing="2">
        <text x="160" y="693" text-anchor="middle">FRENTE</text>
        <text x="480" y="693" text-anchor="middle">COSTAS</text>
      </g>
    </svg>`;
  };
})();
