import type { ReactNode } from 'react'

export function Dialog({ children }: { children: ReactNode }) {
  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="bg-black/50 absolute inset-0" />
      <div className="bg-white dark:bg-slate-900 p-4 rounded-md relative z-10 shadow-lg">{children}</div>
    </div>
  )
}

export default Dialog
