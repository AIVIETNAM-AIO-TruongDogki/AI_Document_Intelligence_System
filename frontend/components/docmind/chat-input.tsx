"use client"

import { ArrowUp, Layers, Square } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { useDocMind } from "./docmind-provider"

export function ChatInput() {
  const { sendMessage, stopGeneration, generation, contextDocuments, scope, activeSessionId, newChat } = useDocMind()
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const busy = Boolean(generation)
  const canSend = value.trim().length > 0 && !busy

  useEffect(() => {
    textareaRef.current?.focus()
  }, [activeSessionId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        newChat()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [newChat])

  const submit = () => {
    if (!canSend) return
    sendMessage(value)
    setValue("")
  }

  const contextLabel =
    scope === "all"
      ? `All documents (${contextDocuments.length})`
      : contextDocuments.length === 0
        ? "No documents selected"
        : `${contextDocuments.length} selected`

  return (
    <div className="relative z-10 shrink-0 px-3 pb-3 md:px-6 md:pb-5">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
        className="mx-auto w-full max-w-3xl rounded-2xl border border-border bg-card/80 shadow-[0_8px_40px_-16px_color-mix(in_oklch,var(--primary)_45%,transparent)] backdrop-blur-xl transition-colors focus-within:border-primary/50"
      >
        <label htmlFor="chat-input" className="sr-only">
          Ask a question about your documents
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              if (e.nativeEvent.isComposing || e.keyCode === 229) return
              e.preventDefault()
              submit()
            }
          }}
          placeholder="Ask anything about your documents…"
          className="field-sizing-content block max-h-52 min-h-14 w-full resize-none bg-transparent px-4 pt-4 pb-2 text-[15px] leading-6 outline-none placeholder:text-muted-foreground"
        />
        <div className="flex items-center justify-between gap-2 px-2.5 pb-2.5">
          <span
            className={cn(
              "flex h-7 items-center gap-1.5 rounded-full border px-2.5 text-xs",
              contextDocuments.length === 0
                ? "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400"
                : "border-border bg-background/60 text-muted-foreground",
            )}
          >
            <Layers className="size-3.5" aria-hidden="true" />
            <span className="sr-only">Context: </span>
            {contextLabel}
          </span>
          {busy ? (
            <button
              type="button"
              onClick={stopGeneration}
              aria-label="Stop generating"
              className="flex size-8 items-center justify-center rounded-full bg-foreground text-background transition-transform hover:scale-105"
            >
              <Square className="size-3 fill-current" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!canSend}
              aria-label="Send message"
              className="flex size-8 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-[0_0_16px_-4px_var(--primary)] transition-all hover:scale-105 disabled:scale-100 disabled:bg-muted disabled:text-muted-foreground disabled:shadow-none"
            >
              <ArrowUp className="size-4" />
            </button>
          )}
        </div>
      </form>
      <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-muted-foreground">
        DocMind answers only from your uploaded documents. Verify important details against the cited pages.
      </p>
    </div>
  )
}
