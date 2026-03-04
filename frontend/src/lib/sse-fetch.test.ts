import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchEventSource, type SseMessage } from './sse-fetch'

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  let i = 0
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) {
        controller.enqueue(encoder.encode(chunks[i]))
        i++
      } else {
        controller.close()
      }
    },
  })
}

function mockFetch(status: number, body: ReadableStream<Uint8Array> | null, ok = true) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    statusText: ok ? 'OK' : 'Error',
    body,
  } as unknown as Response)
}

describe('fetchEventSource', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('parses a single SSE event', async () => {
    const messages: SseMessage[] = []
    const body = makeStream(['data: {"type":"hello"}\n\n'])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', {
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages).toHaveLength(1)
    expect(messages[0].data).toBe('{"type":"hello"}')
    expect(messages[0].event).toBe('message')
  })

  it('parses multiple SSE events in one chunk', async () => {
    const messages: SseMessage[] = []
    const body = makeStream([
      'data: first\n\ndata: second\n\n',
    ])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', {
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages).toHaveLength(2)
    expect(messages[0].data).toBe('first')
    expect(messages[1].data).toBe('second')
  })

  it('handles events split across chunks', async () => {
    const messages: SseMessage[] = []
    const body = makeStream([
      'data: par',
      'tial\n\n',
    ])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', {
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages).toHaveLength(1)
    expect(messages[0].data).toBe('partial')
  })

  it('parses event type and id fields', async () => {
    const messages: SseMessage[] = []
    const body = makeStream([
      'event: custom\nid: 42\ndata: payload\n\n',
    ])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', {
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages[0].event).toBe('custom')
    expect(messages[0].id).toBe('42')
  })

  it('calls onopen with the response', async () => {
    const onopen = vi.fn()
    const body = makeStream([])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', { onopen })

    expect(onopen).toHaveBeenCalledOnce()
    expect(onopen.mock.calls[0][0]).toHaveProperty('status', 200)
  })

  it('does not call onmessage for non-ok responses when onopen does not throw', async () => {
    const messages: SseMessage[] = []
    vi.stubGlobal('fetch', mockFetch(404, null, false))

    await fetchEventSource('/test', {
      onopen: () => {},
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages).toHaveLength(0)
  })

  it('skips SSE comment lines', async () => {
    const messages: SseMessage[] = []
    const body = makeStream([':comment\ndata: kept\n\n'])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', {
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages).toHaveLength(1)
    expect(messages[0].data).toBe('kept')
  })

  it('handles multi-line data fields', async () => {
    const messages: SseMessage[] = []
    const body = makeStream(['data: line1\ndata: line2\n\n'])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', {
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages[0].data).toBe('line1\nline2')
  })

  it('passes fetch options correctly', async () => {
    const fetchMock = mockFetch(200, makeStream([]))
    vi.stubGlobal('fetch', fetchMock)

    await fetchEventSource('/api/sse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: 'value' }),
    })

    expect(fetchMock).toHaveBeenCalledWith('/api/sse', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{"key":"value"}',
    }))
  })

  it('calls onerror when stream read throws', async () => {
    const onerror = vi.fn()
    const body = new ReadableStream({
      pull() {
        throw new Error('stream broken')
      },
    })
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', { onerror })

    expect(onerror).toHaveBeenCalledOnce()
    expect(onerror.mock.calls[0][0]).toBeInstanceOf(Error)
  })

  it('flushes remaining buffer on stream end', async () => {
    const messages: SseMessage[] = []
    // No trailing \n\n — data is in buffer at stream end
    const body = makeStream(['data: final'])
    vi.stubGlobal('fetch', mockFetch(200, body))

    await fetchEventSource('/test', {
      onmessage: (msg) => messages.push(msg),
    })

    expect(messages).toHaveLength(1)
    expect(messages[0].data).toBe('final')
  })
})
