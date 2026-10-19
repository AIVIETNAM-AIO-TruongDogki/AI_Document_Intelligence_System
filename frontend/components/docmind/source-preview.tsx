"use client"

import { FileText, Hash } from "lucide-react"
import { Fragment } from "react"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { formatPages } from "@/lib/docmind/format"
import { getChunk } from "@/lib/docmind/mock-api"
import type { CitationSource } from "@/lib/docmind/types"

function HighlightedContent({ content, snippet }: { content: string; snippet: string }) {
  const index = content.indexOf(snippet)
  if (index === -1) return <>{content}</>
  return (
    <Fragment>
      {content.slice(0, index)}
      <mark className="rounded bg-primary/20 px-0.5 text-foreground ring-1 ring-primary/30">{snippet}</mark>
      {content.slice(index + snippet.length)}
    </Fragment>
  )
}

export function SourcePreview({
  source,
  onOpenChange,
}: {
  source: CitationSource | null
  onOpenChange: (open: boolean) => void
}) {
  const chunk = source ? getChunk(source.chunk_id) : null

  return (
    <Sheet open={source !== null} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full gap-0 sm:max-w-md">
        <SheetHeader className="border-b border-border pb-4">
          <div className="flex items-center gap-2">
            <span className="flex size-6 items-center justify-center rounded-md bg-primary/15 font-mono text-xs font-semibold text-primary">
              {source?.source_index}
            </span>
            <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Source preview</span>
          </div>
          <SheetTitle className="flex items-start gap-2 pt-2 text-base leading-6">
            <FileText className="mt-1 size-4 shrink-0 text-red-500 dark:text-red-400" aria-hidden="true" />
            <span className="break-all">{source?.filename ?? source?.document_id}</span>
          </SheetTitle>
          <SheetDescription>{source ? formatPages(source.page_numbers) : ""}</SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto p-4">
          {source && (
            <div className="flex flex-col gap-4">
              {chunk?.heading && <h3 className="text-sm font-semibold">{chunk.heading}</h3>}
              <p className="text-sm leading-7 text-muted-foreground">
                {chunk ? (
                  <HighlightedContent content={chunk.content} snippet={source.snippet} />
                ) : (
                  <mark className="rounded bg-primary/20 px-0.5 text-foreground">{source.snippet}</mark>
                )}
              </p>
              <dl className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-muted/30 p-3 text-xs">
                <div>
                  <dt className="text-muted-foreground">Pages</dt>
                  <dd className="mt-0.5 font-medium tabular-nums">{source.page_numbers.join(", ")}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Chunk ID</dt>
                  <dd className="mt-0.5 flex items-center gap-1 font-mono">
                    <Hash className="size-3 text-muted-foreground" aria-hidden="true" />
                    <span className="truncate">{source.chunk_id}</span>
                  </dd>
                </div>
              </dl>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
