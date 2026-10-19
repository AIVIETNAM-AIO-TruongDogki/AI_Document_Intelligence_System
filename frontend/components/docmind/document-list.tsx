"use client"

import { FileText, Trash2 } from "lucide-react"
import { useState } from "react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Checkbox } from "@/components/ui/checkbox"
import { formatBytes } from "@/lib/docmind/format"
import type { DocumentItem } from "@/lib/docmind/types"
import { cn } from "@/lib/utils"
import { useDocMind } from "./docmind-provider"

export function DocumentList() {
  const { documents, scope, selectedDocIds, toggleDocument, deleteDocument } = useDocMind()
  const [pendingDelete, setPendingDelete] = useState<DocumentItem | null>(null)

  return (
    <section aria-labelledby="docs-heading" className="flex flex-col gap-1.5">
      <h3 id="docs-heading" className="px-1 text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
        Documents <span className="tabular-nums">({documents.length})</span>
      </h3>

      {documents.length === 0 ? (
        <div className="flex flex-col items-center gap-1.5 rounded-lg border border-dashed border-sidebar-border px-4 py-6 text-center">
          <FileText className="size-5 text-muted-foreground" aria-hidden="true" />
          <p className="text-xs font-medium">No documents yet</p>
          <p className="text-[11px] text-muted-foreground">Upload a PDF to build your knowledge base.</p>
        </div>
      ) : (
        <ul className="flex flex-col gap-1">
          {documents.map((doc) => {
            const selected = selectedDocIds.includes(doc.document_id)
            const inContext = scope === "all" || selected
            return (
              <li
                key={doc.document_id}
                className={cn(
                  "group animate-in fade-in-0 flex items-center gap-2.5 rounded-lg border px-2.5 py-2 transition-colors duration-300",
                  scope === "selected" && selected
                    ? "border-primary/40 bg-primary/5"
                    : "border-transparent hover:border-sidebar-border hover:bg-background/60",
                  !inContext && "opacity-60",
                )}
              >
                {scope === "selected" ? (
                  <Checkbox
                    checked={selected}
                    onCheckedChange={() => toggleDocument(doc.document_id)}
                    aria-label={`Include ${doc.filename} in context`}
                  />
                ) : (
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-red-500/10 text-red-500 dark:text-red-400">
                    <FileText className="size-3.5" aria-hidden="true" />
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => toggleDocument(doc.document_id)}
                  className="min-w-0 flex-1 text-left outline-none"
                  aria-label={`${selected ? "Remove" : "Add"} ${doc.filename} ${selected ? "from" : "to"} selected context`}
                >
                  <p className="truncate text-xs font-medium" title={doc.filename}>
                    {doc.filename}
                  </p>
                  <p className="text-[11px] text-muted-foreground tabular-nums">
                    {doc.page_count} pages · {formatBytes(doc.file_size)}
                  </p>
                </button>
                <button
                  type="button"
                  onClick={() => setPendingDelete(doc)}
                  aria-label={`Delete ${doc.filename}`}
                  className="rounded p-1 text-muted-foreground opacity-0 transition-all outline-none group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </li>
            )
          })}
        </ul>
      )}

      <AlertDialog open={pendingDelete !== null} onOpenChange={(open) => !open && setPendingDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete document?</AlertDialogTitle>
            <AlertDialogDescription>
              {`${pendingDelete?.filename ?? ""} and its indexed chunks will be removed from the knowledge base and excluded from future answers.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => {
                if (pendingDelete) deleteDocument(pendingDelete.document_id)
                setPendingDelete(null)
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  )
}
