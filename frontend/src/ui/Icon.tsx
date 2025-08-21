import { type ComponentProps } from 'react'
// Optional lucide-react icon wrapper. If lucide-react is not installed,
// consumers can replace this with any icon set.
export function Icon(props: ComponentProps<'svg'> & { name?: string; as?: React.ComponentType<unknown> | undefined }) {
  // If user provided a component in `as`, render it.
  const As = props.as
  if (As) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return <As {...(props as any)} />
  }

  // Fallback simple svg (dot)
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <circle cx="12" cy="12" r="8" fill="currentColor" />
    </svg>
  )
}

export default Icon
