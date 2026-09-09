import { StrictMode } from 'react'
import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { NextIntlClientProvider } from 'next-intl'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ImLinkPage } from '@/components/auth/ImLinkPage'
import messages from '@/messages/en.json'

const navigation = vi.hoisted(() => ({ token: 'first', replace: vi.fn() }))
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams({ token: navigation.token }),
  useRouter: () => ({ replace: navigation.replace }),
}))

function page() {
  return (
    <StrictMode>
      <NextIntlClientProvider locale="en" messages={messages}>
        <ImLinkPage />
      </NextIntlClientProvider>
    </StrictMode>
  )
}

const success = () => Response.json({ ok: true, platform: 'wecom', account_id: 'account' })

function pendingResponse() {
  let resolve!: (response: Response) => void
  const promise = new Promise<Response>((complete) => {
    resolve = complete
  })
  return { promise, resolve }
}

describe('IM link confirmation lifecycle', () => {
  beforeEach(() => {
    navigation.token = 'first'
    navigation.replace.mockClear()
  })
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('submits once under StrictMode and still shows the completed binding', async () => {
    const response = pendingResponse()
    const fetch = vi.fn().mockReturnValue(response.promise)
    vi.stubGlobal('fetch', fetch)
    render(page())
    expect(fetch).toHaveBeenCalledTimes(1)
    await act(async () => response.resolve(success()))
    expect(
      screen.getByText(messages.im.link.success.replace('{platform}', 'wecom')),
    ).toBeInTheDocument()
  })

  it('ignores an old failure after a different token has succeeded', async () => {
    const oldResponse = pendingResponse()
    const fetch = vi.fn().mockReturnValue(oldResponse.promise)
    vi.stubGlobal('fetch', fetch)
    const view = render(page())
    navigation.token = 'second'
    fetch.mockResolvedValue(success())
    view.rerender(page())
    await screen.findByText(messages.im.link.success.replace('{platform}', 'wecom'))
    await act(async () => oldResponse.resolve(Response.json({}, { status: 409 })))
    expect(screen.queryByText(messages.im.link.error)).not.toBeInTheDocument()
    expect(
      screen.getByText(messages.im.link.success.replace('{platform}', 'wecom')),
    ).toBeInTheDocument()
  })

  it('preserves the token when redirecting an unauthenticated user to login', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({}, { status: 401 })))
    render(page())
    await waitFor(() =>
      expect(navigation.replace).toHaveBeenCalledWith(
        `/login?next=${encodeURIComponent('/im-link?token=first')}`,
      ),
    )
    expect(navigation.replace).toHaveBeenCalledTimes(1)
  })

  it('lets a non-member request workspace access and shows the pending state', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json(
          { detail: { code: 'not_member', message: 'Not a workspace member.' } },
          { status: 403 },
        ),
      )
      .mockResolvedValueOnce(Response.json({ status: 'pending' }))
    vi.stubGlobal('fetch', fetch)
    render(page())
    const requestAccess = await screen.findByRole('button', {
      name: messages.im.link.requestAccess,
    })
    await act(async () => requestAccess.click())
    expect(await screen.findByText(messages.im.link.accessPending)).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })
})
