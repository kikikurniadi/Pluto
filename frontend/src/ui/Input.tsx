import type { InputHTMLAttributes } from 'react'

export default function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`px-3 py-2 rounded-md ${props.className ?? ''}`} />
}
