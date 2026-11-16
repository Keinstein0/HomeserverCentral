<script lang="ts">
    import PaperNote from "../components/PaperNote.svelte";
    import PhotoNote from "../components/PhotoNote.svelte";
    import Grid from "../components/Grid.svelte";

    import me from "../assets/images/me.jpg";
    import { Pin } from "../components/pin/pin";
    import NixieAgeCounter from "../components/nixie/NixieAgeCounter.svelte";
    const MainPin = new Pin("#ff0000");
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

    <Grid>
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

        <div style="background-color: red; margin-left margin-right: 60px">
            <PaperNote color="#e8da89" pin={MainPin}>
                <h2>My story</h2>
            </PaperNote>
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
    .notes-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(290px, 100%), 1fr));
        gap: 2.5rem 2rem;
        align-items: start;
        justify-items: center;
    }

    /* .about-me targets the .note-wrapper inside PaperNote, which is the
       grid item — so it must be :global from this scoped stylesheet. */
    :global(.about-me) {
        justify-self: center;
    }

    /* Only span two columns once the grid actually has two columns
       (2 × 280px min column + 2rem gap). */
    @media (min-width: 620px) {
        :global(.about-me) {
            grid-column: span 2;
        }
    }

    :global(.nixie-age-counter-container) {
        justify-self: center;
    }

    /* Only span two columns once the grid actually has two columns
       (2 × 280px min column + 2rem gap). */
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

    .note-textarea {
        width: 100%;
        margin-top: 0.6rem;
        padding: 0.4rem;
        box-sizing: border-box;
        border: 1px dashed rgba(0, 0, 0, 0.35);
        background: rgba(255, 255, 255, 0.4);
        border-radius: 4px;
        font-family: inherit;
        font-size: 1rem;
        resize: vertical;
    }

    .note-textarea:focus {
        outline: none;
        background: rgba(255, 255, 255, 0.7);
    }
</style>
