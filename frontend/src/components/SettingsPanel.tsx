import { useEffect, useState } from 'react'
import { Select, DialogVariant, Button } from '../ui'

export default function SettingsPanel() {
  const [open, setOpen] = useState(false)
  const [coin, setCoin] = useState('bitcoin')
  const [useMock, setUseMock] = useState(() => {
    try {
      return typeof window !== 'undefined' && window.localStorage?.getItem('useMockServer') === 'true'
    } catch {
      return false
    }
  })
  const [schedStatus, setSchedStatus] = useState<{running?: boolean; next_run_time?: string | null; interval_seconds?: number | null} | null>(null)

  // fetch schedule status from backend
  const fetchStatus = async (token?: string) => {
    try {
      const headers: Record<string,string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch('/schedule/status', { headers })
      if (!res.ok) {
        setSchedStatus(null)
        return
      }
      const j = await res.json()
      if (j && j.ok) {
        setSchedStatus({ running: j.running, next_run_time: j.next_run_time ?? null, interval_seconds: j.interval_seconds ?? null })
      } else {
        setSchedStatus(null)
      }
    } catch (e) {
      setSchedStatus(null)
    }
  }

  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('useMockServer', useMock ? 'true' : 'false')
      }
    } catch {
      // ignore
    }
  }, [useMock])

  // auto-refresh schedule status every 10s
  useEffect(() => {
    // auto-refresh every 10s
    let t: number | undefined
    const doFetch = () => {
      try {
        const el = document.getElementById('sched-token') as HTMLInputElement | null
        const token = el ? el.value : undefined
        fetchStatus(token)
      } catch {
        fetchStatus()
      }
    }
    doFetch()
    t = window.setInterval(doFetch, 10000) as unknown as number
    return () => { if (t !== undefined) clearInterval(t) }
  }, [])

  return (
    <div className="mb-4 flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-300 mr-2">Coin</label>
  <Select value={coin} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCoin(e.target.value)}>
          <option value="bitcoin">Bitcoin</option>
          <option value="ethereum">Ethereum</option>
          <option value="solana">Solana</option>
        </Select>
      </div>

      <div className="border-t pt-4">
        <h4 className="text-sm font-medium mb-2">Scheduler</h4>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-sm">Interval (s)</label>
          <input type="number" defaultValue={60} id="sched-interval" className="w-24 px-2 py-1 border rounded" />
        </div>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-sm">Token (optional)</label>
          <input type="text" id="sched-token" placeholder="secret token" className="px-2 py-1 border rounded w-full" />
        </div>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-sm">Status</label>
          <div className="text-sm text-slate-300">
            {schedStatus === null && <span>unknown</span>}
            {schedStatus && !schedStatus.running && <span>stopped</span>}
            {schedStatus && schedStatus.running && (
              <span>running — next: {schedStatus.next_run_time ?? 'n/a'} (interval: {schedStatus.interval_seconds ?? 'n/a'}s)</span>
            )}
          </div>
          <Button onClick={() => {
            const token = (document.getElementById('sched-token') as HTMLInputElement).value
            fetchStatus(token)
          }}>Refresh</Button>
        </div>
        <div className="flex gap-2">
          <Button onClick={async () => {
            const interval = Number((document.getElementById('sched-interval') as HTMLInputElement).value || 60)
            const token = (document.getElementById('sched-token') as HTMLInputElement).value
            const headers: Record<string,string> = {'Content-Type': 'application/json'}
            if (token) headers['Authorization'] = `Bearer ${token}`
            await fetch('/schedule/start', { method: 'POST', headers, body: JSON.stringify({ symbol: coin, interval_seconds: interval }) })
            // refresh status after starting
            setTimeout(() => fetchStatus(token), 500)
          }}>Start</Button>
          <Button onClick={async () => {
            const token = (document.getElementById('sched-token') as HTMLInputElement).value
            const headers: Record<string,string> = {}
            if (token) headers['Authorization'] = `Bearer ${token}`
            await fetch('/schedule/stop', { method: 'POST', headers })
            setTimeout(() => fetchStatus(token), 500)
          }}>Stop</Button>
        </div>
      </div>



      <div className="flex items-center gap-3">
        <label className="text-sm">Use local mock server</label>
        <input
          type="checkbox"
          checked={useMock}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUseMock(e.target.checked)}
          aria-label="Use mock server"
          className="h-4 w-4"
        />
      </div>

      <div>
        <Button onClick={() => setOpen(true)} className="bg-indigo-600 text-white">About</Button>
        {open && (
          <DialogVariant>
            <div>
              <h3 className="text-lg font-semibold mb-2">About Pluto</h3>
              <p className="text-sm text-slate-700 dark:text-slate-300">
                Pluto is a decentralized chat assistant demo that returns price and news data. This dialog is
                a local UI demo.
              </p>
              <div className="mt-4 text-right">
                <Button onClick={() => setOpen(false)}>Close</Button>
              </div>
            </div>
          </DialogVariant>
        )}
      </div>
    </div>
  )
}
