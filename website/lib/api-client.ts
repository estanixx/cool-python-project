const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "/api/proxy";

/**
 * Centralized API client for API Gateway v2 Lambda proxy integrations.
 *
 * API Gateway v2 wraps Lambda responses in an envelope:
 *   { statusCode: number, body: string }
 * where `body` is a JSON-encoded string requiring a second parse.
 *
 * @template T Expected response type (after unwrapping the envelope)
 * @param path API path (e.g. "/dictionary", "/product")
 * @param options Optional fetch options (method, body, headers)
 * @returns Parsed response body as type T
 * @throws Error on non-2xx status or malformed body
 */
export async function api<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  const rawText = await res.text();
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawText);
  } catch {
    throw new Error(
      `Invalid JSON from API (status ${res.status}): ${rawText.slice(0, 500)}`,
    );
  }

  const isEnvelope =
    typeof parsed === "object" &&
    parsed !== null &&
    "statusCode" in parsed &&
    "body" in parsed;

  if (isEnvelope) {
    const envelope = parsed as { statusCode: number; body: unknown };
    // API Gateway v2: body is a JSON string that needs a second parse
    let body: unknown;
    if (typeof envelope.body === "string") {
      try {
        body = JSON.parse(envelope.body);
      } catch (parseError) {
        throw new Error(
          `Failed to parse API response body: ${envelope.body}`,
        );
      }
    } else {
      body = envelope.body;
    }

    if (!res.ok || envelope.statusCode >= 400) {
      const errorBody = body as { error?: string };
      throw new Error(
        errorBody?.error || `API error: ${envelope.statusCode}`,
      );
    }

    return body as T;
  }

  if (!res.ok) {
    const errorBody = parsed as { error?: string };
    throw new Error(errorBody?.error || `API error: ${res.status}`);
  }

  return parsed as T;
}
