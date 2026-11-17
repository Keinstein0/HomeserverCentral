<script lang="ts">
  import type { Pin } from "./pin";

  // Renders a Pin instance; see pin.ts for how to create one.
  // `x` places the pin *head* horizontally (CSS left value) so a note
  // can carry several pins, e.g. x="18%" / x="82%" for corner pins.
  // The margin shift compensates for the artwork's off-center head.
  export let pin: Pin;
  export let x = "50%";
</script>

<svg
  width="0"
  height="0"
  style="position: absolute; pointer-events: none;"
  aria-hidden="true"
>
  <defs>
    <filter id={pin.filterId} color-interpolation-filters="sRGB">
      <!-- 1. Desaturate the red pin to grayscale -->
      <feColorMatrix
        in="SourceGraphic"
        type="saturate"
        values="0"
        result="gray"
      />

      <!-- 2. Normalize luminance so red midtones become bright enough to accept light colors (like yellow/cyan) while keeping white highlights pure white -->
      <feComponentTransfer in="gray" result="lifted">
        <feFuncR type="linear" slope="2.6" intercept="0.12" />
        <feFuncG type="linear" slope="2.6" intercept="0.12" />
        <feFuncB type="linear" slope="2.6" intercept="0.12" />
      </feComponentTransfer>

      <!-- 3. Flood with your exact hex color and multiply it on -->
      <feFlood flood-color={pin.color} result="tint" />
      <feBlend in="lifted" in2="tint" mode="multiply" result="colored" />

      <!-- 4. Keep the baked-in shadow neutral: it is translucent (alpha < 1)
           while the pin body is opaque, so the source alpha acts as the tint
           weight. Opaque pixels get the full color, translucent shadow
           pixels fall back to the untouched grayscale. -->
      <feComponentTransfer in="SourceGraphic" result="w">
        <feFuncA type="table" tableValues="0 0 0 1 1" />
      </feComponentTransfer>
      <feComposite in="colored" in2="w" operator="in" result="coloredW" />
      <feComposite in="coloredW" in2="gray" operator="over" />
    </filter>
  </defs>
</svg>

<img
  src={pin.src}
  class="pin-img"
  width={pin.artwork.width}
  height={pin.artwork.height}
  style:width="{pin.size}px"
  style:left={x}
  style:margin-left="{((0.5 - pin.anchor.x) * pin.size).toFixed(1)}px"
  style:filter="url(#{pin.filterId}) drop-shadow(0 4px 6px rgba(0, 0, 0, 0.45))"
  data-anchor-x={pin.anchor.x}
  data-anchor-y={pin.anchor.y}
  alt="Pushpin"
  aria-hidden="true"
/>

<style>
  .pin-img {
    position: absolute;
    top: -16px;
    left: 50%;
    transform: translateX(-50%);
    height: auto;
    z-index: 25;
    pointer-events: none;
  }
</style>
