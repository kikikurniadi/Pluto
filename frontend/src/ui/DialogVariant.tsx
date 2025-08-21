import type { ReactNode } from 'react'
import Dialog from './Dialog'

export function DialogVariant({ children }: { children: ReactNode }) {
  return (
    <Dialog>
      <div className="min-w-[320px]">{children}</div>
    </Dialog>
  )
}

export default DialogVariant
