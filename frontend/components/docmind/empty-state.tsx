"use client"

import { ArrowUpRight, FileSearch, FileText, ShieldAlert, Wallet } from "lucide-react"
import { PROMPT_STARTERS } from "@/lib/docmind/seed"
import { useDocMind } from "./docmind-provider"
import { LogoMark } from "./logo"

const STARTER_ICONS = [Wallet, FileText, FileSearch, ShieldAlert]

export function EmptyState() {
  const { sendMessage, contextDocuments, generation } = useDocMind()

  return (
    <div className="mx-auto flex min-h-full w-full max-w-2xl flex-col items-center justify-center px-4 py-12">
      <LogoMark className="size-12 rounded-2xl [&_svg]:size-6" />
      <h2 className="mt-5 text-center text-2xl font-semibold tracking-tight text-balance md:text-3xl">
        What would you like to know?
      </h2>
      <p className="mt-2 max-w-md text-center text-sm leading-6 text-pretty text-muted-foreground">
        {contextDocuments.length === 0
          ? "Tải lên tài liệu PDF ở thanh bên trái để bắt đầu phân tích và hỏi đáp thông minh!"
          : `Hỏi bất kỳ điều gì về ${contextDocuments.length} tài liệu trong ngữ cảnh. Mọi câu trả lời đều trích dẫn chính xác trang nguồn.`}
      </p>

      <ul className="mt-8 grid w-full grid-cols-1 gap-2.5 sm:grid-cols-2">
        {PROMPT_STARTERS.map((starter, i) => {
          const Icon = STARTER_ICONS[i]
          return (
            <li key={starter.title}>
              <button
                type="button"
                disabled={Boolean(generation)}
                onClick={() => sendMessage(starter.prompt)}
                className="group flex h-full w-full items-start gap-3 rounded-xl border border-border/80 bg-card/60 p-3.5 text-left transition-all outline-none hover:-translate-y-0.5 hover:border-primary/40 hover:bg-card hover:shadow-[0_8px_30px_-12px_var(--primary)] focus-visible:ring-2 focus-visible:ring-ring/60 disabled:pointer-events-none disabled:opacity-60"
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="size-4" aria-hidden="true" />
                </span>
                <span className="flex min-w-0 flex-1 flex-col">
                  <span className="text-sm font-medium">{starter.title}</span>
                  <span className="text-xs text-muted-foreground">{starter.subtitle}</span>
                </span>
                <ArrowUpRight
                  className="size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
                  aria-hidden="true"
                />
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
