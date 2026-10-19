"use client"

import { Database } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { DocumentList } from "./document-list"
import { useDocMind } from "./docmind-provider"
import { IngestionQueue } from "./ingestion-queue"
import { UploadZone } from "./upload-zone"

export function KnowledgeBase() {
  const { documents, scope, setScope, contextDocuments } = useDocMind()

  return (
    <section aria-labelledby="kb-heading" className="flex max-h-[58%] min-h-0 flex-col border-t border-sidebar-border">
      <div className="flex items-center justify-between gap-2 px-4 pt-3 pb-2">
        <h2 id="kb-heading" className="flex items-center gap-1.5 text-xs font-semibold tracking-wide uppercase">
          <Database className="size-3.5 text-primary" aria-hidden="true" />
          Knowledge Base
        </h2>
        <span className="text-[11px] text-muted-foreground tabular-nums">
          {contextDocuments.length}/{documents.length} in context
        </span>
      </div>

      <div className="px-3 pb-2">
        <div role="radiogroup" aria-label="Query scope" className="grid grid-cols-2 gap-1 rounded-lg bg-sidebar-accent/70 p-0.5">
          {(
            [
              { value: "all", label: "All documents" },
              { value: "selected", label: "Selected only" },
            ] as const
          ).map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={scope === option.value}
              onClick={() => setScope(option.value)}
              className={cn(
                "h-7 rounded-md text-xs font-medium transition-all outline-none focus-visible:ring-2 focus-visible:ring-ring/60",
                scope === option.value
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <div className="flex flex-col gap-3 px-3 pb-3">
          <UploadZone />
          <IngestionQueue />
          <DocumentList />
        </div>
      </ScrollArea>
    </section>
  )
}
