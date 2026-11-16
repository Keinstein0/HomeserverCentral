<script lang="ts">
    export let minColumnWidth = "280px";
    export let gap = "2rem";
    export let as: "section" | "div" | "aside" = "section";
</script>

<svelte:element
    this={as}
    class="grid-container"
    style:--min-col-width={minColumnWidth}
    style:--grid-gap={gap}
>
    <slot />
</svelte:element>

<style>
    .grid-container {
        display: grid;
        grid-template-columns: repeat(
            auto-fill,
            minmax(var(--min-col-width), 1fr)
        );
        gap: var(--grid-gap);
        width: 100%;
    }
</style>
