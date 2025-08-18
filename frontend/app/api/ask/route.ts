export const runtime = "nodejs";

export async function POST(req: Request) {
  const body = await req.json();
  const res = await fetch("http://localhost:8000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  // Stream back as-is
  return new Response(res.body, {
    headers: { "Content-Type": "application/json" },
    status: res.status,
  });
}
