import type { ChatSession } from "./types"

export function formatBytes(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`
  return `${bytes} B`
}

export function formatPages(pages: number[]) {
  if (pages.length === 0) return ""
  if (pages.length === 1) return `Page ${pages[0]}`
  return `Pages ${pages[0]}–${pages[pages.length - 1]}`
}

export function createId(prefix: string) {
  const random =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().slice(0, 8)
      : Math.random().toString(36).slice(2, 10)
  return `${prefix}_${random}`
}

export function deriveSessionTitle(message: string) {
  const clean = message.replace(/\s+/g, " ").trim()
  return clean.length > 44 ? `${clean.slice(0, 44).trimEnd()}…` : clean
}

const GROUP_ORDER = ["Today", "Yesterday", "Previous 7 Days", "Older"] as const
export type SessionGroupLabel = (typeof GROUP_ORDER)[number]

export function groupSessionsByDate(sessions: ChatSession[], now = new Date()) {
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const day = 24 * 60 * 60 * 1000
  const groups = new Map<SessionGroupLabel, ChatSession[]>()

  const sorted = [...sessions].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  )

  for (const session of sorted) {
    const t = new Date(session.updated_at).getTime()
    const label: SessionGroupLabel =
      t >= startOfToday
        ? "Today"
        : t >= startOfToday - day
          ? "Yesterday"
          : t >= startOfToday - 7 * day
            ? "Previous 7 Days"
            : "Older"
    const list = groups.get(label) ?? []
    list.push(session)
    groups.set(label, list)
  }

  return GROUP_ORDER.filter((label) => groups.has(label)).map((label) => ({
    label,
    sessions: groups.get(label)!,
  }))
}
