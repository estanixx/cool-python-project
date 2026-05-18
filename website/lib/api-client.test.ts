import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Import after mocking so the module picks up the mocked fetch
import { api } from "./api-client";

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
});
