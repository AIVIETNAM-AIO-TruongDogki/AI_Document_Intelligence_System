"use client"

import { AlertCircle, CheckCircle2, Clock, Loader2, X } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { formatBytes } from "@/lib/docmind/format"
import type { IngestionJob, JobProgress } from "@/lib/docmind/types"
import { cn } from "@/lib/utils"
import { useDocMind } from "./docmind-provider"

const STATUS_STYLES: Record<JobProgress["status"], { badge: string; bar: string; label: string }> = {
  PENDING: {
    badge: "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400",
    bar: "[&_[data-slot=progress-indicator]]:bg-amber-500",
    label: "Pending",
  },
  PROCESSING: {
    badge: "border-sky-500/30 bg-sky-500/10 text-sky-600 dark:text-sky-400",
    bar: "[&_[data-slot=progress-indicator]]:bg-sky-500",
    label: "Processing",
  },
  COMPLETED: {
    badge: "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    bar: "[&_[data-slot=progress-indicator]]:bg-emerald-500",
    label: "Completed",
  },
  FAILED: {
    badge: "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400",
    bar: "[&_[data-slot=progress-indicator]]:bg-red-500",
    label: "Failed",
  },
}

export function IngestionQueue() {
  const { jobs, dismissJob, clearFinishedJobs } = useDocMind()
  if (jobs.length === 0) return null

  const active = jobs.filter((j) => j.status === "PENDING" || j.status === "PROCESSING").length
  const finished = jobs.length - active

  return (
    <section aria-labelledby="jobs-heading" className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between px-1">
        <h3 id="jobs-heading" className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
          Ingestion Jobs {active > 0 && <span className="text-sky-500 tabular-nums">· {active} active</span>}
        </h3>
        {finished > 0 && (
          <button
            type="button"
            onClick={clearFinishedJobs}
            className="text-[11px] text-muted-foreground transition-colors hover:text-foreground"
          >
            Clear finished
          </button>
        )}
      </div>
      <ul className="flex flex-col gap-1.5" aria-live="polite">
        {jobs.map((job) => (
          <JobRow key={job.job_id} job={job} onDismiss={() => dismissJob(job.job_id)} />
        ))}
      </ul>
    </section>
  )
}

function JobRow({ job, onDismiss }: { job: IngestionJob; onDismiss: () => void }) {
  const style = STATUS_STYLES[job.status]
  const isActive = job.status === "PENDING" || job.status === "PROCESSING"

  return (
    <li className="animate-in fade-in-0 slide-in-from-top-1 rounded-lg border border-sidebar-border bg-background/60 p-2.5 duration-300">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-medium" title={job.filename}>
            {job.filename}
          </p>
          <p className="text-[11px] text-muted-foreground tabular-nums">
            {formatBytes(job.file_size)}
            {job.status === "PROCESSING" && ` · ${job.progress}%`}
          </p>
        </div>
        <StatusBadge job={job} />
        {!isActive && (
          <button
            type="button"
            onClick={onDismiss}
            aria-label={`Dismiss ${job.filename}`}
            className="-mr-1 rounded p-0.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="size-3.5" />
          </button>
        )}
      </div>
      {job.status !== "COMPLETED" && (
        <Progress
          value={job.progress}
          aria-label={`${job.filename} ingestion progress`}
          className={cn("mt-2 gap-0", style.bar, job.status === "PENDING" && "opacity-60")}
        />
      )}
    </li>
  )
}

function StatusBadge({ job }: { job: IngestionJob }) {
  const style = STATUS_STYLES[job.status]
  const icon = {
    PENDING: <Clock aria-hidden="true" />,
    PROCESSING: <Loader2 aria-hidden="true" className="animate-spin" />,
    COMPLETED: <CheckCircle2 aria-hidden="true" />,
    FAILED: <AlertCircle aria-hidden="true" />,
  }[job.status]

  const badge = (
    <Badge variant="outline" className={cn("h-5 shrink-0 gap-1 px-1.5 text-[10px] font-semibold tracking-wide", style.badge)}>
      {job.status === "PROCESSING" && (
        <span aria-hidden="true" className="relative mr-0.5 flex size-1.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-sky-500 opacity-75" />
          <span className="relative inline-flex size-1.5 rounded-full bg-sky-500" />
        </span>
      )}
      {job.status !== "PROCESSING" && icon}
      {job.status}
    </Badge>
  )

  if (job.status !== "FAILED" || !job.error_message) return badge

  return (
    <Tooltip>
      <TooltipTrigger render={<span tabIndex={0} className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring/60" />}>
        {badge}
      </TooltipTrigger>
      <TooltipContent side="right" className="max-w-60">
        {job.error_message}
      </TooltipContent>
    </Tooltip>
  )
}
