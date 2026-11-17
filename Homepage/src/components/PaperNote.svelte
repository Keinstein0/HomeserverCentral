<script lang="ts">
    import type { Pin } from "./pin/pin";
    import PinView from "./pin/PinView.svelte";

    export let variant: "sticky" | "lined" = "sticky";
    export let color = "#fff677";
    export let pin: Pin | undefined = undefined;
    // "center": one pin top-center (default). "corners": two pins near
    // the top corners — e.g. for threads strung between the left pins.
    export let pinLayout: "center" | "corners" = "center";
    export let width = "100%";
    export let maxRotation = 4;
    export let maxOffset = 2;

    // Extra classes forwarded onto the wrapper element (the grid item),
    // e.g. for grid placement: <PaperNote class="about-me">
    // (`class` is a reserved word in TS, so it can't be a plain `export let`.)
    $: extraClass = ($$props.class as string) ?? "";

    // Random per-instance jitter; computed once on component creation.
    // ($derived is a Svelte 5 rune — this project runs Svelte 4.)
    const randomRotate = (Math.random() * maxRotation * 2 - maxRotation).toFixed(1);
    const randomX = (Math.random() * maxOffset * 2 - maxOffset).toFixed(3);
    const randomY = (Math.random() * maxOffset * 2 - maxOffset).toFixed(3);
    $: hoverRotate = (
        parseFloat(randomRotate) +
        (parseFloat(randomRotate) < 0 ? -2.5 : 2.5)
    ).toFixed(1);
</script>

<!-- Recolorable pushpin, see Pin.svelte. The jitter/hover transform
     lives on the .paper-layer and the .pin-layer (identical transforms)
     instead of on .note-wrapper itself, so wrapper children keep their
     own z-index in the page's stacking context — that lets overlays
     (e.g. the red thread SVG) sit above the paper but below the pins. -->
<!-- Recolorable pushpin, see Pin.svelte. The jitter/hover transform
     lives on the .paper-layer and the .pin-layer (identical transforms)
     instead of on .note-wrapper itself, so wrapper children keep their
     own z-index in the page's stacking context — that lets overlays
     (e.g. the red thread SVG) sit above the paper but below the pins. -->
<div
    class="note-wrapper {extraClass}"
    style:--note-width={width}
    style:--base-rot="{randomRotate}deg"
    style:--hover-rot="{hoverRotate}deg"
    style:--x-off="{randomX}vw"
    style:--y-off="{randomY}vh"
>
    <div class="paper-layer">
        <div
            class="paper"
            class:variant-sticky={variant === "sticky"}
            class:variant-lined={variant === "lined"}
            style:--paper-color={color}
        >
            {#if variant === "lined"}
                <div class="holes-strip" aria-hidden="true">
                    {#each Array(6) as _}
                        <span class="hole"></span>
                    {/each}
                </div>
            {/if}

            <div class="content" class:lined-content={variant === "lined"}>
                <slot />
            </div>
        </div>
    </div>

    {#if pin}
        <!-- Pins live in their own layer carrying the SAME jitter/hover
             transform as .paper-layer, so they stay glued to the paper
             while remaining above the red thread (z-index 2). -->
        <div class="pin-layer">
            {#if pinLayout === "corners"}
                <!-- Both instances share the Pin's tint filter id; the first
                     definition in the DOM wins, and they are identical anyway. -->
                <PinView {pin} x="18%" />
                <PinView {pin} x="82%" />
            {:else}
                <PinView {pin} />
            {/if}
        </div>
    {/if}
</div>

<style>
    .note-wrapper {
        position: relative;
        width: var(--note-width);
        max-width: 100%;
        box-sizing: border-box;
        display: inline-block;
    }

    /* The jitter/hover transform is shared by the paper layer and the
       pins so they always move together (see PinView for the pin side). */
    .paper-layer {
        position: relative;
        z-index: 1;
        transform: rotate(var(--base-rot)) translate(var(--x-off), var(--y-off));
        transition: transform 0.28s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .note-wrapper:hover .paper-layer {
        transform: rotate(var(--hover-rot))
            translate(var(--x-off), var(--y-off)) scale(1.025);
        z-index: 20;
    }

    /* Pin layer: full-size sibling of the paper layer, transformed
       identically so pins rotate about the note's center (not their own)
       and inherit the vw/vh jitter offsets the paper gets. */
    .pin-layer {
        position: absolute;
        inset: 0;
        z-index: 25;
        pointer-events: none;
        transform: rotate(var(--base-rot)) translate(var(--x-off), var(--y-off));
        transition: transform 0.28s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .note-wrapper:hover .pin-layer {
        transform: rotate(var(--hover-rot))
            translate(var(--x-off), var(--y-off)) scale(1.025);
    }

    .paper {
        position: relative;
        box-sizing: border-box;
        background-color: var(--paper-color);
        width: 100%;
        border-radius: 2px 3px 6px 3px;
        border-top: 1px solid rgba(255, 255, 255, 0.45);
        border-left: 1px solid rgba(255, 255, 255, 0.25);
    }

    /* Sticky Variant */
    .variant-sticky {
        padding: 2.2rem 1.6rem 1.6rem;
        background-image: linear-gradient(
            150deg,
            rgba(255, 255, 255, 0.32) 0%,
            transparent 35%,
            rgba(0, 0, 0, 0.03) 80%,
            rgba(0, 0, 0, 0.12) 100%
        );
        box-shadow:
            0 2px 4px rgba(0, 0, 0, 0.1),
            -2px 8px 14px rgba(0, 0, 0, 0.2),
            6px 14px 22px rgba(0, 0, 0, 0.16);
    }

    /* Lined Notebook Variant */
    .variant-lined {
        display: flex;
        flex-direction: row;
        padding: 1.6rem 1.4rem 1.4rem 0.6rem;
        border-radius: 4px;
        background-image: repeating-linear-gradient(
            to bottom,
            transparent,
            transparent 28px,
            rgba(50, 110, 85, 0.22) 29px
        );
        background-size: 100% 29px;
        background-position: 0 18px;
        box-shadow:
            0 2px 5px rgba(0, 0, 0, 0.12),
            -2px 8px 16px rgba(0, 0, 0, 0.22),
            4px 14px 22px rgba(0, 0, 0, 0.18);
    }

    .holes-strip {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        padding: 0 10px;
        user-select: none;
        flex-shrink: 0;
    }

    .hole {
        width: 13px;
        height: 13px;
        border-radius: 50%;
        background: #1e1e1e;
        box-shadow:
            inset 0 1.5px 3px rgba(0, 0, 0, 0.95),
            0 1px 1px rgba(255, 255, 255, 0.4);
        display: block;
        margin: 8px 0;
    }

    .content {
        width: 100%;
        font-family: "handwritten", cursive, sans-serif;
        color: #1a1a1a;
        word-break: break-word;
        box-sizing: border-box;
    }

    .lined-content {
        padding-left: 0.8rem;
        line-height: 29px;
    }

    .content :global(*) {
        margin: 0 0 0.5rem 0;
    }

    .content :global(*:last-child) {
        margin-bottom: 0;
    }

    .content :global(h1),
    .content :global(h2),
    .content :global(h3) {
        font-weight: 700;
        line-height: 1.25;
        text-align: center;
    }

    .content :global(p) {
        line-height: 1.4;
        font-size: 1.15rem;
    }

    .content :global(ul) {
        padding-left: 1.3rem;
        margin: 0.4rem 0;
        font-size: 1.1rem;
    }

    .content :global(li) {
        line-height: 1.3;
        margin-bottom: 0.3rem;
    }
</style>
