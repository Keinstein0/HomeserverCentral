<script lang="ts">
  import type { Pin } from "./pin";

  // Renders a Pin instance; see pin.ts for how to create one.
  // By default `x` places the pin *head* horizontally (CSS left value)
  // and `y` is the image's top edge. With `centered`, the artwork is
  // centered on the x/y point instead — e.g. a pin seated mid-edge of
  // a note: x="5px" y="50%" centered.
  export let pin: Pin;
  export let x: string = "50%";
  export let y: string = "-16px";
  export let centered = false;

  // Vertical compensation for the artwork's off-center head, used when
  // `centered` (mirrors the margin-left shift below, but for the head's
  // height fraction: 0.5 - anchor.y of the displayed artwork height).
  $: headLift = (
    (0.5 - pin.anchor.y) * pin.size * (pin.artwork.height / pin.artwork.width)
  ).toFixed(1);
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
  class:centered={centered}
  width={pin.artwork.width}
  height={pin.artwork.height}
  style:width="{pin.size}px"
  style:top={centered ? "50%" : y}
  style:left={x}
  style:margin-left="{((0.5 - pin.anchor.x) * pin.size).toFixed(1)}px"
  style:margin-top={centered ? "{headLift}px" : undefined}
  style:filter="url(#{pin.filterId})"
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
    /* Jitter/hover transform is applied by the surrounding .pin-layer
       (see PaperNote) — the pin itself only centers horizontally. */
    transform: translateX(-50%);
    height: auto;
    z-index: 25;
    pointer-events: none;
  }

  /* Centered mode: the artwork is centered on the x/y point (the head
     is then nudged onto that point by the margin compensations). */
  .pin-img.centered {
    transform: translate(-50%, -50%);
  }
</style>
