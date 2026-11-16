import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import Page from '../routes/+page.svelte';

describe('+page.svelte', () => {
    it('renders without throwing', () => {
        const { container } = render(Page);
        expect(container).toBeTruthy();
    });

    it('renders the page skeleton', () => {
        const { container } = render(Page);
        expect(container.querySelector('h1')).toBeTruthy();
        expect(container.querySelector('main')).toBeTruthy();
    });
});
