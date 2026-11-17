<script lang="ts">
    import PaperNote from "../components/PaperNote.svelte";
    import PhotoNote from "../components/PhotoNote.svelte";
    import Grid from "../components/Grid.svelte";

    import me from "../assets/images/me.jpg";
    import { Pin } from "../components/pin/pin";
    import NixieAgeCounter from "../components/nixie/NixieAgeCounter.svelte";
    import { onMount } from "svelte";
    const MainPin = new Pin("#ff0000");

    // Shared green for the "My story" note and its timeline entries.
    const storyGreen = "#bfe8a8";

    // Demo story events; the timeline renders them most recent first.
    const storyEvents = [
        {
            date: "November 2026",
            title: "This website goes live",
            text: "Built my own homepage with Svelte, Docker and nginx — you're looking at it, and it runs on my homeserver.",
        },
        {
            date: "June 2026",
            title: "First homeserver",
            text: "Rescued a used mini PC from a flea market. It now runs containers for the whole family and hasn't slept since.",
        },
        {
            date: "August 2024",
            title: "Started the IMS program",
            text: "Enrolled at the Alte Kanti and Berufsbildung Baden — turning ideas into finished products as a daily job.",
        },
        {
            date: "December 2023",
            title: "Hello, Linux",
            text: "Wiped my laptop and installed Fedora. Broke it twice in the first week — and fixed it both times.",
        },
        {
            date: "September 2022",
            title: "First line of code",
            text: "A tiny game made of copy-pasted tutorials. It was terrible. I was hooked anyway.",
        },
    ];

    // Red thread tying the story notes' left pin heads together. The
    // sag curves are measured from the live DOM — the pins ride along
    // with each note's random jitter and rotation — then drawn as SVG
    // curves that hang with slack between the notes, like thread
    // obeying gravity on a real corkboard.
    let storyStackEl: HTMLElement | undefined;
    let threadBox = { w: 0, h: 0 };
    let threadPaths: string[] = [];

    function measureThread() {
        if (!storyStackEl) return;
        const stack = storyStackEl.getBoundingClientRect();
        threadBox = { w: stack.width, h: stack.height };

        // Anchor the thread to each note's left pin *head*. The head
        // sits off-center inside the pin artwork (see pin.ts anchor)
        // and the whole note is tilted by --base-rot, so the head is
        // derived from the pin image's live box, its anchor fractions
        // and the wrapper's rotation — exact for any jitter/rotation.
        const pins: { x: number; y: number }[] = [];
        for (const wrapper of storyStackEl.querySelectorAll<HTMLElement>(
            ".note-wrapper",
        )) {
            const img = wrapper.querySelector<HTMLImageElement>("img.pin-img");
            if (!img) continue;
            const rect = img.getBoundingClientRect();
            const ax = parseFloat(img.dataset.anchorX ?? "0.5");
            const ay = parseFloat(img.dataset.anchorY ?? "0.5");
            const size = img.clientWidth; // layout px — unaffected by rotation
            const h = (size * img.naturalHeight) / img.naturalWidth;
            // Head offset from the image center in local px…
            const dx = ax * size - size / 2;
            const dy = ay * h - h / 2;
            // …rotated by the wrapper's tilt, since the pin inherits it.
            const rot =
                (parseFloat(
                    wrapper.style.getPropertyValue("--base-rot") || "0",
                ) *
                    Math.PI) /
                180;
            pins.push({
                x:
                    rect.left +
                    rect.width / 2 +
                    Math.cos(rot) * dx -
                    Math.sin(rot) * dy -
                    stack.left,
                y:
                    rect.top +
                    rect.height / 2 +
                    Math.sin(rot) * dx +
                    Math.cos(rot) * dy -
                    stack.top,
            });
        }

        threadPaths = [];
        for (let i = 0; i + 1 < pins.length; i++) {
            const a = pins[i];
            const b = pins[i + 1];
            const dy = b.y - a.y;
            // Loose thread: leave each pin downwards, dip below the
            // straight line by `sag`, and rise back into the next pin.
            // The bow is small so the curve hugs the notes' margin strip
            // instead of swinging out into the bare corkboard.
            const sag = Math.min(90, Math.max(24, Math.abs(dy) * 0.3));
            const bx = 10;
            threadPaths.push(
                `M ${a.x.toFixed(1)} ${a.y.toFixed(1)} ` +
                    `C ${(a.x - bx).toFixed(1)} ${(a.y + dy * 0.25 + sag).toFixed(1)}, ` +
                    `${(b.x - bx).toFixed(1)} ${(b.y - dy * 0.25 + sag).toFixed(1)}, ` +
                    `${b.x.toFixed(1)} ${b.y.toFixed(1)}`,
            );
        }
    }

    onMount(() => {
        // Stagger the notes horizontally into a zig-zag: even notes lean
        // right, odd notes lean left (random magnitude), so the column
        // reads as deliberately staggered instead of random noise.
        storyStackEl
            ?.querySelectorAll<HTMLElement>(".note-wrapper")
            .forEach((el, i) => {
                const sign = i % 2 === 0 ? -1 : 1;
                const mag = Math.round(Math.random() * 25 + 8);
                el.style.marginLeft = `${sign * mag}px`;
            });

        measureThread();
        // The board keeps settling for a few frames after mount
        // (webfont swap, image decode, scrollbar) and a ResizeObserver
        // only sees size changes, so re-measure on every animation
        // frame until the geometry holds still for several in a row.
        let last = "";
        let stable = 0;
        let frames = 0;
        let raf = 0;
        const settle = () => {
            measureThread();
            const sig = `${threadBox.w}x${threadBox.h}|${threadPaths.join("|")}`;
            stable = sig === last ? stable + 1 : 0;
            last = sig;
            frames += 1;
            if (stable < 4 && frames < 180) raf = requestAnimationFrame(settle);
        };
        raf = requestAnimationFrame(settle);
        // Belt and braces for fonts that land after the settle window.
        document.fonts?.ready.then(measureThread);
        const observer =
            typeof ResizeObserver === "undefined"
                ? undefined
                : new ResizeObserver(measureThread);
        if (observer && storyStackEl) {
            observer.observe(storyStackEl);
            for (const wrapper of storyStackEl.querySelectorAll(
                ".note-wrapper",
            )) {
                observer.observe(wrapper);
            }
        }
        return () => {
            cancelAnimationFrame(raf);
            observer?.disconnect();
        };
    });
</script>

<main class="board">
    <header class="title-container">
        <PaperNote
            variant="lined"
            color="#cbf5e1"
            pin={MainPin}
            width="min(560px, 94vw)"
            maxRotation={2}
        >
            <h1 class="main-title">Welcome to my website</h1>
            <p
                style="text-align: center; margin-top: 0.2rem; font-weight: regular; font-size: 24px;"
            >
                I hope you enjoy it
            </p>
        </PaperNote>
    </header>

    <Grid gap="2.5rem 2.25rem">
        <PhotoNote src={me} alt="a picture of me" pin={MainPin}>
            <h2>that's me :D</h2>
            <p style="font-size: 10px;">
                Actually why am I putting my face on the internet?
            </p>
        </PhotoNote>

        <PaperNote class="about-me" color="#e8da89" pin={MainPin} width="55%">
            <h2>About me:</h2>
            <p style="font-size: 20px;">
                Hi, I'm Alexander Straub, and I'm currently enrolled in the IMS
                program at the Alte Kanti and the Berufsbildung Baden. <br />
                For me, the most exciting thing about computer science is
                <b>turning ideas into finished products</b>. Does that sound
                generic? Yes it does. But I still love seeing an idea or
                architecture go from a piece of paper to something that actually
                runs.
            </p>
        </PaperNote>

        <div class="nixie-age-counter-container">
            <NixieAgeCounter
                birthDate="2008-09-24-00:00"
                decimals={8}
                label="MY AGE"
            />
        </div>

        <div class="story-stack" bind:this={storyStackEl}>
            <PaperNote
                color={storyGreen}
                pin={MainPin}
                pinLayout="corners"
                width="min(560px, 100%)"
            >
                <h2>My story</h2>
            </PaperNote>

            <div class="story-timeline">
                {#each storyEvents as event}
                    <PaperNote
                        color={storyGreen}
                        pin={MainPin}
                        width="min(480px, 100%)"
                        maxOffset={1.5}
                        pinLayout="corners"
                    >
                        <p class="event-date">{event.date}</p>
                        <h3>{event.title}</h3>
                        <p>{event.text}</p>
                    </PaperNote>
                {/each}
            </div>

            <svg
                class="red-string"
                viewBox="0 0 {threadBox.w} {threadBox.h}"
                aria-hidden="true"
            >
                {#each threadPaths as d}
                    <path {d} />
                {/each}
            </svg>
        </div>
    </Grid>
</main>

<style>
    @font-face {
        font-family: "handwritten";
        src: url("./../assets/dreaming-outloud-pro-regular.otf")
            format("opentype");
    }

    :global(body) {
        margin: 0;
        min-height: 100vh;
        background-image: url("./../assets/cardboard.webp");
        /* The texture tiles cleanly in X and Y, so scale the tiles down
           (75% = tile edges at three-quarter size) for a finer grain. */
        background-size: 75%;
        background-position: center;
        background-repeat: repeat;
        background-color: #2b221a;
        font-family: "handwritten", cursive, sans-serif;
    }

    .board {
        max-width: 1120px;
        margin: 0 auto;
        padding: 2.5rem 1.25rem 4rem;
        box-sizing: border-box;
    }

    .title-container {
        display: flex;
        justify-content: center;
        margin-bottom: 6rem;
    }
    /* .about-me targets the .note-wrapper inside PaperNote, which is the
       grid item — so it must be :global from this scoped stylesheet. */
    :global(.about-me) {
        justify-self: center;
    }

    /* Only span two columns once the grid actually has two columns
       (2 × 280px min column + 2.25rem gap). */
    @media (min-width: 620px) {
        :global(.about-me) {
            grid-column: span 2;
        }
    }

    :global(.nixie-age-counter-container) {
        justify-self: center;
    }

    /* Only span two columns once the grid actually has two columns
       (2 × 280px min column + 2.25rem gap). */
    @media (min-width: 650px) {
        :global(.nixie-age-counter-container) {
            grid-column: span 2;
        }
    }

    .main-title {
        font-size: 3rem;
        letter-spacing: 1px;
        margin: 0;
    }

    /* Story stack: header note + pinned timeline. Spans the full row by
       default; parked in the third column once the grid has three. */
    .story-stack {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        grid-column: 1 / -1;
    }

    /* Three columns fit once 3 × 280px min + 2 × 2.25rem gaps + board
       padding do — 1000px viewport leaves room for the scrollbar.
       Below that the stack keeps its full-width row under the counter. */
    @media (min-width: 1000px) {
        .story-stack {
            grid-column: 3;
        }
    }

    .story-timeline {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2.25rem;
        margin-top: 3rem;
        width: 100%;
    }

    /* Date line above each event title. Kept more specific than
       PaperNote's generic `.content p` rule so it wins the cascade. */
    .story-timeline p.event-date {
        font-size: 0.95rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        opacity: 0.72;
        margin-bottom: 0.35rem;
    }

    /* Red thread: an SVG overlay strung *between* the note paper and the
       pins — the paper layer sits at z-index 1 (PaperNote), the pins at
       z-index 25 (PinView), so the thread at z-index 2 runs in front of
       the paper but behind every pin head. */
    .red-string {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: visible;
        pointer-events: none;
        z-index: 2;
        filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.35));
    }

    .red-string path {
        fill: none;
        stroke: rgba(178, 34, 34, 0.9);
        stroke-width: 2;
        stroke-linecap: round;
    }
</style>
