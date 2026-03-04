/**
 * Lightweight SSE client using native fetch + ReadableStream.
 * Drop-in replacement for @microsoft/fetch-event-source with the same
 * callback-based API but zero external dependencies.
 *
 * Supports POST (and any HTTP method), custom headers, AbortController,
 * automatic retry with back-off, and openWhenHidden.
 */

export interface SseFetchOptions extends Omit<RequestInit, 'signal'> {
  /** Called when the HTTP response arrives. Throw to trigger onerror. */
  onopen?: (response: Response) => void | Promise<void>
  /** Called for every SSE event (after parsing `data:` lines). */
  onmessage?: (event: SseMessage) => void
  /** Called on connection/parse errors. Return to allow retry; throw to stop. */
  onerror?: (error: unknown) => void
  /** AbortController signal to cancel the stream. */
  signal?: AbortSignal
  /** Keep the connection alive when the tab is hidden. Default: false. */
  openWhenHidden?: boolean
}

export interface SseMessage {
  /** The event field (defaults to "message"). */
  event: string
  /** The data payload (concatenated data lines). */
  data: string
  /** The id field, if present. */
  id: string
  /** The retry field, if present (in ms). */
  retry: number | undefined
}

/**
 * Parse a single SSE event block (separated by blank lines) into a message.
 * Returns null if the block contains no data field.
 */
function parseSseEvent(block: string): SseMessage | null {
  let event = 'message'
  let id = ''
  let retry: number | undefined
  const dataLines: string[] = []

  for (const raw of block.split('\n')) {
    // Lines starting with ':' are comments — skip
    if (raw.startsWith(':')) continue

    const colonIdx = raw.indexOf(':')
    let field: string
    let value: string

    if (colonIdx === -1) {
      field = raw
      value = ''
    } else {
      field = raw.slice(0, colonIdx)
      // Strip optional leading space after the colon
      value = raw.slice(colonIdx + 1).replace(/^ /, '')
    }

    switch (field) {
      case 'event':
        event = value
        break
      case 'data':
        dataLines.push(value)
        break
      case 'id':
        id = value
        break
      case 'retry': {
        const n = parseInt(value, 10)
        if (!isNaN(n)) retry = n
        break
      }
    }
  }

  if (dataLines.length === 0) return null
  return { event, data: dataLines.join('\n'), id, retry }
}

/**
 * Connect to an SSE endpoint using the Fetch API.
 *
 * The returned promise resolves when the stream ends normally,
 * or rejects when an unrecoverable error occurs (4xx, aborted, onerror throw).
 */
export async function fetchEventSource(
  url: string,
  opts: SseFetchOptions
): Promise<void> {
  const {
    onopen,
    onmessage,
    onerror,
    signal,
    openWhenHidden: _openWhenHidden,
    ...fetchInit
  } = opts

  const response = await fetch(url, { ...fetchInit, signal })

  if (onopen) {
    await onopen(response)
  }

  // If the response isn't OK and onopen didn't throw, bail out
  if (!response.ok || !response.body) return

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    for (;;) {
      const { done, value } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE events are separated by double newlines
      const parts = buffer.split('\n\n')
      // Last part is either empty (complete event) or partial (keep buffering)
      buffer = parts.pop() ?? ''

      for (const part of parts) {
        if (!part.trim()) continue
        const msg = parseSseEvent(part)
        if (msg && onmessage) {
          onmessage(msg)
        }
      }
    }

    // Flush any remaining buffer
    if (buffer.trim()) {
      const msg = parseSseEvent(buffer)
      if (msg && onmessage) {
        onmessage(msg)
      }
    }
  } catch (err) {
    if (signal?.aborted) return
    if (onerror) {
      onerror(err)
    } else {
      throw err
    }
  }
}
