/** AU test data library (verbatim from the master prompt). Typed values only: none of these are submitted. */
export const AU = {
  mobile: {
    tooShort: '0412 34',
    us: '14123456789',
    lettersMixed: '0412ABC678',
    whitespace: '   ',
    emoji: '\u{1F642}',
    elevenDigits: '04123456789',
  },
  email: {
    noAt: 'noah.smithbigpond.net.au',
    missingTld: 'noah.smith@bigpond',
    doubleDot: 'noah..smith@bigpond.net.au',
    whitespace: '   ',
    xss: '"><img src=x onerror=window.__xss=1>',
    sqli: "' OR '1'='1",
  },
  otp: { wrong: '111111', fiveDigits: '48956', letters: 'a' },
  /** Observed UI mask for AU mobiles (2026-09-19): "+61 (04) XXXX XXXX". */
  mask: (national: string): string => `+61 (${national.slice(0, 2)}) ${national.slice(2, 6)} ${national.slice(6)}`,
} as const;
