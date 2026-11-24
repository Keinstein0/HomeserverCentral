<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import NixieTube from "./NixieTube.svelte";
  import scratchedMetalTile from "./../../assets/scratched-metal-tile.webp";

  // Configuration is done in code — adjust these props in App.svelte.
  /** Engraved nameplate text; set to '' to omit the plate entirely */
  export let birthDate: string = "2008-04-15T08:00";
  export let decimals: number = 8;
  export let label: string = "MY AGE";
  export let showDeckHue: boolean = true;

  const MS_PER_YEAR = 1000 * 60 * 60 * 24 * 365.2425;

  let wholeDigits: string[] = ["1", "8"];
  let fracDigits: string[] = [];

  let animFrameId: number;

  function updateAge() {
    const birthTimestamp = new Date(birthDate).getTime();
    if (!isNaN(birthTimestamp)) {
      const now = Date.now();
      const ageInYears = (now - birthTimestamp) / MS_PER_YEAR;

      if (ageInYears >= 0) {
        const [whole, frac] = ageInYears.toFixed(decimals).split(".");
        wholeDigits = whole.padStart(2, "0").split("");
        fracDigits = (frac || "").split("");
      }
    }
    animFrameId = requestAnimationFrame(updateAge);
  }

  onMount(() => {
    animFrameId = requestAnimationFrame(updateAge);
  });

  onDestroy(() => {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
    }
  });
</script>

<div class="physical-apparatus">
  <!-- Tubes standing freely in open space; cardboard background shows through transparent glass -->
  <div class="tubes-row">
    <!-- Whole year digits -->
    <div class="digits-group integer-group">
      {#each wholeDigits as d}
        <NixieTube digit={d} />
      {/each}
    </div>

    <!-- Neon Decimal Dot Bulb -->
    <div class="dot-separator">
      <NixieTube isDot={true} active={true} />
    </div>

    <!-- Fractional decimal tubes (fast ticking digits) -->
    <div class="digits-group fractional-group">
      {#each fracDigits as d}
        <NixieTube digit={d} />
      {/each}
    </div>
  </div>

  <!-- Real Scratched Metal Enclosure Box underneath the tubes (Repeating 1:1 Pixel-Sharp Texture) -->
  <div class="metal-chassis-box">
    <!-- Top Deck Surface where tubes are plugged in -->
    <div
      class="chassis-top-deck"
      style:background-image="linear-gradient(180deg, rgba(255, 255, 255, 0.22)
      0%, transparent 60%), url({scratchedMetalTile})"
    >
      {#if showDeckHue}
        <div class="neon-deck-reflection"></div>
      {/if}
      <div class="socket-runway"></div>
    </div>

    <!-- Front Face of the Box using seamless 1:1 repeating scratched metal -->
    <div
      class="chassis-front-face"
      style:background-image="linear-gradient(180deg, rgba(255, 255, 255, 0.1)
      0%, rgba(0, 0, 0, 0.25) 100%), url({scratchedMetalTile})"
    >
      <!-- Four Industrial Screws with varied slot angles -->
      <div class="bolt-socket top-left">
        <span class="slotted-screw screw-rot-1"></span>
      </div>
      <div class="bolt-socket top-right">
        <span class="slotted-screw screw-rot-2"></span>
      </div>
      <div class="bolt-socket bottom-left">
        <span class="slotted-screw screw-rot-3"></span>
      </div>
      <div class="bolt-socket bottom-right">
        <span class="slotted-screw screw-rot-4"></span>
      </div>

      {#if label}
        <!-- Label machine-engraved directly into the chassis face -->
        <span class="engraved-label">{label}</span>
      {/if}
    </div>

    <!-- Soft Realistic Cast Ground Shadow onto Cardboard Background -->
    <div class="chassis-ground-shadow"></div>
  </div>
</div>

<style>
  .physical-apparatus {
    width: 100%;
    max-width: 1040px;
    margin: 2.2rem auto 3.8rem;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    padding: 0 16px;
  }

  /* Tubes stand directly in open air; cardboard shows through transparent glass */
  .tubes-row {
    --responsive-tube-scale: 1;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    position: relative;
    z-index: 5;
    margin-bottom: -18px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    width: 100%;
  }

  @media (max-width: 960px) {
    .tubes-row {
      --responsive-tube-scale: 0.85;
    }
  }

  @media (max-width: 760px) {
    .tubes-row {
      --responsive-tube-scale: 0.68;
    }
  }

  @media (max-width: 500px) {
    .tubes-row {
      --responsive-tube-scale: 0.44;
      margin-bottom: -12px;
    }
  }

  @media (max-width: 380px) {
    .tubes-row {
      --responsive-tube-scale: 0.38;
      margin-bottom: -10px;
    }
  }

  .digits-group {
    display: flex;
    align-items: flex-end;
    overflow-x: hidden;
  }

  .dot-separator {
    display: flex;
    align-items: flex-end;
  }

  /* Soft Natural Box Shadows onto the Cardboard */
  .metal-chassis-box {
    position: relative;
    width: 100%;
    max-width: 980px;
    box-sizing: border-box;
    z-index: 2;
    /* Soft, subtle natural drop shadow */
    box-shadow:
      0 10px 22px rgba(0, 0, 0, 0.28),
      0 3px 6px rgba(0, 0, 0, 0.18);
    border-radius: 8px;
  }

  /* Top Deck of the Metal Box: 1:1 Pixel-Sharp Tiling */
  .chassis-top-deck {
    height: 30px;
    width: 100%;
    background-repeat: repeat-x;
    background-size: 547px auto;
    background-position: top left;
    border-radius: 8px 8px 0 0;
    border-top: 1.5px solid rgba(255, 255, 255, 0.42);
    border-left: 1.5px solid rgba(255, 255, 255, 0.18);
    border-right: 1.5px solid rgba(0, 0, 0, 0.6);
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
  }

  /* Orange neon reflection cast onto the top deck */
  .neon-deck-reflection {
    position: absolute;
    inset: 0;
    background: radial-gradient(
      ellipse at 50% 100%,
      rgba(255, 100, 0, 0.32) 0%,
      rgba(255, 50, 0, 0.1) 55%,
      transparent 80%
    );
    pointer-events: none;
    z-index: 1;
  }

  /* Socket runway / mounting groove on the top deck */
  .socket-runway {
    position: absolute;
    bottom: 2px;
    left: 3%;
    right: 3%;
    height: 14px;
    background: linear-gradient(180deg, #070504 0%, #16120e 100%);
    border-radius: 7px;
    border-top: 1px solid #000;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.85);
    z-index: 2;
  }

  /* Front Face of the Box: 1:1 Pixel-Sharp Repeating Scratches */
  .chassis-front-face {
    position: relative;
    /* Compact face: only the four mounting screws remain */
    padding: 2.5rem 1.8rem 2.2rem;
    background-repeat: repeat-x;
    background-size: 547px auto;
    background-position: left center;
    border-radius: 0 0 8px 8px;
    border-top: 2px solid #554437; /* Bevel edge between top deck and front face */
    border-left: 1.5px solid rgba(255, 255, 255, 0.14);
    border-right: 2px solid #080605;
    border-bottom: 2.5px solid #080605;
    box-shadow:
      inset 0 1px 2px rgba(255, 255, 255, 0.2),
      inset 0 -2px 5px rgba(0, 0, 0, 0.7);
    box-sizing: border-box;
  }

  /* Machined Screw Wells */
  .bolt-socket {
    position: absolute;
    width: 17px;
    height: 17px;
    border-radius: 50%;
    background: #090706;
    box-shadow:
      inset 0 2px 4px rgba(0, 0, 0, 0.95),
      0 1px 1px rgba(255, 255, 255, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 12;
  }

  /* Slotted Industrial Machine Screws */
  .slotted-screw {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: radial-gradient(
      circle at 35% 35%,
      #d0d0d0 0%,
      #777 55%,
      #2a2a2a 100%
    );
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
    position: relative;
  }

  .slotted-screw::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 1.5px;
    right: 1.5px;
    height: 1.8px;
    background: #111;
    transform: translateY(-50%);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.3);
  }

  .screw-rot-1 {
    transform: rotate(34deg);
  }
  .screw-rot-2 {
    transform: rotate(-52deg);
  }
  .screw-rot-3 {
    transform: rotate(18deg);
  }
  .screw-rot-4 {
    transform: rotate(-74deg);
  }

  .top-left {
    top: 11px;
    left: 13px;
  }
  .top-right {
    top: 11px;
    right: 13px;
  }
  .bottom-left {
    bottom: 13px;
    left: 13px;
  }
  .bottom-right {
    bottom: 13px;
    right: 13px;
  }

  /* Label engraved directly into the metal face of the chassis:
     a dark carved impression with the engraved groove's lower
     edge catching a faint glint of light */
  .engraved-label {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-family: "Share Tech Mono", ui-monospace, monospace;
    font-size: 2.3rem;
    letter-spacing: 9px;
    color: rgba(0, 0, 0, 0.82);
    text-shadow:
      /* carved pit shadow */
      0 -1px 1px rgba(0, 0, 0, 0.85),
      /* light glinting off the groove's lower edge */ 0 1px 1px
        rgba(255, 255, 255, 0.32);
    z-index: 12;
    user-select: none;
    white-space: nowrap;
  }

  /* Soft Natural Ground Shadow Cast onto Cardboard Background */
  .chassis-ground-shadow {
    position: absolute;
    bottom: -10px;
    left: 4%;
    right: 4%;
    height: 18px;
    background: rgba(0, 0, 0, 0.35);
    filter: blur(8px);
    border-radius: 50%;
    pointer-events: none;
    z-index: -1;
  }
</style>
