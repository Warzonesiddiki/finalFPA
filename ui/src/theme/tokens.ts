/**
 * Centralized theme tokens and Conditional Formatting (CF) rules per 08_UI_UX_SPEC.md §14.
 * Rule: Non-colour signals (symbols/text) are mandatory for black-and-white print tests.
 */

export const tokens = {
  severity: {
    high: {
      bg: '#fee2e2',
      text: '#991b1b',
      border: '#f87171',
      symbol: '[HIGH ⚠]',
      icon: '⚠',
      label: 'High',
    },
    medium: {
      bg: '#fef3c7',
      text: '#92400e',
      border: '#fcd34d',
      symbol: '[MED ⚑]',
      icon: '⚑',
      label: 'Med',
    },
    low: {
      bg: '#e0f2fe',
      text: '#075985',
      border: '#7dd3fc',
      symbol: '[LOW ⓘ]',
      icon: 'ⓘ',
      label: 'Low',
    },
  },
  status: {
    open: {
      bg: '#fee2e2',
      text: '#b91c1c',
      label: 'Open',
    },
    in_review: {
      bg: '#fef3c7',
      text: '#b45309',
      label: 'In Review',
    },
    explained: {
      bg: '#e0e7ff',
      text: '#4338ca',
      label: 'Explained',
    },
    corrected: {
      bg: '#dcfce7',
      text: '#15803d',
      label: 'Corrected',
    },
    closed: {
      bg: '#f1f5f9',
      text: '#475569',
      label: 'Closed',
    },
    reopened: {
      bg: '#ffedd5',
      text: '#c2410c',
      label: 'Reopened',
    },
    not_applicable: {
      bg: '#f3e8ff',
      text: '#7e22ce',
      label: 'Not Applicable',
    },
  },
  aging: {
    bucket0_7: {
      bg: '#f0fdf4',
      text: '#166534',
      border: '#bbf7d0',
      label: '0–7d',
    },
    bucket8_30: {
      bg: '#fffbeb',
      text: '#b45309',
      border: '#fde68a',
      label: '8–30d',
    },
    bucket31_plus: {
      bg: '#fef2f2',
      text: '#b91c1c',
      border: '#fecaca',
      label: '31+d',
    },
    overdue: {
      bg: '#fee2e2',
      text: '#991b1b',
      border: '#ef4444',
      symbol: '⚠ Overdue',
    },
  },
  semantic: {
    disclaimer: {
      bannerBg: '#f8fafc',
      bannerBorder: '#cbd5e1',
      text: '#334155',
      canonicalPhrase: 'Potential exception — requires accounting review.',
    },
    flaggedAgain: {
      bg: '#fdf2f8',
      text: '#9d174d',
      border: '#f472b6',
      label: 'Flagged again',
    },
  },
} as const;
