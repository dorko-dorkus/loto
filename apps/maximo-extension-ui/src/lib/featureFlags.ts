const flags = (process.env.NEXT_PUBLIC_FEATURE_FLAGS || '')
  .split(',')
  .map((f) => f.trim())
  .filter(Boolean);

export const FEATURE_FLAGS: Record<string, boolean> = Object.fromEntries(
  flags.map((f) => [f, true])
);

export const isFeatureEnabled = (flag: string): boolean => !!FEATURE_FLAGS[flag];
