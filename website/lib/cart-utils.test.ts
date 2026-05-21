import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { generateCartId, calculateLocalTotal } from "./cart-utils";

describe("generateCartId", () => {
  it("returns a valid UUID v4 string", () => {
    const id = generateCartId();
    // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  });

  it("returns unique values on successive calls", () => {
    const ids = new Set(Array.from({ length: 100 }, () => generateCartId()));
    expect(ids.size).toBe(100);
  });
});

describe("calculateLocalTotal", () => {
  it("calculates subtotal, tax, and total from products", () => {
    const products = [
      { uuid: "p1", name: "A", price: 100 },
      { uuid: "p2", name: "B", price: 50 },
    ];
    const result = calculateLocalTotal(products, 0.1);
    expect(result.subtotal).toBe(150);
    expect(result.tax).toBe(15);
    expect(result.total).toBe(165);
  });

  it("handles missing prices as zero", () => {
    const products = [
      { uuid: "p1", name: "A" },
      { uuid: "p2", name: "B", price: 50 },
    ];
    const result = calculateLocalTotal(products, 0.07);
    expect(result.subtotal).toBe(50);
    expect(result.tax).toBeCloseTo(3.5);
    expect(result.total).toBeCloseTo(53.5);
  });

  it("returns zeros for empty products", () => {
    const result = calculateLocalTotal([], 0.1);
    expect(result.subtotal).toBe(0);
    expect(result.tax).toBe(0);
    expect(result.total).toBe(0);
  });

  it("uses default tax rate of 0.07 when not specified", () => {
    const products = [{ uuid: "p1", name: "A", price: 100 }];
    const result = calculateLocalTotal(products);
    expect(result.tax).toBeCloseTo(7);
    expect(result.total).toBeCloseTo(107);
  });
});

describe("copyToClipboard", () => {
  beforeEach(() => {
    vi.stubGlobal("navigator", {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("writes text to clipboard and returns true on success", async () => {
    const { copyToClipboard } = await import("./cart-utils");
    const result = await copyToClipboard("test-id");
    expect(result).toBe(true);
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    expect((globalThis as any).navigator.clipboard.writeText).toHaveBeenCalledWith("test-id");
  });

  it("returns false when clipboard API is unavailable", async () => {
    vi.stubGlobal("navigator", {});
    const { copyToClipboard } = await import("./cart-utils");
    const result = await copyToClipboard("test-id");
    expect(result).toBe(false);
  });

  it("returns false when writeText throws", async () => {
    vi.stubGlobal("navigator", {
      clipboard: {
        writeText: vi.fn().mockRejectedValue(new Error("denied")),
      },
    });
    const { copyToClipboard } = await import("./cart-utils");
    const result = await copyToClipboard("test-id");
    expect(result).toBe(false);
  });
});
