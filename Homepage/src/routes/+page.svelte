<script lang="ts">
    import PaperNote from "../components/PaperNote.svelte";
    import PhotoNote from "../components/PhotoNote.svelte";
    import Grid from "../components/Grid.svelte";

    import me from "../assets/images/me.jpg";
    import { Pin } from "../components/pin/pin";
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
                style="text-align: center; margin-top: 0.2rem; font-weight: bold;"
            >
                I hope you enjoy it
            </p>
        </PaperNote>
    </header>

    <Grid>
        <PhotoNote src={me} alt="a picture of me" pin={MainPin}>
            <h2>that's me :D</h2>
        </PhotoNote>

        <PaperNote color="#e8da89" pin={MainPin}>
            <h2>About me:</h2>
            <p>I like cheese</p>
        </PaperNote>
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
        margin-bottom: 2rem;
    }

    .main-title {
        font-size: 3rem;
        letter-spacing: 1px;
        margin: 0;
    }

    .notes-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(290px, 100%), 1fr));
        gap: 2.5rem 2rem;
        align-items: start;
        justify-items: center;
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
