import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import Page from '../routes/+page.svelte';

describe('+page.svelte', () => {
    it('renders the welcome heading', () => {
        const { getByText } = render(Page);
        expect(getByText('Welcome to Homepage')).toBeInTheDocument();
    });

    it('renders the page without throwing', () => {
        const { container } = render(Page);
        expect(container).toBeTruthy();
        expect(container.innerHTML).toContain('Welcome to Homepage');
    });
});
