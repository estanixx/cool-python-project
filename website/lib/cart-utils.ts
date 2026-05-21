/**
 * Generate a UUID v4 using crypto.randomUUID().
 * Returns lowercase UUID string.
 */
export function generateCartId(): string {
  return crypto.randomUUID();
}

/**
 * Calculate cart totals client-side (subtotal, tax, total).
 * Used as fallback when API call fails.
 */
export function calculateLocalTotal(
  products: Array<{ price?: number }>,
  taxRate: number = 0.07,
): { subtotal: number; tax: number; total: number } {
  const subtotal = products.reduce((sum, p) => sum + (p.price ?? 0), 0);
  const tax = subtotal * taxRate;
  const total = subtotal + tax;
  return { subtotal, tax, total };
}

/**
 * Copy text to clipboard using the Clipboard API.
 * Returns true on success, false on failure.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (!navigator?.clipboard?.writeText) {
    return false;
  }
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
