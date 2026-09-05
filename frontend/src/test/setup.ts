import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'

import { server } from '@/test/msw/server'

function polyfillDomRange() {
  const rect = {
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    toJSON: () => ({}),
  } as DOMRect

  const rectList = {
    length: 1,
    item: () => rect,
    [Symbol.iterator]: function* () {
      yield rect
    },
  } as unknown as DOMRectList

  if (!Range.prototype.getClientRects) {
    Range.prototype.getClientRects = () => rectList
  }
  if (!Range.prototype.getBoundingClientRect) {
    Range.prototype.getBoundingClientRect = () => rect
  }
  if (!Element.prototype.getClientRects) {
    Element.prototype.getClientRects = () => rectList
  }
  if (!Element.prototype.getBoundingClientRect) {
    Element.prototype.getBoundingClientRect = () => rect
  }
  if (!document.elementFromPoint) {
    document.elementFromPoint = () => null
  }
}

polyfillDomRange()

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  localStorage.removeItem('aminvc_device_id')
})
afterAll(() => server.close())
