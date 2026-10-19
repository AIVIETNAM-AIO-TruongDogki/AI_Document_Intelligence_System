"use client"

import { useState } from "react"
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"
import { ChatHeader } from "./chat-header"
import { ChatInput } from "./chat-input"
import { MessageList } from "./message-list"
import { Sidebar } from "./sidebar"

export function AppShell() {
  const [desktopOpen, setDesktopOpen] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex h-dvh overflow-hidden bg-background">
      <aside
        aria-label="Sidebar"
        className={cn(
          "hidden shrink-0 overflow-hidden border-r border-sidebar-border bg-sidebar transition-[width] duration-300 ease-out md:block",
          desktopOpen ? "w-72" : "w-0 border-r-0",
        )}
      >
        <div className="h-full w-72">
          <Sidebar onCollapse={() => setDesktopOpen(false)} />
        </div>
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" showCloseButton={false} className="w-[86vw] max-w-80 gap-0 bg-sidebar p-0 md:hidden">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SheetDescription className="sr-only">Chat history and document knowledge base</SheetDescription>
          <Sidebar onNavigate={() => setMobileOpen(false)} onCollapse={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <main className="relative flex min-w-0 flex-1 flex-col">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[radial-gradient(60%_100%_at_50%_0%,color-mix(in_oklch,var(--primary)_14%,transparent),transparent)]"
        />
        <ChatHeader
          sidebarOpen={desktopOpen}
          onToggleDesktop={() => setDesktopOpen((o) => !o)}
          onOpenMobile={() => setMobileOpen(true)}
        />
        <MessageList />
        <ChatInput />
      </main>
    </div>
  )
}
