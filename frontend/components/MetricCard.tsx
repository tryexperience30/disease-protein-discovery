import type { MetricCard as MetricCardType } from "@/types";

export function MetricCard({ metric, research }: { metric: MetricCardType; research?: boolean }) {
  return (
    <article className="panel p-4" title={metric.description}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm text-muted">{metric.label}</h3>
        <span className="cursor-help text-xs text-muted" aria-label={metric.description} title={metric.description}>
          i
        </span>
      </div>
      <p className="mt-2 font-mono text-2xl tracking-tight">
        {metric.available ? metric.formatted : "—"}
      </p>
      <p className="mt-2 text-sm leading-relaxed text-muted">{metric.interpretation}</p>
      {research && (
        <p className="mt-2 text-xs text-muted">{metric.description}</p>
      )}
    </article>
  );
}
