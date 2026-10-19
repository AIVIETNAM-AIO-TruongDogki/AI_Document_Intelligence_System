"use client"

import { PanelLeftClose, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { ChatHistory } from "./chat-history"
import { useDocMind } from "./docmind-provider"
import { KnowledgeBase } from "./knowledge-base"
import { Logo } from "./logo"

interface SidebarProps {
  onCollapse: () => void
  onNavigate?: () => void
}

export function Sidebar({ onCollapse, onNavigate }: SidebarProps) {
  const { newChat } = useDocMind()

  return (
    <div className="flex h-full flex-col text-sidebar-foreground">
      <div className="flex flex-col gap-3 p-3">
        <div className="flex items-center justify-between pl-1">
          <Logo />
          <Tooltip>
            <TooltipTrigger
              render={
                <Button variant="ghost" size="icon-sm" onClick={onCollapse} aria-label="Collapse sidebar" />
              }
            >
              <PanelLeftClose />
            </TooltipTrigger>
            <TooltipContent side="right">Collapse sidebar</TooltipContent>
          </Tooltip>
        </div>
        <Button
          className="w-full justify-start gap-2 shadow-[0_0_24px_-6px_var(--primary)]"
          onClick={() => {
            newChat()
            onNavigate?.()
          }}
        >
          <Plus />
          New Chat
          <kbd className="ml-auto rounded border border-primary-foreground/20 px-1.5 font-sans text-[10px] text-primary-foreground/70">
            {"⌘ K"}
          </kbd>
        </Button>
      </div>

      <ChatHistory onNavigate={onNavigate} />
      <KnowledgeBase />
    </div>
  )
}
