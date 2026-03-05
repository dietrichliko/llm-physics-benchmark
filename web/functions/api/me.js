/**
 * GET /api/me
 * Returns the authenticated user's identity extracted from the
 * Cloudflare Access JWT.  Falls back to a dev user when running locally
 * without Access (wrangler pages dev).
 */
export async function onRequestGet({ request }) {
  const email = request.headers.get("Cf-Access-Authenticated-User-Email");
  const jwt   = request.headers.get("Cf-Access-Jwt-Assertion");

  // Local development: no CF Access headers present
  if (!email && !jwt) {
    return Response.json({ email: "dev@localhost", sub: "dev", is_dev: true });
  }

  let sub = email ?? "unknown";
  if (jwt) {
    try {
      // The JWT is already verified by CF Access at the edge; we only decode
      // the payload here to extract the stable subject identifier.
      const payload = JSON.parse(
        atob(jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
      );
      sub = payload.sub ?? payload.email ?? sub;
    } catch {
      // Malformed JWT — keep sub = email
    }
  }

  return Response.json({ email: email ?? "unknown", sub });
}
