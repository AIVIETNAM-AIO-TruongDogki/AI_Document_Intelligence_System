"use client"

import { Check, Copy, FileText, Search } from "lucide-react"
import { useState } from "react"
import { formatPages } from "@/lib/docmind/format"
import type { ChatMessage, CitationSource } from "@/lib/docmind/types"
import { cn } from "@/lib/utils"
import { useDocMind } from "./docmind-provider"
import { LogoMark } from "./logo"
import { Markdown } from "./markdown"

export function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="flex justify-end">
      <p className="max-w-[85%] rounded-2xl rounded-br-md bg-secondary px-4 py-2.5 text-[15px] leading-7 whitespace-pre-wrap text-secondary-foreground">
        <span className="sr-only">You said: </span>
        {message.content}
      </p>
    </div>
  )
}

interface AssistantMessageProps {
  message: ChatMessage
  phase: "retrieving" | "streaming" | null
  onOpenSource: (source: CitationSource) => void
}

export function AssistantMessage({ message, phase, onOpenSource }: AssistantMessageProps) {
  const sources = message.sources ?? []

  return (
    <article aria-label="DocMind response" className="flex gap-3 md:gap-4">
      <LogoMark className="mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        {phase === "retrieving" ? (
          <RetrievingIndicator />
        ) : (
          <>
            <Markdown
              content={message.content}
              sources={sources}
              streaming={phase === "streaming"}
              onOpenSource={onOpenSource}
            />
            {phase === null && sources.length > 0 && <SourceList sources={sources} onOpenSource={onOpenSource} />}
            {phase === null && message.content && <MessageActions content={message.content} />}
          </>
        )}
      </div>
    </article>
  )
}

function RetrievingIndicator() {
  const { contextDocuments } = useDocMind()
  return (
    <div role="status" className="flex flex-col gap-3 pt-1">
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <Search className="size-4 animate-pulse text-primary" aria-hidden="true" />
        {`Searching ${contextDocuments.length} document${contextDocuments.length === 1 ? "" : "s"} for relevant passages…`}
      </p>
      <div aria-hidden="true" className="flex flex-col gap-2">
        {["w-11/12", "w-4/5", "w-2/3"].map((w) => (
          <div key={w} className={cn("h-3 animate-pulse rounded-full bg-muted", w)} />
        ))}
      </div>
    </div>
  )
}

function SourceList({ sources, onOpenSource }: { sources: CitationSource[]; onOpenSource: (s: CitationSource) => void }) {
  return (
    <section aria-label="Sources" className="mt-5">
      <h3 className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
        Sources <span className="tabular-nums">({sources.length})</span>
      </h3>
      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {sources.map((source) => (
          <li key={source.chunk_id}>
            <button
              type="button"
              onClick={() => onOpenSource(source)}
              className="group flex h-full w-full items-start gap-2.5 rounded-lg border border-border/80 bg-card/50 p-2.5 text-left transition-colors outline-none hover:border-primary/40 hover:bg-card focus-visible:ring-2 focus-visible:ring-ring/60"
            >
              <span className="flex size-5 shrink-0 items-center justify-center rounded bg-primary/15 font-mono text-[11px] font-semibold text-primary">
                {source.source_index}
              </span>
              <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="flex items-center gap-1.5 text-xs font-medium">
                  <FileText className="size-3 shrink-0 text-muted-foreground" aria-hidden="true" />
                  <span className="truncate">{source.filename ?? source.document_id}</span>
                </span>
                <span className="text-[11px] text-muted-foreground">{formatPages(source.page_numbers)}</span>
                <span className="line-clamp-2 text-xs leading-5 text-muted-foreground">{`"${source.snippet}"`}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

function MessageActions({ content }: { content: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="mt-3 flex items-center gap-1">
      <button
        type="button"
        onClick={async () => {
          await navigator.clipboard.writeText(content)
          setCopied(true)
          setTimeout(() => setCopied(false), 1600)
        }}
        className="flex h-7 items-center gap-1.5 rounded-md px-2 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        {copied ? <Check className="size-3.5" aria-hidden="true" /> : <Copy className="size-3.5" aria-hidden="true" />}
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  )
}
