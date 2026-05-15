import { createContext, useContext, useEffect } from 'react'

export interface DirtyInfo {
  dirty: boolean
  message: string
}

export interface DirtyAPI {
  register: (tabId: string, info: DirtyInfo) => void
}

const NOOP: DirtyAPI = { register: () => {} }

export const DirtyContext = createContext<DirtyAPI>(NOOP)

/**
 * Register dirty status for a tab. Called by each tab component.
 * The latest value wins; on unmount (which shouldn't normally happen
 * with state-preserving Tabs), the tab is cleared.
 */
export function useTabDirty(tabId: string, dirty: boolean, message: string) {
  const { register } = useContext(DirtyContext)
  useEffect(() => {
    register(tabId, { dirty, message })
  }, [tabId, dirty, message, register])

  useEffect(() => {
    return () => {
      register(tabId, { dirty: false, message: '' })
    }
  }, [tabId, register])
}
