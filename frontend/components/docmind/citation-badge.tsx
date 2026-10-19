"use client"

import { FileText } from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { formatPages } from "@/lib/docmind/format"
import type { CitationSource } from "@/lib/docmind/types"

export function CitationBadge({ source, onOpen }: { source: CitationSource; onOpen: () => void }) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <button
            type="button"
            data-citation
            onClick={onOpen}
            aria-label={`Source ${source.source_index}: ${source.filename ?? "document"}, ${formatPages(source.page_numbers)}`}
            className="mx-0.5 inline-flex h-[18px] min-w-[18px] -translate-y-px items-center justify-center rounded-md border border-primary/30 bg-primary/10 px-1 align-middle font-mono text-[10px] font-semibold text-primary no-underline transition-all outline-none hover:border-primary/60 hover:bg-primary/20 hover:shadow-[0_0_12px_-2px_var(--primary)] focus-visible:ring-2 focus-visible:ring-ring/60"
          />
        }
      >
        {source.source_index}
      </TooltipTrigger>
      <TooltipContent side="top" className="flex max-w-72 flex-col items-start gap-1 py-2 text-left">
        <span className="flex items-center gap-1.5 font-medium">
          <FileText className="size-3" aria-hidden="true" />
          {source.filename ?? source.document_id}
        </span>
        <span className="opacity-70">{formatPages(source.page_numbers)}</span>
        <span className="line-clamp-3 opacity-90">{`"${source.snippet}"`}</span>
      </TooltipContent>
    </Tooltip>
  )
}
