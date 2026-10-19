"use client"

import { MessageSquare, MoreHorizontal, Pencil, Trash2 } from "lucide-react"
import { useMemo, useState } from "react"
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ScrollArea } from "@/components/ui/scroll-area"
import { groupSessionsByDate } from "@/lib/docmind/format"
import type { ChatSession } from "@/lib/docmind/types"
import { cn } from "@/lib/utils"
import { useDocMind } from "./docmind-provider"

export function ChatHistory({ onNavigate }: { onNavigate?: () => void }) {
  const { sessions, activeSessionId, selectSession, renameSession, deleteSession } = useDocMind()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [pendingDelete, setPendingDelete] = useState<ChatSession | null>(null)
  const groups = useMemo(() => groupSessionsByDate(sessions), [sessions])

  return (
    <>
      <ScrollArea className="min-h-0 flex-1">
        <nav aria-label="Chat history" className="flex flex-col gap-4 px-3 pb-4">
          {groups.length === 0 && (
            <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed px-4 py-8 text-center">
              <MessageSquare className="size-5 text-muted-foreground" aria-hidden="true" />
              <p className="text-xs text-muted-foreground">No conversations yet. Ask your first question to get started.</p>
            </div>
          )}
          {groups.map((group) => (
            <section key={group.label} aria-labelledby={`group-${group.label}`}>
              <h2
                id={`group-${group.label}`}
                className="px-2 pb-1 text-[11px] font-medium tracking-wide text-muted-foreground uppercase"
              >
                {group.label}
              </h2>
              <ul className="flex flex-col gap-0.5">
                {group.sessions.map((session) => (
                  <li key={session.id}>
                    <SessionRow
                      session={session}
                      active={session.id === activeSessionId}
                      editing={session.id === editingId}
                      onSelect={() => {
                        selectSession(session.id)
                        onNavigate?.()
                      }}
                      onStartRename={() => setEditingId(session.id)}
                      onRename={(title) => {
                        renameSession(session.id, title)
                        setEditingId(null)
                      }}
                      onCancelRename={() => setEditingId(null)}
                      onDelete={() => setPendingDelete(session)}
                    />
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>
      </ScrollArea>

      <AlertDialog open={pendingDelete !== null} onOpenChange={(open) => !open && setPendingDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this chat?</AlertDialogTitle>
            <AlertDialogDescription>
              {`"${pendingDelete?.title ?? ""}" and all of its messages will be permanently removed.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => {
                if (pendingDelete) deleteSession(pendingDelete.id)
                setPendingDelete(null)
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

interface SessionRowProps {
  session: ChatSession
  active: boolean
  editing: boolean
  onSelect: () => void
  onStartRename: () => void
  onRename: (title: string) => void
  onCancelRename: () => void
  onDelete: () => void
}

function SessionRow({ session, active, editing, onSelect, onStartRename, onRename, onCancelRename, onDelete }: SessionRowProps) {
  if (editing) {
    return (
      <input
        autoFocus
        defaultValue={session.title}
        aria-label="Chat title"
        onFocus={(e) => e.currentTarget.select()}
        onBlur={(e) => onRename(e.currentTarget.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onRename(e.currentTarget.value)
          if (e.key === "Escape") onCancelRename()
        }}
        className="h-8 w-full rounded-md border border-ring bg-background px-2 text-sm outline-none ring-3 ring-ring/30"
      />
    )
  }

  return (
    <div
      className={cn(
        "group relative flex h-8 items-center rounded-md text-sm transition-colors",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
      )}
    >
      {active && <span aria-hidden="true" className="absolute top-1.5 bottom-1.5 left-0 w-0.5 rounded-full bg-primary" />}
      <button
        type="button"
        onClick={onSelect}
        onDoubleClick={onStartRename}
        aria-current={active ? "page" : undefined}
        className="h-full min-w-0 flex-1 truncate rounded-md pr-8 pl-2.5 text-left outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
      >
        {session.title}
      </button>
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label={`Actions for ${session.title}`}
          className={cn(
            "absolute right-1 flex size-6 items-center justify-center rounded text-muted-foreground opacity-0 outline-none transition-opacity hover:bg-background/60 hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100 data-popup-open:opacity-100",
            active && "opacity-100",
          )}
        >
          <MoreHorizontal className="size-4" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-40">
          <DropdownMenuItem onClick={onStartRename}>
            <Pencil />
            Rename
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onClick={onDelete}>
            <Trash2 />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
