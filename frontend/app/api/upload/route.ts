export const runtime = "nodejs";

export async function POST(req: Request) {
  const res = await fetch("http://localhost:8000/ingest", {
    method: "POST",
    body: req.body,
    headers: { "content-type": req.headers.get("content-type") || "" },
  });
  return new Response(res.body, {
    headers: { "Content-Type": "application/json" },
    status: res.status,
  });
}
