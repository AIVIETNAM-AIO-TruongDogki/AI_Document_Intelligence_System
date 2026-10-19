"use client"

import { UploadCloud } from "lucide-react"
import { useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { useDocMind } from "./docmind-provider"

export function UploadZone() {
  const { uploadFiles } = useDocMind()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false)
      }}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files)
      }}
    >
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className={cn(
          "group flex w-full items-center gap-3 rounded-lg border border-dashed px-3 py-3 text-left transition-all outline-none focus-visible:ring-2 focus-visible:ring-ring/60",
          dragging
            ? "border-primary bg-primary/10 shadow-[0_0_24px_-8px_var(--primary)]"
            : "border-sidebar-border hover:border-primary/50 hover:bg-primary/5",
        )}
      >
        <span
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary transition-transform",
            dragging ? "scale-110" : "group-hover:-translate-y-0.5",
          )}
        >
          <UploadCloud className="size-4" aria-hidden="true" />
        </span>
        <span className="flex min-w-0 flex-col">
          <span className="text-xs font-medium text-foreground">{dragging ? "Drop to upload" : "Upload PDFs"}</span>
          <span className="text-[11px] text-muted-foreground">Drag & drop or click · up to 50 MB</span>
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        className="sr-only"
        tabIndex={-1}
        aria-label="Upload PDF files"
        onChange={(e) => {
          if (e.target.files?.length) uploadFiles(e.target.files)
          e.target.value = ""
        }}
      />
    </div>
  )
}
