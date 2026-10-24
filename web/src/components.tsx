import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';

export function Icon({ name, className = '' }: { name: string; className?: string }) {
  return <img src={`/assets/${name}.svg`} alt="" aria-hidden="true" className={`icon ${className}`} />;
}

export function Card({ title, subtitle, children, className = '', testId }: { title: string; subtitle?: string; children?: ReactNode; className?: string; testId?: string }) {
  return <section className={`card ${className}`} data-testid={testId}><div className="card-heading"><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{children}</section>;
}

export function Dialog({ kind, title, children, onClose, hideClose = false }: { kind: string; title: string; children: ReactNode; onClose: () => void; hideClose?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  const previous = useRef<HTMLElement | null>(null);
  useEffect(() => {
    previous.current = document.activeElement as HTMLElement;
    const dialog = ref.current;
    dialog?.showModal();
    return () => { dialog?.close(); previous.current?.focus(); };
  }, []);
  return <dialog ref={ref} className={`dialog dialog-${kind}`} aria-label={title} onKeyDown={event=>{if(event.key!=='Tab')return;const items=Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),textarea:not(:disabled),select:not(:disabled),iframe,[tabindex="0"]'));const first=items[0],last=items.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}} onCancel={event => { event.preventDefault(); onClose(); }} onClick={event => { if (event.target === event.currentTarget) { const r = event.currentTarget.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) onClose(); } }}>
    {!hideClose && <button className="close-dialog" aria-label={`Close ${title}`} onClick={onClose}><span aria-hidden="true">×</span></button>}
    {children}
  </dialog>;
}

export function Pill({ children, kind = 'blue' }: { children: ReactNode; kind?: 'blue' | 'green' | 'amber' | 'gray' }) {
  return <span className={`pill pill-${kind}`}>{children}</span>;
}
