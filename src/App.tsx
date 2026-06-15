import { useCallback, useMemo, useRef, useState } from 'react'
import { Tabs, Tab } from './components/Tabs'
import { StatusBar } from './components/StatusBar'
import { SplitTab } from './components/SplitTab'
import { MergeTab } from './components/MergeTab'
import { ExtractTab } from './components/ExtractTab'
import { CompressTab } from './components/CompressTab'
import { ScanTab } from './components/ScanTab'
import { ConfirmModal } from './components/ConfirmModal'
import { DirtyAPI, DirtyContext, DirtyInfo } from './lib/dirtyContext'

const TAB_LABELS: Record<string, string> = {
  split: 'Split',
  merge: 'Merge',
  extract: 'Extract',
  compress: 'Compress',
  scan: 'Photos → PDF',
}

function ResponsiveLabel({ full, short }: { full: string; short: string }) {
  return (
    <>
      <span className="sm:hidden">{short}</span>
      <span className="hidden sm:inline">{full}</span>
    </>
  )
}

export default function App() {
  const [active, setActive] = useState('split')
  const [status, setStatus] = useState('Ready')
  const [pending, setPending] = useState<{ to: string; message: string } | null>(null)

  const dirtyRef = useRef<Record<string, DirtyInfo>>({})
  const dirtyAPI = useMemo<DirtyAPI>(
    () => ({
      register: (tabId, info) => {
        dirtyRef.current[tabId] = info
      },
    }),
    [],
  )

  const tabs = useMemo<Tab[]>(
    () => [
      { id: 'split', label: 'Split', content: <SplitTab setStatus={setStatus} /> },
      { id: 'merge', label: 'Merge', content: <MergeTab setStatus={setStatus} /> },
      {
        id: 'extract',
        label: <ResponsiveLabel full="Extract Text" short="Extract" />,
        content: <ExtractTab setStatus={setStatus} />,
      },
      {
        id: 'compress',
        label: 'Compress',
        content: <CompressTab setStatus={setStatus} />,
      },
      {
        id: 'scan',
        label: <ResponsiveLabel full="Photos → PDF" short="Photos" />,
        content: <ScanTab setStatus={setStatus} />,
      },
    ],
    [],
  )

  const requestTab = useCallback(
    (to: string) => {
      if (to === active) return
      const cur = dirtyRef.current[active]
      if (cur?.dirty) {
        setPending({ to, message: cur.message })
      } else {
        setActive(to)
      }
    },
    [active],
  )

  const confirmSwitch = () => {
    if (pending) setActive(pending.to)
    setPending(null)
  }
  const cancelSwitch = () => setPending(null)

  const fromLabel = TAB_LABELS[active] ?? active
  const toLabel = pending ? TAB_LABELS[pending.to] ?? pending.to : ''

  return (
    <DirtyContext.Provider value={dirtyAPI}>
      <div className="h-full flex flex-col bg-ink">
        <header className="h-12 px-3 sm:px-5 flex items-center bg-panel border-b border-rule shrink-0">
          <div className="h-6 w-6 rounded bg-coral flex items-center justify-center text-white text-[11px] font-bold mr-3">
            P
          </div>
          <div className="text-[13.5px] font-semibold text-cream">PDF Tool</div>
          <div className="ml-3 text-[11.5px] text-stone hidden sm:block">
            Split · Merge · Extract · Compress · Scan
          </div>
        </header>
        <main className="flex-1 min-h-0">
          <Tabs tabs={tabs} active={active} onChange={requestTab} />
        </main>
        <StatusBar message={status} />
      </div>

      <ConfirmModal
        open={pending !== null}
        title={`Unsaved work in ${fromLabel}`}
        message={
          (pending?.message ?? '') +
          ` Switch to ${toLabel} anyway? Your work in ${fromLabel} stays where it is.`
        }
        confirmLabel={`Switch to ${toLabel}`}
        cancelLabel={`Stay in ${fromLabel}`}
        onConfirm={confirmSwitch}
        onCancel={cancelSwitch}
      />
    </DirtyContext.Provider>
  )
}
