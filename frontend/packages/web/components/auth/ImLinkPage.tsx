'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { ApiError, createApiClient, confirmImLink, requestImLinkAccess } from '@cubeplex/core'

type Status = 'verifying' | 'success' | 'requestAccess' | 'pending' | 'error'
type ErrorKey = 'invalidToken' | 'emailMismatch' | 'notMember' | 'error'

const CODE_TO_KEY: Record<string, ErrorKey> = {
  invalid_token: 'invalidToken',
  email_mismatch: 'emailMismatch',
  not_member: 'notMember',
}

export function ImLinkPage() {
  const t = useTranslations('im.link')
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')
  const client = useMemo(() => createApiClient(''), [])
  const confirmation = useRef<{
    token: string
    promise: ReturnType<typeof confirmImLink>
  } | null>(null)

  const [status, setStatus] = useState<Status>('verifying')
  const [errorMsg, setErrorMsg] = useState('')
  const [platform, setPlatform] = useState('')

  useEffect(() => {
    if (!token) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- mount-time validation
      setStatus('error')
      setErrorMsg(t('invalidToken'))
      return
    }
    let active = true
    // Reuse the request when StrictMode replays this effect.
    if (confirmation.current?.token !== token) {
      confirmation.current = { token, promise: confirmImLink(client, token) }
    }
    setStatus('verifying')
    confirmation.current.promise
      .then((result) => {
        if (!active) return
        setStatus('success')
        setPlatform(result.platform)
      })
      .catch((err: unknown) => {
        if (!active) return
        if (err instanceof ApiError && err.status === 401) {
          const returnUrl = `/im-link?token=${encodeURIComponent(token)}`
          // LoginForm reads ``next``, not ``redirect`` — using the wrong param
          // silently drops the return URL and the user lands on home with no
          // binding feedback.
          router.replace(`/login?next=${encodeURIComponent(returnUrl)}`)
          return
        }
        if (err instanceof ApiError && err.code === 'not_member') {
          setStatus('requestAccess')
          return
        }
        setStatus('error')
        const key = err instanceof ApiError && err.code ? CODE_TO_KEY[err.code] : undefined
        setErrorMsg(key ? t(key) : t('error'))
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- router/t are stable
  }, [client, token])

  if (status === 'verifying') {
    return <p className="text-center text-sm text-muted-foreground">{t('verifying')}</p>
  }

  if (status === 'success') {
    return (
      <div className="text-center space-y-3">
        <p className="text-sm font-medium">{t('success', { platform })}</p>
        <Link href="/" className="text-sm text-primary underline">
          {t('goToApp')}
        </Link>
      </div>
    )
  }

  if (status === 'requestAccess') {
    return (
      <div className="text-center space-y-3">
        <p className="text-sm text-muted-foreground">{t('accessRequired')}</p>
        <button
          type="button"
          className="text-sm font-medium text-primary underline"
          onClick={() => {
            if (!token) return
            requestImLinkAccess(client, token)
              .then((result) => setStatus(result.status === 'approved' ? 'success' : 'pending'))
              .catch((err: unknown) => {
                setErrorMsg(err instanceof Error ? err.message : t('error'))
                setStatus('error')
              })
          }}
        >
          {t('requestAccess')}
        </button>
      </div>
    )
  }

  if (status === 'pending') {
    return <p className="text-center text-sm text-muted-foreground">{t('accessPending')}</p>
  }

  return (
    <div className="text-center space-y-3">
      <p className="text-sm text-destructive">{errorMsg}</p>
      <Link href="/" className="text-sm text-primary underline">
        {t('goToApp')}
      </Link>
    </div>
  )
}
