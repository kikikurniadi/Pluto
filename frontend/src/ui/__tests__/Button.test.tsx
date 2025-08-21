import { render } from '@testing-library/react'
import Button from '../Button'

describe('Button', () => {
  it('renders children and forwards className', () => {
    const { getByText } = render(<Button className="test">Click</Button>)
    expect(getByText('Click')).toBeTruthy()
  })
})
