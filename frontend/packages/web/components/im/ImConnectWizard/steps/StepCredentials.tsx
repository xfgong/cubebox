'use client'

import { useTranslations } from 'next-intl'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

import type { WizardStepProps } from '../platforms/types'

type DynamicT = (key: string, values?: Record<string, string | number>) => string

function FieldHint({ text }: { text: string }): React.ReactElement {
  return <p className="text-xs leading-snug text-muted-foreground">{text}</p>
}

export function StepCredentials({
  descriptor,
  form,
  onChange,
}: WizardStepProps): React.ReactElement {
  const t = useTranslations() as unknown as DynamicT
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-3">
      {descriptor.credentialFields.map((f) => {
        if (f.showIf && !f.showIf(form)) return null
        const fieldClass = cn('min-w-0 space-y-1.5', f.fullWidth && 'sm:col-span-2')
        const hint = f.descriptionKey ? <FieldHint text={t(f.descriptionKey)} /> : null
        if (f.type === 'select' && f.options) {
          return (
            <div key={f.key} className={fieldClass}>
              <Label htmlFor={`cred-${f.key}`} className="leading-snug">
                {t(f.labelKey)}
              </Label>
              <Select
                value={form[f.key] ?? ''}
                onValueChange={(v) => onChange({ [f.key]: v ?? '' })}
              >
                <SelectTrigger id={`cred-${f.key}`}>
                  <SelectValue placeholder={t('im.wizard.credentials.placeholderSelect')} />
                </SelectTrigger>
                <SelectContent>
                  {f.options.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {t(o.labelKey)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {hint}
            </div>
          )
        }
        return (
          <div key={f.key} className={fieldClass}>
            <Label htmlFor={`cred-${f.key}`} className="leading-snug">
              {t(f.labelKey)}
            </Label>
            <Input
              id={`cred-${f.key}`}
              type={f.type}
              required={f.required}
              placeholder={f.placeholder}
              value={form[f.key] ?? ''}
              onChange={(e) => onChange({ [f.key]: e.target.value })}
            />
            {hint}
          </div>
        )
      })}
    </div>
  )
}
