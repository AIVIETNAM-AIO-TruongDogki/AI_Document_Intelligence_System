"use client"

import { ArrowDown } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import type { CitationSource } from "@/lib/docmind/types"
import { useDocMind } from "./docmind-provider"
import { EmptyState } from "./empty-state"
import { AssistantMessage, UserMessage } from "./message"
import { SourcePreview } from "./source-preview"

export function MessageList() {
  const { messages, activeSessionId, generation } = useDocMind()
  const scrollRef = useRef<HTMLDivElement>(null)
  const stickToBottom = useRef(true)
  const [showJump, setShowJump] = useState(false)
  const [preview, setPreview] = useState<CitationSource | null>(null)

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior })
  }, [])

  useEffect(() => {
    stickToBottom.current = true
    scrollToBottom("instant")
  }, [activeSessionId, scrollToBottom])

  const lastContent = messages.at(-1)?.content
  useEffect(() => {
    if (stickToBottom.current) scrollToBottom("instant")
  }, [messages.length, lastContent, scrollToBottom])

  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight
    stickToBottom.current = distance < 80
    setShowJump(distance > 240)
  }

  return (
    <div className="relative min-h-0 flex-1">
      <div ref={scrollRef} onScroll={handleScroll} className="h-full overflow-y-auto">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <ol aria-label="Conversation" className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-4 pt-8 pb-10 md:px-6">
            {messages.map((message) => (
              <li key={message.id}>
                {message.role === "user" ? (
                  <UserMessage message={message} />
                ) : (
                  <AssistantMessage
                    message={message}
                    phase={generation?.messageId === message.id ? generation.phase : null}
                    onOpenSource={setPreview}
                  />
                )}
              </li>
            ))}
          </ol>
        )}
      </div>

      {showJump && (
        <Button
          variant="outline"
          size="icon-sm"
          aria-label="Scroll to latest message"
          onClick={() => scrollToBottom()}
          className="animate-in fade-in-0 zoom-in-95 absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-background/90 shadow-md backdrop-blur"
        >
          <ArrowDown />
        </Button>
      )}

      <SourcePreview source={preview} onOpenChange={(open) => !open && setPreview(null)} />
    </div>
  )
}
