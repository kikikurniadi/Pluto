const DEFAULT_ORCHESTRATOR = import.meta.env.VITE_ORCHESTRATOR_URL ?? 'http://localhost:8001'

export type QueryResponse = {
  success: boolean
  reply?: string
  error?: string
}

function randomPrice(base = 10000) {
  // generate a mock price roughly around base
  const delta = Math.round((Math.random() - 0.5) * base * 0.2)
  return base + delta
}

function delay(ms: number) {
  return new Promise((res) => setTimeout(res, ms))
}

async function mockResponse(text: string): Promise<QueryResponse> {
  await delay(400 + Math.random() * 600)
  const q = text.toLowerCase()
  if (q.includes('price') || q.includes('harga') || q.includes('berapa')) {
    const coin = q.includes('ethereum') ? 'Ethereum' : q.includes('solana') ? 'Solana' : 'Bitcoin'
    const base = coin === 'Ethereum' ? 1800 : coin === 'Solana' ? 20 : 65000
    const price = randomPrice(base)
    return { success: true, reply: `Harga ${coin} saat ini adalah $${price} USD.` }
  }
  if (q.includes('news') || q.includes('berita') || q.includes('update')) {
    return {
      success: true,
      reply:
        'Berita terkini: 1) Exchange X mengumumkan listing baru. 2) Token Y mengalami lonjakan harga 12%. (mocked)'
    }
  }

  // fallback echo
  return { success: true, reply: `Mock reply: saya mengerti — "${text}"` }
}

export async function sendQuery(text: string): Promise<QueryResponse> {
  // Priority: runtime localStorage toggle (useMockServer), then VITE_USE_MOCK env var
  try {
    const runtimeFlag = typeof window !== 'undefined' && window.localStorage?.getItem('useMockServer')
    const useMockRuntime = runtimeFlag === 'true'
    const useMockEnv = (import.meta.env.VITE_USE_MOCK ?? 'false') === 'true'

    if (useMockRuntime || useMockEnv) return mockResponse(text)

    const url = `${DEFAULT_ORCHESTRATOR}/query`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })

    if (!res.ok) {
      // fallback to mock on HTTP errors
      return mockResponse(text)
    }

    const data = await res.json()
    // Expecting { reply: string } or similar shape from orchestrator
    if (data && (data.reply || data.result || data.message)) {
      return { success: true, reply: data.reply ?? data.result ?? data.message }
    }

    return { success: true, reply: JSON.stringify(data) }
  } catch (err: any) {
    // On network errors, return a mock response so UI remains functional
    return mockResponse(text)
  }
}
