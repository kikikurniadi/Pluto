import { render } from '@testing-library/react'
import Input from '../Input'

describe('Input', () => {
  it('renders and accepts value', () => {
    const { container } = render(<Input value="hello" />)
    expect(container.querySelector('input')?.getAttribute('value')).toBe('hello')
  })
})
