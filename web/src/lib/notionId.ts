export function normalizeNotionIdFromString(input: string): string | null {
  if (!input) return null;
  const s = String(input);
  const m = s.match(/[0-9a-fA-F-]{32,}/);
  if (!m) return null;
  const hex = m[0].replace(/[^0-9a-fA-F]/g, "");
  if (hex.length !== 32) return null;
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`.toLowerCase();
}
