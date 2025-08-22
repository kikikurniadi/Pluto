import '@testing-library/jest-dom'
import React from 'react'

// Ensure JSX tests which rely on React in scope work in the test environment
// (some projects use automatic runtime, but the tests expect React to be defined).
(globalThis as any).React = React
