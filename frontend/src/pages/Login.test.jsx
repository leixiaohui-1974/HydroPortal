import { describe, expect, test } from 'vitest';

import { shouldShowDemoCredentials } from './Login';

describe('shouldShowDemoCredentials', () => {
  test('defaults to visible in dev when env var is unset', () => {
    expect(shouldShowDemoCredentials({ DEV: true })).toBe(true);
  });

  test('defaults to hidden outside dev when env var is unset', () => {
    expect(shouldShowDemoCredentials({ DEV: false })).toBe(false);
  });

  test('empty string does not override dev fallback', () => {
    expect(
      shouldShowDemoCredentials({
        DEV: true,
        VITE_HYDROPORTAL_DEMO_AUTH: '',
      })
    ).toBe(true);
  });

  test('recognizes explicit truthy values', () => {
    for (const value of ['1', 'true', 'yes', 'on', ' TRUE ']) {
      expect(
        shouldShowDemoCredentials({
          DEV: false,
          VITE_HYDROPORTAL_DEMO_AUTH: value,
        })
      ).toBe(true);
    }
  });

  test('recognizes explicit falsey values', () => {
    for (const value of ['0', 'false', 'no', 'off', 'anything-else']) {
      expect(
        shouldShowDemoCredentials({
          DEV: true,
          VITE_HYDROPORTAL_DEMO_AUTH: value,
        })
      ).toBe(false);
    }
  });
});
