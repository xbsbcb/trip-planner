const BASE = "http://localhost:8000"

export async function createPlan(request) {
  const res = await fetch(`${BASE}/api/trip/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}

export async function* streamPlan(request) {
  const res = await fetch(`${BASE}/api/trip/plan/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        yield JSON.parse(line.slice(6))
      }
    }
  }
}
