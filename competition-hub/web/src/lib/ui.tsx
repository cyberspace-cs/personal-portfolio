import { createContext, useContext, useState, type ReactNode } from 'react'

interface UICtx {
  openLogin: () => void
  loginOpen: boolean
  setLoginOpen: (b: boolean) => void
  toast: (msg: string, kind?: 'ok' | 'err') => void
  message: { text: string; kind: 'ok' | 'err' } | null
}

const C = createContext<UICtx | null>(null)

export function UIProvider({ children }: { children: ReactNode }) {
  const [loginOpen, setLoginOpen] = useState(false)
  const [message, setMessage] = useState<{ text: string; kind: 'ok' | 'err' } | null>(null)

  function toast(text: string, kind: 'ok' | 'err' = 'ok') {
    setMessage({ text, kind })
    window.setTimeout(() => setMessage(null), 2800)
  }

  return (
    <C.Provider value={{ openLogin: () => setLoginOpen(true), loginOpen, setLoginOpen, toast, message }}>
      {children}
    </C.Provider>
  )
}

export function useUI() {
  const c = useContext(C)
  if (!c) throw new Error('useUI 必须在 UIProvider 内使用')
  return c
}
