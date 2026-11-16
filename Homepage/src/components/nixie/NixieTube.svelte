<script lang="ts">
  export let digit: string | number = '';
  export let isDot: boolean = false;
  export let scale: number = 1;
  export let active: boolean = true;

  $: currentDigitStr = digit !== undefined && digit !== null ? String(digit) : '';

  // Authentic bent-wire cathode geometry (normalized in 100 x 160 box)
  const wirePaths: Record<string, string> = {
    '0': 'M 50,30 C 31,30 27,56 27,80 C 27,104 31,130 50,130 C 69,130 73,104 73,80 C 73,56 69,30 50,30 Z',
    '1': 'M 38,48 L 52,32 L 52,130 M 36,130 L 68,130',
    '2': 'M 29,54 C 29,35 42,28 52,28 C 64,28 72,37 72,50 C 72,69 56,92 28,130 L 73,130',
    '3': 'M 32,36 C 42,29 61,28 67,37 C 72,46 67,64 54,70 C 69,74 73,92 69,112 C 64,126 44,130 30,123',
    '4': 'M 64,28 L 26,98 L 75,98 M 64,28 L 64,130',
    '5': 'M 70,28 L 35,28 L 31,68 C 37,62 47,60 57,63 C 68,67 72,83 72,99 C 72,116 63,130 48,130 C 36,130 28,122 26,114',
    '6': 'M 64,36 C 45,41 32,68 29,96 C 29,117 39,130 52,130 C 65,130 73,116 73,97 C 73,78 64,66 51,66 C 39,66 31,78 29,96',
    '7': 'M 26,28 L 74,28 C 68,58 56,96 44,130',
    '8': 'M 50,72 C 38,68 33,57 33,46 C 33,35 41,28 50,28 C 59,28 67,35 67,46 C 67,56 61,68 50,72 C 63,76 71,89 71,104 C 71,120 61,130 50,130 C 39,130 29,120 29,104 C 29,89 37,76 50,72 Z',
    '9': 'M 37,124 C 55,119 68,92 71,64 C 71,43 61,30 48,30 C 35,30 27,43 27,63 C 27,82 36,94 49,94 C 61,94 69,82 71,64',
  };

  const allDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
  $: unlitDigits = allDigits.filter((d) => d !== currentDigitStr);

  // Per-tube imperfections: real nixie tubes vary subtly in glow color and stability.
  // Seeded once per component instance so each tube keeps its own character.
  const seed = Math.random();
  const hueShift = ((seed - 0.5) * 12).toFixed(2) + 'deg'; // ±6 deg per-tube color variance
  const bri = (0.95 + seed * 0.1).toFixed(3); // 0.95..1.05 brightness variance
  const flickerDur = (16 + Math.random() * 8).toFixed(2) + 's'; // long cycle: mostly calm, rare blink-outs
  const flickerDelay = (-Math.random() * 16).toFixed(2) + 's'; // negative delay desyncs tubes
  const colorDur = (20 + Math.random() * 10).toFixed(2) + 's'; // slow color drift cycle
  const colorDelay = (-Math.random() * 20).toFixed(2) + 's';
</script>

<div
  class="nixie-tube-unit"
  class:is-dot-unit={isDot}
  style:--custom-scale={scale}
  style:--tube-hue={hueShift}
  style:--tube-bri={bri}
  style:--flicker-dur={flickerDur}
  style:--flicker-delay={flickerDelay}
  style:--color-dur={colorDur}
  style:--color-delay={colorDelay}
>
  {#if isDot}
    <!-- Decimal Dot Pilot Tube -->
    <svg
      viewBox="0 0 60 250"
      class="tube-svg dot-tube-svg"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="dotBrassSocket" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#3a2b0c" />
          <stop offset="30%" stop-color="#c9a232" />
          <stop offset="55%" stop-color="#fae896" />
          <stop offset="80%" stop-color="#a07d1e" />
          <stop offset="100%" stop-color="#2c1f07" />
        </linearGradient>

        <radialGradient id="dotAmberGlow" cx="50%" cy="65%" r="50%">
          <stop offset="0%" stop-color="#ff7700" stop-opacity="0.38" />
          <stop offset="60%" stop-color="#ff3300" stop-opacity="0.1" />
          <stop offset="100%" stop-color="#ff2200" stop-opacity="0" />
        </radialGradient>
      </defs>

      <!-- Soft, delicate vertical shadow of the glass cylinder onto cardboard -->
      <rect x="18" y="90" width="24" height="116" rx="12" fill="#000000" opacity="0.12" filter="blur(5px)" />

      <!-- Contact Shadow on Box Deck -->
      <ellipse cx="30" cy="226" rx="20" ry="7" fill="#000000" opacity="0.55" filter="blur(2px)" />

      <!-- Circular Socket Hole in Top of Metal Box -->
      <ellipse cx="30" cy="216" rx="18" ry="6" fill="#080605" stroke="#251d16" stroke-width="1.2" />

      <!-- Brass Mounting Collar -->
      <path d="M 14,208 C 14,201 46,201 46,208 L 46,218 C 46,225 14,225 14,218 Z" fill="url(#dotBrassSocket)" />
      <ellipse cx="30" cy="208" rx="16" ry="6" fill="#7a5f1e" stroke="#fae896" stroke-width="0.8" />

      <!-- Transparent Vacuum Glass Interior: cardboard shows through -->
      <path
        d="M 15,206 L 15,108 C 15,74 45,74 45,108 L 45,206 Z"
        fill="rgba(255, 255, 255, 0.03)"
      />

      <!-- Amber glow when lit -->
      {#if active}
        <path
          class="glow-live"
          d="M 15,206 L 15,108 C 15,74 45,74 45,108 L 45,206 Z"
          fill="url(#dotAmberGlow)"
        />
      {/if}

      <!-- Internal Neon Pilot Bead -->
      <circle cx="30" cy="162" r="4.5" fill={active ? '#fffdf5' : '#1e1814'} />
      {#if active}
        <circle class="glow-live" cx="30" cy="162" r="11" fill="none" stroke="#ff7700" stroke-width="6" opacity="0.8" filter="blur(2.5px)" />
        <circle class="glow-live" cx="30" cy="162" r="20" fill="none" stroke="#ff2600" stroke-width="8" opacity="0.45" filter="blur(5px)" />
      {/if}

      <!-- Glass Outline & Crisp Specular Glare -->
      <path
        d="M 15,206 L 15,108 C 15,74 45,74 45,108 L 45,206"
        fill="none"
        stroke="rgba(255,255,255,0.28)"
        stroke-width="1.1"
      />
      <ellipse cx="30" cy="96" rx="12" ry="5.5" fill="rgba(255,255,255,0.32)" />
      <ellipse cx="30" cy="85" rx="3.5" ry="2" fill="rgba(255,255,255,0.65)" stroke="#382d24" stroke-width="0.6" />

      <!-- Left Vertical Glass Glare -->
      <path d="M 17,110 L 17,202 L 19,202 L 19,110 Z" fill="rgba(255,255,255,0.35)" />
    </svg>
  {:else}
    <!-- Transparent Glass Digit Nixie Tube with Dark Cold Cathodes and Soft Natural Shadow -->
    <svg
      viewBox="0 0 130 250"
      class="tube-svg"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <!-- Top Mica Spacer Disc Texture -->
        <radialGradient id="micaTextureLarge" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#807267" stop-opacity="0.38" />
          <stop offset="85%" stop-color="#4a3e35" stop-opacity="0.5" />
          <stop offset="100%" stop-color="#2a221a" stop-opacity="0.65" />
        </radialGradient>

        <!-- Brass Socket Collar Gradient -->
        <linearGradient id="brassCollarLarge" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#3c2c0e" />
          <stop offset="25%" stop-color="#cda635" />
          <stop offset="50%" stop-color="#fceda4" />
          <stop offset="75%" stop-color="#b08824" />
          <stop offset="100%" stop-color="#281c06" />
        </linearGradient>

        <!-- Delicate fine wire mesh pattern -->
        <pattern id="anodeScreenFine" width="3.5" height="3.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <path d="M 0,0 L 3.5,0 M 0,0 L 0,3.5" fill="none" stroke="rgba(215, 205, 195, 0.18)" stroke-width="0.55" />
        </pattern>

        <!-- Warm Amber Internal Glow when Active -->
        <radialGradient id="tubeAmberWash" cx="50%" cy="55%" r="50%">
          <stop offset="0%" stop-color="#ff7700" stop-opacity="0.32" />
          <stop offset="55%" stop-color="#ff4400" stop-opacity="0.12" />
          <stop offset="100%" stop-color="#ff2200" stop-opacity="0" />
        </radialGradient>
      </defs>

      <!-- 1. SOFT NATURAL SHADOW OF TUBE ONTO CARDBOARD BACKGROUND BEHIND IT -->
      <rect x="30" y="52" width="70" height="152" rx="20" fill="#000000" opacity="0.14" filter="blur(6px)" />

      <!-- Contact Shadow onto Top Deck of Metal Box -->
      <ellipse cx="65" cy="234" rx="46" ry="11" fill="#000000" opacity="0.55" filter="blur(3px)" />

      <!-- Orange Neon Glow Reflected on Metal Deck Below -->
      {#if active && currentDigitStr !== ''}
        <ellipse class="glow-live" cx="65" cy="234" rx="52" ry="14" fill="#ff4d00" opacity="0.4" filter="blur(5px)" />
        <ellipse class="glow-live" cx="65" cy="230" rx="38" ry="8" fill="#ffaa00" opacity="0.25" filter="blur(2.5px)" />
      {/if}

      <!-- 2. Socket Hole Cutout in Top Face of Metal Box -->
      <ellipse cx="65" cy="222" rx="44" ry="10" fill="#080605" stroke="#251d16" stroke-width="1.3" />

      <!-- 3. Socket Base: Bakelite Rim & Brass Collar in Isometric Ellipse -->
      <g class="socket-base">
        <!-- Lower Bakelite Ring -->
        <path d="M 22,212 C 22,201 108,201 108,212 L 108,223 C 108,234 22,234 22,223 Z" fill="#14110f" stroke="#080605" stroke-width="1" />
        <ellipse cx="65" cy="223" rx="43" ry="11" fill="#1c1613" />

        <!-- Upper Machined Brass Collar Ring -->
        <path d="M 24,204 C 24,194 106,194 106,204 L 106,214 C 106,224 24,224 24,214 Z" fill="url(#brassCollarLarge)" />
        <ellipse cx="65" cy="204" rx="41" ry="10" fill="#88681b" stroke="#fceda4" stroke-width="0.8" />
      </g>

      <!-- 4. CRYSTAL-CLEAR TRANSPARENT GLASS (Cardboard background is fully visible through the tube) -->
      <path
        d="M 25,204 L 25,65 C 25,24 105,24 105,65 L 105,204 Z"
        fill="rgba(255, 255, 255, 0.03)"
      />

      <!-- Warm Amber Internal Glow when Active (illuminates cardboard through clear glass) -->
      {#if active && currentDigitStr !== ''}
        <path
          d="M 26,202 L 26,66 C 26,28 104,28 104,66 L 104,202 Z"
          fill="url(#tubeAmberWash)"
        />
      {/if}

      <!-- Structural Side Steel Support Posts -->
      <line x1="31" y1="52" x2="31" y2="200" stroke="#60544a" stroke-width="1.3" opacity="0.55" />
      <line x1="99" y1="52" x2="99" y2="200" stroke="#4a4038" stroke-width="1.3" opacity="0.55" />

      <!-- Top Mica Insulator Disc (semi-transparent plate) -->
      <ellipse cx="65" cy="52" rx="38" ry="12" fill="url(#micaTextureLarge)" stroke="#685c52" stroke-width="0.7" opacity="0.55" />
      <ellipse cx="52" cy="51" rx="5.5" ry="2.5" fill="#0a0806" opacity="0.5" />
      <ellipse cx="78" cy="51" rx="5.5" ry="2.5" fill="#0a0806" opacity="0.5" />
      <circle cx="31" cy="52" r="1.8" fill="#fff" opacity="0.45" />
      <circle cx="99" cy="52" r="1.8" fill="#fff" opacity="0.45" />

      <!-- Bottom Ceramic Insulator Base -->
      <ellipse cx="65" cy="198" rx="38" ry="11" fill="#241d18" stroke="#3d3128" stroke-width="0.8" opacity="0.6" />

      <!-- Cylindrical Diamond Anode Mesh Screen Cage (Airy, fine transparent mesh) -->
      <rect x="27" y="52" width="76" height="146" fill="url(#anodeScreenFine)" rx="8" opacity="0.75" />

      <!-- 5. UNLIT WIRES IN THE BACKGROUND: DARKER, DISTINCT COLD NICKEL CATHODES -->
      <g class="unlit-wires-background">
        {#each unlitDigits as d, i}
          {@const zOffset = (i - 4.5) * 0.9}
          <g transform="translate({65 + zOffset * 0.6}, {126 - zOffset * 1.2}) scale(0.82) translate(-50, -80)">
            <!-- Wire lead to socket -->
            <line x1="50" y1="130" x2="50" y2="152" stroke="#1c1612" stroke-width="1.2" opacity="0.45" />

            <!-- Darker wire drop shadow -->
            <path
              d={wirePaths[d]}
              fill="none"
              stroke="#000000"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
              opacity="0.35"
              transform="translate(0.5, 0.8)"
            />
            <!-- Darker Cold Nickel Wire Body (distinct, dark bent wire silhouette) -->
            <path
              d={wirePaths[d]}
              fill="none"
              stroke="#221b16"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
              opacity="0.45"
            />
            <!-- Top wire specular metallic edge -->
            <path
              d={wirePaths[d]}
              fill="none"
              stroke="#6d5c4e"
              stroke-width="0.7"
              stroke-linecap="round"
              stroke-linejoin="round"
              opacity="0.4"
            />
          </g>
        {/each}
      </g>

      <!-- 6. ACTIVE GLOWING NUMBER: VIBRANT & IN THE ABSOLUTE FOREGROUND on top of all unlit wires! -->
      {#if active && wirePaths[currentDigitStr]}
        <g
          class="lit-wire-foreground glow-live"
          transform="translate(65, 126) scale(0.84) translate(-50, -80)"
        >
          <!-- Lead wire to socket (ignited) -->
          <line x1="50" y1="130" x2="50" y2="152" stroke="#ff8800" stroke-width="2.4" opacity="0.9" />

          <!-- Layer 1: Broad volumetric gas bloom -->
          <path
            d={wirePaths[currentDigitStr]}
            fill="none"
            stroke="#ff1800"
            stroke-width="24"
            stroke-linecap="round"
            stroke-linejoin="round"
            opacity="0.55"
            filter="blur(7px)"
          />
          <!-- Layer 2: Neon plasma corona -->
          <path
            d={wirePaths[currentDigitStr]}
            fill="none"
            stroke="#ff5500"
            stroke-width="14"
            stroke-linecap="round"
            stroke-linejoin="round"
            opacity="0.95"
            filter="blur(2.6px)"
          />
          <!-- Layer 3: Intense yellow-orange plasma sheath -->
          <path
            d={wirePaths[currentDigitStr]}
            fill="none"
            stroke="#ffa400"
            stroke-width="7.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            opacity="1"
          />
          <!-- Layer 4: Hot white-cream incandescent wire core -->
          <path
            d={wirePaths[currentDigitStr]}
            fill="none"
            stroke="#ffffff"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
            opacity="1"
            filter="drop-shadow(0 0 2px #ffffff)"
          />
          <!-- Layer 5: Townsend violet edge ionization halo -->
          <path
            d={wirePaths[currentDigitStr]}
            fill="none"
            stroke="#6875ff"
            stroke-width="22"
            stroke-linecap="round"
            stroke-linejoin="round"
            opacity="0.18"
            filter="blur(8px)"
          />
        </g>
      {/if}

      <!-- 7. Specular Glare & Curved Glass Rim on Top (Crisp Clear Glass) -->
      <!-- Top Elliptical Dome Highlight -->
      <path
        d="M 28,63 C 28,33 102,33 102,63"
        fill="none"
        stroke="rgba(255,255,255,0.48)"
        stroke-width="2.2"
        stroke-linecap="round"
      />
      <ellipse cx="65" cy="45" rx="33" ry="12" fill="rgba(255,255,255,0.2)" opacity="0.7" />

      <!-- Glass Outline Rim -->
      <path
        d="M 25,204 L 25,65 C 25,24 105,24 105,65 L 105,204"
        fill="none"
        stroke="rgba(255,255,255,0.28)"
        stroke-width="1.2"
      />

      <!-- Exhaust Pip (Glass melt seal on apex of dome) -->
      <ellipse cx="65" cy="23" rx="6" ry="3.5" fill="rgba(255,255,255,0.7)" stroke="#382d24" stroke-width="0.7" />
      <ellipse cx="65" cy="22" rx="2.8" ry="1.4" fill="#ffffff" />

      <!-- Left Vertical Specular Glare Strip -->
      <path
        d="M 27,68 L 27,200 L 32,200 L 32,68 Z"
        fill="rgba(255,255,255,0.32)"
        opacity="0.85"
      />

      <!-- Right Soft Rim Highlight -->
      <path
        d="M 98,68 L 98,200 L 102,200 L 102,68 Z"
        fill="rgba(255,255,255,0.2)"
        opacity="0.7"
      />

      <!-- Orange Neon Glow Reflected on Inner Curved Glass Surface -->
      {#if active && currentDigitStr !== ''}
        <path
          d="M 26,72 L 26,196 L 30,196 L 30,72 Z"
          fill="rgba(255, 140, 0, 0.5)"
          filter="blur(1px)"
        />
        <path
          d="M 98,72 L 98,196 L 102,196 L 102,72 Z"
          fill="rgba(255, 140, 0, 0.45)"
          filter="blur(1px)"
        />
      {/if}
    </svg>
  {/if}
</div>

<style>
  .nixie-tube-unit {
    --base-s: var(--responsive-tube-scale, 1);
    --s: calc(var(--base-s) * var(--custom-scale, 1));
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    user-select: none;
    margin: 0 calc(-2px * var(--s));
    flex-shrink: 0;
  }

  .is-dot-unit {
    margin: 0 calc(-5px * var(--s));
  }

  .tube-svg {
    width: calc(74px * var(--s));
    height: calc(142px * var(--s));
    overflow: visible;
    display: block;
    /* Delicate soft drop shadow onto cardboard behind + subtle per-tube color/brightness variance */
    --tube-shadow: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.15));
    filter: var(--tube-shadow) hue-rotate(var(--tube-hue, 0deg)) brightness(var(--tube-bri, 1));
    animation: tube-color-drift var(--color-dur, 17s) ease-in-out var(--color-delay, 0s) infinite;
  }

  .dot-tube-svg {
    width: calc(36px * var(--s));
    height: calc(142px * var(--s));
    --tube-shadow: drop-shadow(0 3px 5px rgba(0, 0, 0, 0.12));
    filter: var(--tube-shadow) hue-rotate(var(--tube-hue, 0deg)) brightness(var(--tube-bri, 1));
    animation: tube-color-drift var(--color-dur, 17s) ease-in-out var(--color-delay, 0s) infinite;
  }

  /* Plasma flicker: the tube glows steady most of the time, with rare, brief
     blink-outages (with a stutter on recovery) — only the glow layers animate,
     glass, wires and shadows stay rock steady. */
  .glow-live {
    animation: tube-plasma-flicker var(--flicker-dur, 11s) linear var(--flicker-delay, 0s) infinite;
  }

  /* Pilot tubes blink out a little more often than digit cathodes */
  .is-dot-unit .glow-live {
    animation-duration: calc(var(--flicker-dur, 11s) * 0.7);
  }

  @keyframes tube-plasma-flicker {
    0%,
    100% {
      opacity: 1;
    }
    12% {
      opacity: 0.94;
    }
    24% {
      opacity: 0.97;
    }
    /* blink-out #1: a sudden dropout with a stutter on recovery */
    36% {
      opacity: 0.9;
    }
    36.6% {
      opacity: 0.12;
    }
    37.4% {
      opacity: 0.55;
    }
    38.4% {
      opacity: 0.22;
    }
    39.8% {
      opacity: 1;
    }
    55% {
      opacity: 0.93;
    }
    /* blink-out #2: brief dim, then a second sharp dropout */
    70% {
      opacity: 0.85;
    }
    74% {
      opacity: 0.96;
    }
    78.2% {
      opacity: 0.28;
    }
    79% {
      opacity: 0.65;
    }
    80% {
      opacity: 1;
    }
    90% {
      opacity: 0.96;
    }
  }

  /* Slow color drift: the glow's hue wanders slightly around each tube's own
     base tint, like a gas mixture that never burns perfectly the same way. */
  @keyframes tube-color-drift {
    0%,
    100% {
      filter: var(--tube-shadow, none) hue-rotate(var(--tube-hue, 0deg)) brightness(var(--tube-bri, 1));
    }
    30% {
      filter: var(--tube-shadow, none) hue-rotate(calc(var(--tube-hue, 0deg) + 5deg))
        brightness(var(--tube-bri, 1));
    }
    60% {
      filter: var(--tube-shadow, none) hue-rotate(calc(var(--tube-hue, 0deg) - 6deg))
        brightness(calc(var(--tube-bri, 1) * 0.97));
    }
    85% {
      filter: var(--tube-shadow, none) hue-rotate(calc(var(--tube-hue, 0deg) + 2deg))
        brightness(var(--tube-bri, 1));
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .glow-live,
    .tube-svg,
    .dot-tube-svg {
      animation: none;
    }
  }
</style>
