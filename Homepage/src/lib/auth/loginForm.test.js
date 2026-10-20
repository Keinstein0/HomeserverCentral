import { describe, it, expect } from 'vitest';
import { ERROR_MESSAGES, getLoginError, parseLoginQuery } from '../../../static/lib/loginForm.js';

describe('getLoginError', () => {
    it('returns the mapped message for a known error code', () => {
        expect(getLoginError('missing_fields')).toBe(ERROR_MESSAGES.missing_fields);
        expect(getLoginError('invalid_credentials')).toBe(ERROR_MESSAGES.invalid_credentials);
    });

    it('returns a generic fallback for an unknown error code', () => {
        expect(getLoginError('totally_unknown')).toBe('Something went wrong. Please try again.');
    });

    it('returns a generic fallback for null', () => {
        expect(getLoginError(null)).toBe('Something went wrong. Please try again.');
    });

    it('returns a generic fallback for empty string', () => {
        expect(getLoginError('')).toBe('Something went wrong. Please try again.');
    });
});

describe('parseLoginQuery', () => {
    it('decodes all three params from a full query string', () => {
        const result = parseLoginQuery('?error=invalid_credentials&redirect=%2Fdashboard&room=status-viewers');
        expect(result).toEqual({
            error: 'invalid_credentials',
            redirect: '/dashboard',
            room: 'status-viewers',
        });
    });

    it('defaults redirect to "/" when not present', () => {
        const result = parseLoginQuery('?error=missing_fields');
        expect(result.redirect).toBe('/');
    });

    it('defaults room to empty string when not present', () => {
        const result = parseLoginQuery('?error=missing_fields&redirect=%2F');
        expect(result.room).toBe('');
    });

    it('returns null error when no error param is present', () => {
        const result = parseLoginQuery('?redirect=%2F&room=test-room');
        expect(result.error).toBeNull();
    });

    it('handles an empty query string with all defaults', () => {
        const result = parseLoginQuery('');
        expect(result).toEqual({ error: null, redirect: '/', room: '' });
    });

    it('preserves special characters through URL encoding round-trip', () => {
        // Room alias with # and : — encoded as %23 and %3A
        const encoded = '?room=%23status-viewers%3Akeinstein0.ch';
        const result = parseLoginQuery(encoded);
        expect(result.room).toBe('#status-viewers:keinstein0.ch');
    });

    it('handles a raw room ID starting with !', () => {
        const result = parseLoginQuery('?room=%21statusroom%3Akeinstein0.ch');
        expect(result.room).toBe('!statusroom:keinstein0.ch');
    });
});
