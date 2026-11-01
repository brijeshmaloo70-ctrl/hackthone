import { createContext, useCallback, useContext, useState } from 'react'
import { CircleAlert, CircleCheck, Info, Lightbulb, X } from 'lucide-react'

const ToastCtx = createContext(() => {})

/** Toasts: const toast = useToast(); toast('Saved', 'success') */
export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const push = useCallback((text, tone = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setItems((t) => [...t, { id, text, tone }])
    setTimeout(() => setItems((t) => t.filter((x) => x.id !== id)), 4200)
  }, [])
  const Icon = { success: CircleCheck, error: CircleAlert, info: Info }
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {items.map((t) => {
          const I = Icon[t.tone] || Info
          return (
            <div key={t.id} className={`toast toast-${t.tone}`}>
              <I size={17} aria-hidden="true" /> <span>{t.text}</span>
              <button onClick={() => setItems((x) => x.filter((y) => y.id !== t.id))} aria-label="Dismiss"><X size={14} /></button>
            </div>
          )
        })}
      </div>
    </ToastCtx.Provider>
  )
}

export const useToast = () => useContext(ToastCtx)

/** Dismissible "how to use this page" card. Remembers dismissal per page. */
export function PageHint({ id, title, steps }) {
  const key = `hint:${id}`
  const [open, setOpen] = useState(() => localStorage.getItem(key) !== 'off')
  if (!open) {
    return (
      <button className="hint-reopen" onClick={() => { localStorage.removeItem(key); setOpen(true) }}>
        <Lightbulb size={14} /> How to use this page
      </button>
    )
  }
  return (
    <div className="hint fade-in">
      <Lightbulb size={18} color="#fcd34d" style={{ flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
      <div style={{ flex: 1 }}>
        <strong>{title}</strong>
        <ol>{steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
      </div>
      <button className="btn btn-ghost btn-sm" onClick={() => { localStorage.setItem(key, 'off'); setOpen(false) }}>Got it</button>
    </div>
  )
}
