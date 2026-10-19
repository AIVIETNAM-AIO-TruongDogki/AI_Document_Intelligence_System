"use client"

import { Check, Copy } from "lucide-react"
import { isValidElement, useRef, useState } from "react"

export function CodeBlock({ children }: { children: React.ReactNode }) {
  const preRef = useRef<HTMLPreElement>(null)
  const [copied, setCopied] = useState(false)

  const className = isValidElement<{ className?: string }>(children) ? (children.props.className ?? "") : ""
  const language = /language-(\w+)/.exec(className)?.[1] ?? "text"

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-muted/40 dark:bg-black/30">
      <div className="flex h-9 items-center justify-between border-b border-border/70 pr-1.5 pl-3.5">
        <span className="font-mono text-[11px] text-muted-foreground">{language}</span>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard.writeText(preRef.current?.textContent ?? "")
            setCopied(true)
            setTimeout(() => setCopied(false), 1600)
          }}
          className="flex h-6 items-center gap-1.5 rounded-md px-2 text-[11px] text-muted-foreground transition-colors hover:bg-background/70 hover:text-foreground"
        >
          {copied ? <Check className="size-3" aria-hidden="true" /> : <Copy className="size-3" aria-hidden="true" />}
          {copied ? "Copied" : "Copy code"}
        </button>
      </div>
      <pre ref={preRef} className="overflow-x-auto p-4 font-mono text-[13px] leading-6">
        {children}
      </pre>
    </div>
  )
}
