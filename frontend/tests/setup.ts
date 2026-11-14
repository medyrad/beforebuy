import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

afterEach(cleanup)
document.documentElement.lang = 'fa'
document.documentElement.dir = 'rtl'

Object.defineProperty(window, 'scrollTo', { value: vi.fn(), writable: true })
