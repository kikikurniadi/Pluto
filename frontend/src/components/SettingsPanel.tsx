import { useEffect, useState } from 'react'
import { Select, DialogVariant, Button } from '../ui'

export default function SettingsPanel() {
  const [open, setOpen] = useState(false)
  const [coin, setCoin] = useState('bitcoin')
  const [useMock, setUseMock] = useState(() => {
    try {
      return typeof window !== 'undefined' && window.localStorage?.getItem('useMockServer') === 'true'
    } catch (e) {
      return false
    }
  })

  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('useMockServer', useMock ? 'true' : 'false')
      }
    } catch (e) {
      // ignore
    }
  }, [useMock])

  return (
    <div className="mb-4 flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-300 mr-2">Coin</label>
        <Select value={coin} onChange={(e) => setCoin((e.target as HTMLSelectElement).value)}>
          <option value="bitcoin">Bitcoin</option>
          <option value="ethereum">Ethereum</option>
          <option value="solana">Solana</option>
        </Select>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm">Use local mock server</label>
        <input
          type="checkbox"
          checked={useMock}
          onChange={(e) => setUseMock(e.target.checked)}
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
