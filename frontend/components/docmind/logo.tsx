import { BrainCircuit } from "lucide-react"
import { cn } from "@/lib/utils"

export function LogoMark({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-[oklch(0.55_0.2_260)] text-primary-foreground shadow-[0_0_18px_-4px_var(--primary)]",
        className,
      )}
    >
      <BrainCircuit className="size-4" />
    </span>
  )
}

export function Logo() {
  return (
    <div className="flex items-center gap-2">
      <LogoMark />
      <span className="text-[15px] font-semibold tracking-tight">DocMind</span>
    </div>
  )
}
