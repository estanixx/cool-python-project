import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Import after mocking so the module picks up the mocked fetch
import { api, createCart, getCartTotal, getCart } from "./api-client";
import type { Cart, CartProduct, CartTotal } from "@/types/api";

/** Helper to build a mock fetch response with text() support. */
function mockResponse(envelope: object, ok = true) {
  const bodyStr = JSON.stringify(envelope);
  return {
    ok,
    text: () => Promise.resolve(bodyStr),
    json: () => Promise.resolve(envelope),
  };
}

describe("api-client", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    // Reset env var before each test
    delete (globalThis as any).__NEXT_RUNTIME;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.stubGlobal("fetch", mockFetch);
  });

  describe("double-parse success", () => {
    it("parses a successful double-JSON-encoded response", async () => {
      const envelope = {
        statusCode: 200,
        body: JSON.stringify({ entries: [{ Word: "hello", definition: "greeting" }] }),
      };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(envelope),
      });

      const result = await api<{ entries: Array<{ Word: string; definition: string }> }>("/dictionary");

      expect(result).toEqual({
        entries: [{ Word: "hello", definition: "greeting" }],
      });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/dictionary"),
        expect.objectContaining({
          headers: { "Content-Type": "application/json" },
        }),
      );
    });

    it("passes through response body when already an object (non-string)", async () => {
      const envelope = {
        statusCode: 200,
        body: { products: [] },
      };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(envelope),
      });

      const result = await api<{ products: unknown[] }>("/product");

      expect(result).toEqual({ products: [] });
    });
  });

  describe("error response handling", () => {
    it("throws error with message from body on 404", async () => {
      const envelope = {
        statusCode: 404,
        body: JSON.stringify({ error: "not found" }),
      };
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve(envelope),
      });

      await expect(api("/dictionary/missing")).rejects.toThrow("not found");
    });

    it("throws generic error when body has no error field", async () => {
      const envelope = {
        statusCode: 500,
        body: JSON.stringify({ message: "internal error" }),
      };
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve(envelope),
      });

      await expect(api("/product")).rejects.toThrow("API error: 500");
    });
  });

  describe("malformed body handling", () => {
    it("throws parse error when body is not valid JSON", async () => {
      const envelope = {
        statusCode: 200,
        body: "not-json",
      };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(envelope),
      });

      await expect(api("/dictionary")).rejects.toThrow(
        "Failed to parse API response body: not-json",
      );
    });

    it("throws parse error when body is malformed JSON string", async () => {
      const envelope = {
        statusCode: 200,
        body: "{broken json",
      };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(envelope),
      });

      await expect(api("/word-trick")).rejects.toThrow(
        "Failed to parse API response body",
      );
    });
  });

  describe("createCart", () => {
    it("sends POST with create operation and returns cart", async () => {
      const cartId = "550e8400-e29b-41d4-a716-446655440000";
      const products: CartProduct[] = [
        { uuid: "p1", name: "Mouse", price: 29.99 },
      ];
      const expected: Cart = { UUID: cartId.toUpperCase(), products };

      mockFetch.mockResolvedValue(
        mockResponse({ statusCode: 200, body: JSON.stringify(expected) }),
      );

      const result = await createCart(cartId, products);

      expect(result).toEqual(expected);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/shopping-cart"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            operation: "create",
            cart_id: cartId,
            products,
          }),
        }),
      );
    });

    it("throws on API error", async () => {
      mockFetch.mockResolvedValue(
        mockResponse(
          { statusCode: 400, body: JSON.stringify({ error: "bad request" }) },
          false,
        ),
      );

      await expect(createCart("bad-id", [])).rejects.toThrow("bad request");
    });
  });

  describe("getCartTotal", () => {
    it("sends POST with get_total operation and returns totals", async () => {
      const cartId = "CART-1";
      const expected: CartTotal = { subtotal: 100, tax: 7, total: 107 };

      mockFetch.mockResolvedValue(
        mockResponse({ statusCode: 200, body: JSON.stringify(expected) }),
      );

      const result = await getCartTotal(cartId);

      expect(result).toEqual(expected);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/shopping-cart"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            operation: "get_total",
            cart_id: cartId,
            tax_rate: 0.07,
          }),
        }),
      );
    });

    it("accepts custom tax rate", async () => {
      mockFetch.mockResolvedValue(
        mockResponse({
          statusCode: 200,
          body: JSON.stringify({ subtotal: 100, tax: 10, total: 110 }),
        }),
      );

      const result = await getCartTotal("CART-1", 0.1);

      expect(result.subtotal).toBe(100);
      expect(result.tax).toBe(10);
      expect(result.total).toBe(110);
    });

    it("throws on API error", async () => {
      mockFetch.mockResolvedValue(
        mockResponse(
          {
            statusCode: 404,
            body: JSON.stringify({ error: "shopping cart not found" }),
          },
          false,
        ),
      );

      await expect(getCartTotal("missing")).rejects.toThrow(
        "shopping cart not found",
      );
    });
  });

  describe("getCart", () => {
    it("sends POST with read operation and returns cart", async () => {
      const cartId = "CART-1";
      const products: CartProduct[] = [
        { uuid: "p1", name: "Mouse", price: 29.99 },
      ];
      const expected: Cart = { UUID: cartId, products };

      mockFetch.mockResolvedValue(
        mockResponse({ statusCode: 200, body: JSON.stringify(expected) }),
      );

      const result = await getCart(cartId);

      expect(result).toEqual(expected);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/shopping-cart"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            operation: "read",
            cart_id: cartId,
          }),
        }),
      );
    });

    it("throws 404 when cart not found", async () => {
      mockFetch.mockResolvedValue(
        mockResponse(
          {
            statusCode: 404,
            body: JSON.stringify({ error: "shopping cart not found" }),
          },
          false,
        ),
      );

      await expect(getCart("missing")).rejects.toThrow(
        "shopping cart not found",
      );
    });
  });
});
