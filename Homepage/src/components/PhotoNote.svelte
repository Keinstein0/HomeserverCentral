<script lang="ts">
    import type { Pin } from "./pin/pin";
    import PinView from "./pin/PinView.svelte";

    export let src: string | undefined = undefined;
    export let alt = "";
    export let caption = "";
    export let frame = "#141414";
    export let pin: Pin | undefined = undefined;
    export let width = "100%";
    export let maxRotation = 4;
    export let maxOffset = 2;

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

<!-- Recolorable pushpin, see Pin.svelte -->
<div
    class="photo-wrapper"
    style:--photo-width={width}
    style:--base-rot="{randomRotate}deg"
    style:--hover-rot="{hoverRotate}deg"
    style:--x-off="{randomX}vw"
    style:--y-off="{randomY}vh"
    style:--frame-color={frame}
>
    {#if pin}
        <PinView {pin} />
    {/if}

    <div class="film-frame">
        <div class="sprocket" aria-hidden="true"></div>

        <div class="film-window">
            <img {src} {alt} class="photo-img" />
        </div>

        <div class="sprocket" aria-hidden="true"></div>

        {#if caption || $$slots.default}
            <div class="film-caption">
                {#if caption}
                    <p>{caption}</p>
                {/if}
                <slot />
            </div>
        {/if}

        <!-- glossy light reflection sweeping across the film -->
        <div class="film-sheen" aria-hidden="true"></div>
    </div>
</div>

<style>
    .photo-wrapper {
        position: relative;
        width: var(--photo-width);
        max-width: 100%;
        transform: rotate(var(--base-rot)) translate(var(--x-off), var(--y-off));
        transition: transform 0.28s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-sizing: border-box;
        display: inline-block;
    }

    .photo-wrapper:hover {
        transform: rotate(var(--hover-rot))
            translate(var(--x-off), var(--y-off)) scale(1.025);
        z-index: 20;
    }

    /* The film strip: dark base, sprocket strips on the left and right */
    .film-frame {
        position: relative;
        display: flex;
        flex-wrap: wrap;
        align-items: stretch;
        box-sizing: border-box;
        background: var(--frame-color);
        background-image: linear-gradient(
            165deg,
            rgba(255, 255, 255, 0.07) 0%,
            transparent 25%,
            rgba(0, 0, 0, 0.25) 100%
        );
        padding: 0.55rem;
        border-radius: 4px;
        box-shadow:
            0 2px 4px rgba(0, 0, 0, 0.14),
            -2px 8px 14px rgba(0, 0, 0, 0.24),
            6px 14px 22px rgba(0, 0, 0, 0.2);
    }

    /* Perforation strips, like the edges of 35mm film */
    .sprocket {
        flex-shrink: 0;
        width: 17px;
        background-image: radial-gradient(
            3.5px 2.5px at 50% 50%,
            rgba(255, 255, 255, 0.16) 55%,
            rgba(255, 255, 255, 0.04) 72%,
            transparent 78%
        );
        background-size: 100% 22px;
        background-repeat: repeat-y;
        background-position: 0 8px;
    }

    .film-window {
        flex: 1;
        min-width: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.45rem 0.55rem;
        border-left: 1px solid rgba(255, 255, 255, 0.07);
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }

    .photo-img {
        display: block;
        max-width: 100%;
        max-height: 340px;
        width: auto;
        height: auto;
        object-fit: contain;
        filter: saturate(0.92) contrast(1.05);
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.09);
    }

    /* Handwritten note in the film's lower margin */
    .film-caption {
        width: 100%;
        font-family: "handwritten", cursive, sans-serif;
        color: #ece7d9;
        text-align: center;
        padding: 0.55rem 0.8rem 0.25rem;
        word-break: break-word;
    }

    .film-caption p {
        margin: 0;
        font-size: 1.05rem;
        line-height: 1.4;
    }

    .film-caption :global(*) {
        margin: 0 0 0.4rem 0;
    }

    .film-caption :global(*:last-child) {
        margin-bottom: 0;
    }

    /* Diagonal glossy reflection over the film surface */
    .film-sheen {
        position: absolute;
        inset: 0;
        pointer-events: none;
        border-radius: 4px;
        background: linear-gradient(
            115deg,
            transparent 26%,
            rgba(255, 255, 255, 0.07) 38%,
            rgba(255, 255, 255, 0.2) 46%,
            rgba(255, 255, 255, 0.06) 55%,
            transparent 66%
        );
    }
</style>
