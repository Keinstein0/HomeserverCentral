import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vitest/config';

export default defineConfig({
    plugins: [svelte()],
    test: {
        // happy-dom is lighter and faster than jsdom for component tests.
        environment: 'happy-dom',
        include: ['src/**/*.{test,spec}.{js,ts}'],
        globals: false,
        setupFiles: ['./vitest.setup.js'],
    },
});
