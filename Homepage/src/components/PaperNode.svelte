<script lang="ts">
    export let variant: "sticky" | "lined" = "sticky";
    export let color = "#fff677";
    export let pinSrc: string | undefined = undefined;
    export let pinColor = "#d90000";
    export let width = "100%";
    export let maxRotation = 4;
    export let maxOffset = 2;

    // Unique ID so multiple pins on the same page can have different colors
    const filterId = `pin-tint-${Math.random().toString(36).slice(2, 9)}`;

    const randomRotate = (
        Math.random() * maxRotation * 2 -
        maxRotation
    ).toFixed(1);
    const randomX = (Math.random() * maxOffset * 2 - maxOffset).toFixed(3);
    const randomY = (Math.random() * maxOffset * 2 - maxOffset).toFixed(3);
    const hoverRotate = (
        parseFloat(randomRotate) + (parseFloat(randomRotate) < 0 ? -2.5 : 2.5)
    ).toFixed(1);
</script>

<!-- Hidden SVG filter that recolors the pin to the exact hex code -->
{#if pinSrc}
    <svg
        width="0"
        height="0"
        style="position: absolute; pointer-events: none;"
        aria-hidden="true"
    >
        <defs>
            <filter id={filterId} color-interpolation-filters="sRGB">
                <!-- 1. Desaturate the red pin to grayscale -->
                <feColorMatrix type="saturate" values="0" result="gray" />

                <!-- 2. Normalize luminance so red midtones become bright enough to accept light colors (like yellow/cyan) while keeping white highlights pure white -->
                <feComponentTransfer in="gray" result="normalized">
                    <feFuncR type="linear" slope="1.8" intercept="0.05" />
                    <feFuncG type="linear" slope="1.8" intercept="0.05" />
                    <feFuncB type="linear" slope="1.8" intercept="0.05" />
                </feComponentTransfer>

                <!-- 3. Flood with your exact hex color -->
                <feFlood flood-color={pinColor} result="tint" />

                <!-- 4. Multiply the hex color onto the normalized grayscale pin -->
                <feBlend
                    mode="multiply"
                    in="normalized"
                    in2="tint"
                    result="colored"
                />

                <!-- 5. Clip back to the original image's transparency (alpha channel) -->
                <feComposite in="colored" in2="SourceGraphic" operator="in" />
            </filter>
        </defs>
    </svg>
{/if}

<div
    class="note-wrapper"
    style:--note-width={width}
    style:--base-rot="{randomRotate}deg"
    style:--hover-rot="{hoverRotate}deg"
    style:--x-off="{randomX}vw"
    style:--y-off="{randomY}vh"
>
    {#if pinSrc}
        <img
            src={pinSrc}
            class="pin-img"
            style:filter="url(#{filterId})"
            alt="Pushpin"
            aria-hidden="true"
        />
    {/if}

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

<style>
    .note-wrapper {
        position: relative;
        width: var(--note-width);
        max-width: 100%;
        transform: rotate(var(--base-rot)) translate(var(--x-off), var(--y-off));
        transition: transform 0.28s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-sizing: border-box;
        display: inline-block;
    }

    .note-wrapper:hover {
        transform: rotate(var(--hover-rot))
            translate(var(--x-off), var(--y-off)) scale(1.025);
        z-index: 20;
    }

    .pin-img {
        position: absolute;
        top: -16px;
        left: 50%;
        transform: translateX(-50%);
        width: 44px;
        height: auto;
        z-index: 25;
        pointer-events: none;
        filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.45));
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
