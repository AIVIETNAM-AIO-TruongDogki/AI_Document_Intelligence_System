"use client"

import { Menu, Moon, PanelLeftOpen, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import { useDocMind } from "./docmind-provider"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

interface ChatHeaderProps {
  sidebarOpen: boolean
  onToggleDesktop: () => void
  onOpenMobile: () => void
}

export function ChatHeader({ sidebarOpen, onToggleDesktop, onOpenMobile }: ChatHeaderProps) {
  const { activeSession } = useDocMind()

  return (
    <header className="relative z-10 flex h-14 shrink-0 items-center gap-2 border-b border-border/60 bg-background/70 px-3 backdrop-blur-md md:px-4">
      <Button variant="ghost" size="icon-sm" className="md:hidden" onClick={onOpenMobile} aria-label="Open sidebar">
        <Menu />
      </Button>
      {!sidebarOpen && (
        <Tooltip>
          <TooltipTrigger
            render={
              <Button
                variant="ghost"
                size="icon-sm"
                className="hidden md:inline-flex"
                onClick={onToggleDesktop}
                aria-label="Expand sidebar"
              />
            }
          >
            <PanelLeftOpen />
          </TooltipTrigger>
          <TooltipContent side="bottom">Expand sidebar</TooltipContent>
        </Tooltip>
      )}

      <h1 className="min-w-0 flex-1 truncate text-sm font-medium">{activeSession?.title ?? "New chat"}</h1>

      <ApiStatusPill />
      <ThemeToggle />
    </header>
  )
}

function ApiStatusPill() {
  const { apiStatus } = useDocMind()
  const config = {
    checking: { dot: "bg-amber-500", label: "Connecting", detail: "Checking API health…" },
    connected: {
      dot: "bg-emerald-500",
      label: "Connected",
      detail: apiStatus.state === "connected" ? `${API_BASE_URL} · ${apiStatus.latency}ms` : "",
    },
    offline: { dot: "bg-red-500", label: "Offline", detail: "The DocMind API is unreachable." },
  }[apiStatus.state]

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            tabIndex={0}
            role="status"
            className="flex h-7 items-center gap-1.5 rounded-full border border-border/70 bg-card/60 px-2.5 text-xs text-muted-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
          />
        }
      >
        <span aria-hidden="true" className="relative flex size-2">
          {apiStatus.state === "connected" && (
            <span className={cn("absolute inline-flex size-full animate-ping rounded-full opacity-60", config.dot)} />
          )}
          <span className={cn("relative inline-flex size-2 rounded-full", config.dot)} />
        </span>
        <span className="hidden sm:inline">{config.label}</span>
        <span className="sr-only sm:hidden">{`API ${config.label}`}</span>
      </TooltipTrigger>
      <TooltipContent side="bottom">{config.detail}</TooltipContent>
    </Tooltip>
  )
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      aria-label="Toggle color theme"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      <Sun className="hidden dark:block" />
      <Moon className="dark:hidden" />
    </Button>
  )
}
