<script lang="ts">
    import PaperNote from "../components/PaperNote.svelte";
    import PhotoNote from "../components/PhotoNote.svelte";
    import Grid from "../components/Grid.svelte";

    import me from "../assets/images/me.jpg";
    import { Pin } from "../components/pin/pin";
    import NixieAgeCounter from "../components/nixie/NixieAgeCounter.svelte";
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

        <div class="story-stack">
            <PaperNote color={storyGreen} pin={MainPin} width="min(480px, 94%)">
                <h2>My story</h2>
            </PaperNote>

            <div class="story-timeline">
                <div class="timeline-string" aria-hidden="true"></div>
                {#each storyEvents as event}
                    <PaperNote
                        color={storyGreen}
                        pin={MainPin}
                        width="min(480px, 100%)"
                    >
                        <p class="event-date">{event.date}</p>
                        <h3>{event.title}</h3>
                        <p>{event.text}</p>
                    </PaperNote>
                {/each}
            </div>
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
        background-size: cover;
        background-position: center;
        background-repeat: repeat-y;
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

    /* Story stack: header note + twine timeline. Spans the full row by
       default; parked in the third column once the grid has three. */
    .story-stack {
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

    .timeline-string {
        position: absolute;
        left: 50%;
        top: -2.25rem;
        bottom: -1.25rem;
        width: 3px;
        border-radius: 2px;
        transform: translateX(-50%) rotate(0.4deg);
        background: linear-gradient(
            to bottom,
            rgba(242, 226, 189, 0),
            rgba(242, 226, 189, 0.65) 3%,
            rgba(242, 226, 189, 0.65) 97%,
            rgba(242, 226, 189, 0)
        );
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
</style>
