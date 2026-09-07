'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Plus } from 'lucide-react'
import {
  createApiClient,
  listWorkspaceAccessRequests,
  resolveWorkspaceAccessRequest,
  useMemberStore,
  useWorkspaceStore,
  type WorkspaceAccessRequest,
} from '@cubeplex/core'
import { Button } from '@/components/ui/button'
import { SETTINGS_CONTENT_WIDTH, SectionHeader } from '@/components/shared/SectionHeader'
import { cn } from '@/lib/utils'
import { WsMembersTable } from './members/WsMembersTable'
import { AddWsMemberDialog } from './members/AddWsMemberDialog'

interface MembersPanelProps {
  wsId: string
}

export function MembersPanel({ wsId }: MembersPanelProps) {
  const t = useTranslations('wsMembers')
  const client = useMemo(() => createApiClient(''), [])
  const wsRole = useWorkspaceStore((s) => s.workspaces.find((w) => w.id === wsId)?.role)
  const isAdmin = wsRole === 'admin'

  const { loadAvailable, addWsMember, available } = useMemberStore()
  const [addOpen, setAddOpen] = useState(false)
  const [requests, setRequests] = useState<WorkspaceAccessRequest[]>([])

  useEffect(() => {
    if (!isAdmin) return
    void listWorkspaceAccessRequests(client, wsId).then(setRequests)
  }, [client, isAdmin, wsId])

  const resolveRequest = useCallback(
    async (requestId: string, approved: boolean) => {
      await resolveWorkspaceAccessRequest(client, wsId, requestId, approved)
      setRequests((current) => current.filter((request) => request.id !== requestId))
    },
    [client, wsId],
  )

  const handleOpenAdd = useCallback(async () => {
    await loadAvailable(client, wsId)
    setAddOpen(true)
  }, [client, wsId, loadAvailable])

  const handleAdd = useCallback(
    async (userId: string, role: string) => {
      await addWsMember(client, wsId, userId, role)
    },
    [client, wsId, addWsMember],
  )

  return (
    <div className="flex h-full flex-col">
      <SectionHeader
        title={t('title')}
        description={t('subtitle')}
        contained={SETTINGS_CONTENT_WIDTH}
        action={
          isAdmin ? (
            <Button size="sm" className="gap-1.5" onClick={() => void handleOpenAdd()}>
              <Plus className="size-3.5" />
              {t('addMember')}
            </Button>
          ) : undefined
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className={cn('flex w-full flex-col gap-6', SETTINGS_CONTENT_WIDTH)}>
          {!isAdmin ? (
            <p className="rounded-md border border-border/60 bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
              {t('accessDenied')}
            </p>
          ) : (
            <>
              <WsMembersTable wsId={wsId} />
              {requests.length > 0 && (
                <section className="space-y-3 rounded-xl border border-border/70 p-4">
                  <h2 className="text-sm font-medium">{t('accessRequests.title')}</h2>
                  {requests.map((request) => (
                    <div
                      key={request.id}
                      className="flex items-center justify-between gap-3 text-sm"
                    >
                      <span>{request.display_name ?? request.email}</span>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => void resolveRequest(request.id, true)}>
                          {t('accessRequests.approve')}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => void resolveRequest(request.id, false)}
                        >
                          {t('accessRequests.reject')}
                        </Button>
                      </div>
                    </div>
                  ))}
                </section>
              )}
            </>
          )}
        </div>
      </div>

      {isAdmin && (
        <AddWsMemberDialog
          open={addOpen}
          onOpenChange={setAddOpen}
          available={available}
          onAdd={handleAdd}
        />
      )}
    </div>
  )
}
