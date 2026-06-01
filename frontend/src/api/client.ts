import type { ApiErrorBody } from '@/types/api'

const API_BASE = '/api/v1'

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorBody
    if (body?.error) {
      return body.error
    }
  } catch {
    // ignore
  }
  return response.statusText || 'Request failed'
}

export async function apiClient<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const headers = new Headers(options.headers)

  if (options.body !== undefined && !(options.body instanceof FormData)) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    const message = await parseError(response)
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    return undefined as T
  }

  const text = await response.text()
  if (!text) {
    return undefined as T
  }

  return JSON.parse(text) as T
}
