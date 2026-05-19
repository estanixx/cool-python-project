/**
 * API proxy route — invokes Lambdas directly via Floci's Lambda API.
 *
 * Floci v1.5.16 (LocalStack) does NOT support API Gateway v2 HTTP invocation
 * (returns 404 for ALL routes). As a workaround we bypass API Gateway entirely
 * and invoke the correct Lambda function directly.
 *
 * Environment variables are sourced from /shared/.env by docker-entrypoint.sh.
 */
import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://floci:4566";
const API_ID = process.env.API_ID || "";
const STAGE = process.env.STAGE || "local";

const LAMBDA_INVOKE_URL = `${API_BASE_URL}/2015-03-31/functions`;

/** Map the first URL path segment to the corresponding Lambda function name. */
const PATH_TO_FUNCTION: Record<string, string> = {
  dictionary: `dictionary-${STAGE}`,
  product: `product-${STAGE}`,
  "shopping-cart": `shopping-cart-${STAGE}`,
  "word-trick": `word-trick-${STAGE}`,
};

export async function GET(request: NextRequest) {
  return proxyRequest("GET", request);
}

export async function POST(request: NextRequest) {
  return proxyRequest("POST", request);
}

export async function PUT(request: NextRequest) {
  return proxyRequest("PUT", request);
}

export async function DELETE(request: NextRequest) {
  return proxyRequest("DELETE", request);
}

async function proxyRequest(method: string, request: NextRequest) {
  try {
    // Extract path from /api/proxy/[...path]
    const { pathname, searchParams } = new URL(request.url);
    const segments = pathname.replace("/api/proxy/", "").split("/");
    const functionKey = segments[0];
    const functionName = PATH_TO_FUNCTION[functionKey];

    if (!functionName) {
      return NextResponse.json(
        { error: `Unknown API path: ${functionKey}` },
        { status: 404 },
      );
    }

    // Build the raw path (same path the Lambda handler expects)
    const rawPath = "/" + segments.join("/");

    // Build query string
    const rawQueryString = searchParams.toString();

    // Parse path parameters (second segment onwards)
    const pathParams: Record<string, string> = {};
    if (segments.length > 1) {
      const paramName =
        {
          dictionary: "word",
          product: "product_id",
          "shopping-cart": "cart_id",
        }[functionKey] ?? null;
      if (paramName) {
        pathParams[paramName] = decodeURIComponent(segments[1]);
      }
    }

    // Parse query parameters
    const queryStringParams: Record<string, string> = {};
    searchParams.forEach((value, key) => {
      queryStringParams[key] = value;
    });

    // Read body for POST/PUT
    let body: unknown = null;
    if (method === "POST" || method === "PUT") {
      try {
        body = await request.json();
      } catch {
        body = null;
      }
    }

    // Build API Gateway v2 event envelope
    const event = {
      version: "2.0",
      routeKey: `${method} ${rawPath}`,
      rawPath,
      rawQueryString,
      headers: Object.fromEntries(request.headers),
      requestContext: {
        accountId: "000000000000",
        apiId: API_ID,
        stage: "$default",
        domainName: `${API_ID}.execute-api.us-east-1.amazonaws.com`,
        domainPrefix: API_ID,
        requestId: crypto.randomUUID(),
        http: {
          method,
          path: rawPath,
          protocol: "HTTP/1.1",
          sourceIp: request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "127.0.0.1",
          userAgent: request.headers.get("user-agent") || "",
        },
      },
      pathParameters: Object.keys(pathParams).length > 0 ? pathParams : null,
      queryStringParameters: Object.keys(queryStringParams).length > 0 ? queryStringParams : null,
      body: body !== null ? JSON.stringify(body) : null,
      isBase64Encoded: false,
    };

    // Invoke Lambda
    const invokeUrl = `${LAMBDA_INVOKE_URL}/${functionName}/invocations`;
    const response = await fetch(invokeUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(event),
    });

    const payload = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: payload.error || "Lambda invocation failed" },
        { status: response.status },
      );
    }

    // Lambda returns API Gateway envelope: { statusCode, body, headers }
    const lambdaStatus = payload.statusCode ?? 200;
    const lambdaBody = payload.body;
    const lambdaHeaders = payload.headers || {};

    // Return the Lambda's envelope so api-client.ts can unwrap it as before
    return NextResponse.json(
      { statusCode: lambdaStatus, body: lambdaBody },
      {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          ...lambdaHeaders,
        },
      },
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Proxy error: ${message}` },
      { status: 502 },
    );
  }
}
