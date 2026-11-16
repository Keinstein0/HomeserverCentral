<script lang="ts">
  import type { Pin } from './pin';

  // Renders a Pin instance; see pin.ts for how to create one.
  let { pin }: { pin: Pin } = $props();
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
      <feColorMatrix in="SourceGraphic" type="saturate" values="0" result="gray" />

      <!-- 2. Normalize luminance so red midtones become bright enough to accept light colors (like yellow/cyan) while keeping white highlights pure white -->
      <feComponentTransfer in="gray" result="lifted">
        <feFuncR type="linear" slope="1.8" intercept="0.05" />
        <feFuncG type="linear" slope="1.8" intercept="0.05" />
        <feFuncB type="linear" slope="1.8" intercept="0.05" />
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
  style:width="{pin.size}px"
  style:filter="url(#{pin.filterId}) drop-shadow(0 4px 6px rgba(0, 0, 0, 0.45))"
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
