<script lang="ts">
    import PaperNote from "../components/PaperNote.svelte";
    import PhotoNote from "../components/PhotoNote.svelte";
    import Grid from "../components/Grid.svelte";

    import me from "../assets/images/me.jpg";
    import github from "../assets/images/github.png";
    import { Pin } from "../components/pin/pin";
    import NixieAgeCounter from "../components/nixie/NixieAgeCounter.svelte";
    import GitActivityCounter from "../components/git/GitActivityCounter.svelte";
    import { onMount } from "svelte";
    import modernpainterdemo from "../assets/images/modernpainterdemo.gif";
    const MainPin = new Pin("#ff0000");
    const LinkPin = new Pin("#8080ff");

    // Shared green for the "My story" note and its timeline entries.
    const storyGreen = "#bfe8a8";
    // Red for story notes that reference robotics.
    const storyRed = "#f2a9a4";

    // Dedicated robotics page — not defined yet, so it points to
    // example.com for now.
    const roboticsUrl = "https://example.com";

    type TechLink = { label: string; url: string; sep?: string };

    const techCategories: {
        title: string;
        lines: TechLink[][];
    }[] = [
        {
            title: "Programming Languages",
            lines: [
                [
                    {
                        label: "C#",
                        url: "https://dotnet.microsoft.com/languages/csharp",
                    },
                    {
                        label: "(ASP.NET, EF, AOT, MonoGame)",
                        url: "https://dotnet.microsoft.com/languages/csharp",
                        sep: "",
                    },
                ],
                [
                    {
                        label: "Python",
                        url: "https://www.python.org/",
                    },
                    {
                        label: "(Flask, Pygame, ML)",
                        url: "https://www.python.org/",
                        sep: "",
                    },
                ],
                [
                    { label: "Astro", url: "https://astro.build/" },
                    { label: "Svelte", url: "https://svelte.dev/" },
                    { label: "Node.js", url: "https://nodejs.org/" },
                ],
                [
                    {
                        label: "HTML/CSS/JS",
                        url: "https://developer.mozilla.org/docs/Web",
                    },
                    {
                        label: "SQL",
                        url: "https://en.wikipedia.org/wiki/SQL",
                    },
                    {
                        label: "MongoDB",
                        url: "https://www.mongodb.com/",
                    },
                ],
            ],
        },
        {
            title: "General Tech",
            lines: [
                [{ label: "Fedora Linux", url: "https://fedoraproject.org/" }],
                [
                    {
                        label: "MCP",
                        url: "https://modelcontextprotocol.io/",
                    },
                    { label: "A2A", url: "https://a2a-protocol.org/" },
                    { label: "OpenRouter", url: "https://openrouter.ai/" },
                ],
                [
                    {
                        label: "Docker",
                        url: "https://www.docker.com/",
                    },
                    {
                        label: "(Dev Containers)",
                        url: "https://containers.dev/",
                        sep: "",
                    },
                    { label: "Caddy", url: "https://caddyserver.com/" },
                ],
                [
                    { label: "Matrix", url: "https://matrix.org/" },
                    {
                        label: "(Tuwunel)",
                        url: "https://github.com/matrix-construct/tuwunel",
                        sep: "",
                    },
                ],
                [
                    { label: "Git", url: "https://git-scm.com/" },
                    {
                        label: "GitHub Actions",
                        url: "https://github.com/features/actions",
                    },
                ],
            ],
        },
    ];

    // Demo story events; the timeline renders them most recent first.
    const storyEvents = [
        {
            date: "November 2026",
            title: "This website goes live",
            text: "Moved my personal site over to my homeserver, with a fresh redesign that looks way better.",
        },
        {
            date: "May 2025",
            title: "1st place at FLL Open Africa Championship",
            text: "Traveled all the way to South Africa with my robotics team and ended up winning 1st place overall!",
            link: roboticsUrl,
        },
        {
            date: "August 2024",
            title: "Started the IMS program",
            text: "Started IMS and immediately dove into my biggest project so far: SmartPainter.",
        },
        {
            date: "July 2024",
            title: "My first internship",
            text: "Landed an internship at VGT in Aarau, which turned into my full-time IMS apprenticeship.",
        },
        {
            date: "March 2024",
            title: "First GitHub repo",
            text: "After tinkering with little games in WebTigerJython, I finally pushed my first real project to GitHub.",
        },
        {
            date: "Summer 2023",
            title: "Joined the robotics team 'mindfactory'",
            text: "After 5 years in the cantonal robotics course, I joined our competitive FIRST LEGO League team.",
            link: roboticsUrl,
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

    <Grid gap="0 2.25rem">
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
                        color={event.link ? storyRed : storyGreen}
                        hoverColor={event.link ? "#e8857f" : ""}
                        link={event.link}
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

        <PaperNote color="#e8da89" pin={MainPin}>
            <h2>My projects:</h2>
            <p style="font-size: 20px;">
                Take a look at my projects on my GitHub account or the dedicated
                page here:
                <br />
            </p>

            <a class="projects-link" href="https://example.com">
                <PaperNote
                    color="#ded9d9"
                    hoverColor="#cfe4ff"
                    pin={LinkPin}
                    maxOffset={0}
                    ><h3 style="color:#0000af">My projects</h3></PaperNote
                >
            </a>
        </PaperNote>

        <!-- GitHub logo → your GitHub profile. (The raw <img> with a
             relative src 404s in Vite — assets must be imported.) -->
        <!-- GitHub sticker + the note it pins: ONE grid item so they
             overlap as a unit — the note slides slightly under the
             sticker, so the LinkPin on the note's top edge reads as
             pinning both the sticker and the note. -->
        <div class="github-tile">
            <a
                class="github-link"
                href="https://github.com/keinstein0"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Link to my GitHub account"
            >
                <img src={github} alt="Link to my GitHub account" />
            </a>

            <a class="projects-link" href="https://github.com/keinstein0">
                <PaperNote
                    color="#ded9d9"
                    hoverColor="#cfe4ff"
                    pin={LinkPin}
                    maxOffset={0}
                    ><h3 style="color:#0000af">My github</h3></PaperNote
                >
            </a>
        </div>

        <div class="painter-image-note">
            <PhotoNote
                src={modernpainterdemo}
                alt="a gif of smartpainter"
                pin={MainPin}
            >
                <h2>That's SmartPainter</h2>
                <p style="font-size: 10px;">
                    in fact I was lying: its modern painter, the evolution of
                    SPainter
                </p>
            </PhotoNote>
        </div>

        <div class="my-technologies-note">
            <PaperNote color="#e8da89" pin={MainPin} width="65%">
                <h2>My technologies:</h2>
            </PaperNote>
        </div>

        {#each techCategories as category}
            <div class="tech-note">
                <PaperNote color="#e8da89" pin={MainPin} variant="lined">
                    <h3>{category.title}</h3>
                    <ul class="tech-list">
                        {#each category.lines as line}
                            <li>
                                {#each line as link, i}
                                    {#if i > 0}
                                        <span class="tech-sep"
                                            >&nbsp;{link.sep ?? "·"}&nbsp;</span
                                        >
                                    {/if}
                                    <a
                                        class="tech-link"
                                        href={link.url}
                                        target="_blank"
                                        rel="noreferrer">{link.label}</a
                                    >
                                {/each}
                            </li>
                        {/each}
                    </ul>
                </PaperNote>
            </div>
        {/each}

        <div class="git-activity-counter-container">
            <GitActivityCounter
                username="keinstein0"
                label="GIT ACTIVITY"
                showDeckHue={false}
            />
        </div>
    </Grid>

    <PaperNote color="#e8da89" pin={MainPin} variant="lined">
        <h2>Contact me:</h2>
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
</main>

<style>
    @font-face {
        font-family: "handwritten";
        src: url("./../assets/dreaming-outloud-pro-regular.otf")
            format("opentype");
    }

    :global(html) {
        /* Overscrolling past the page edges exposes the root background —
           match the body's cardboard base color so there's no white flash. */
        background-color: #2b221a;
        /* Nothing above the page worth scrolling to — disable the
           rubber-band bounce entirely (mobile + trackpad overscroll). */
        overscroll-behavior: none;
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

    .git-activity-counter-container {
        justify-self: center;
        width: 100%;
        max-width: 720px;
    }

    /* Only span two columns once the grid actually has two columns
       (2 × 280px min column + 2.25rem gap). */
    @media (min-width: 650px) {
        :global(.nixie-age-counter-container),
        .git-activity-counter-container {
            grid-column: span 2;
        }
    }

    /* Row gap is 0 on the grid (see the Grid gap prop), so vertical
       spacing between grid items comes from their own bottom margins —
       identical visuals, but implicit rows stay free for the story
       stack's long span. The stack itself is excluded: it spans many
       rows and must not contribute spacing inside them. */
    :global(.grid-container > *:not(.story-stack)) {
        margin-bottom: 2.5rem;
    }

    .painter-image-note {
        grid-column: span 2;
        margin-left: 25%;
        margin-right: 25%;
    }

    .my-technologies-note {
        grid-column: span 2;
        /* PaperNote's .note-wrapper is inline-block, so centering the
           wrapper horizontally is just text alignment on the container. */
        text-align: center;
    }

    .tech-note h3 {
        margin: 0 0 0.35rem;
        padding-bottom: 0.15rem;
        font-size: 1.1rem;
        letter-spacing: 0.04em;
        border-bottom: 1.5px dashed rgba(26, 26, 26, 0.35);
    }

    .tech-list {
        list-style: none;
        margin: 0;
        padding: 0;
        font-size: 1.25rem;
        line-height: 1.35;
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }

    .tech-list li {
        margin: 0;
    }

    /* Technology links read like normal handwriting until hovered, then
       they turn the same link-blue used on "My projects" / "My github". */
    .tech-link {
        color: inherit;
        text-decoration: none;
        transition: color 0.15s ease;
    }

    .tech-link:hover,
    .tech-link:focus-visible {
        color: #0000af;
        text-decoration: underline;
    }

    .tech-sep {
        white-space: nowrap;
    }

    /* The clickable inner "My projects" note: neutral link styling — the
       hover affordance comes from PaperNote's hoverColor tint. */
    .projects-link {
        display: block;
        text-decoration: none;
        color: inherit;
        cursor: pointer;
    }

    /* GitHub logo tile: centered in its grid cell, sized like a small
       board sticker, with a subtle lift on hover to match the notes. */
    .github-link {
        justify-self: center;
    }

    .github-link img {
        display: block;
        width: 210px;
        height: auto;
        transform: rotate(15deg);
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.25));
        transition:
            transform 0.28s cubic-bezier(0.175, 0.885, 0.32, 1.275),
            filter 0.28s ease;
    }

    .github-link:hover img {
        transform: rotate(10deg) scale(1.04);
        filter: drop-shadow(0 4px 7px rgba(0, 0, 0, 0.3));
    }

    /* GitHub sticker + pinned note: one flex column. The sticker sits on
       a higher z-plane than the note's paper, so the note slides under
       it while the note's pin (z-index 25) stays above — one pin, two
       layers. The negative margin is how much the note tucks under. */
    .github-tile {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-self: center;
        width: min(280px, 100%);
    }

    .github-tile .github-link {
        position: relative;
        z-index: 2;
    }

    .github-tile :global(.note-wrapper) {
        width: 100%;
        margin-top: -34px;
    }

    /* Unified hover: whichever of the two you hover, the tile lifts as a
       unit. The sticker rises just above the note's hovered paper layer
       (z-index 20) while staying below the note's pin (z-index 25), so
       the "one pin pins both" illusion never breaks. Hovering the sticker
       also tints the note — same as hovering the note itself. */
    .github-tile:hover .github-link {
        z-index: 22;
    }

    .github-tile:hover :global(.note-wrapper .paper) {
        background-color: #cfe4ff;
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
            /* Span "everything below" so future side components can flow
               down columns 1–2 beside it. Empty implicit rows cost nothing
               because the row gap is 0 — spacing comes from item margins.
               The span only needs to be big, not exact. */
            grid-row: 2 / span 50;
            align-self: start;
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
