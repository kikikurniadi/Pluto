import React from 'react'
import type { ReactNode } from 'react'

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement> & { children?: ReactNode }) {
  const { children, className, ...rest } = props
  return (
    <select {...rest} className={["px-3 py-2 rounded-md bg-slate-700", className].filter(Boolean).join(' ')}>
      {children}
    </select>
  )
}

export default Select
