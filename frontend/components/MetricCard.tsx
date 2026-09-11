import type { MetricCard as MetricCardType } from "@/types";
import { ConceptExplainer } from "@/components/ConceptExplainer";
import { METRIC_CONCEPT } from "@/lib/concepts";

const BAR_KEYS = new Set(["density", "relative_lcc", "conductance"]);

export function MetricCard({ metric, research }: { metric: MetricCardType; research?: boolean }) {
  const conceptId = METRIC_CONCEPT[metric.key];
  const showBar =
    BAR_KEYS.has(metric.key) && metric.available && metric.value != null && metric.value >= 0 && metric.value <= 1;

  return (
    <article className="panel p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-display text-sm font-medium text-muted">{metric.label}</h3>
        {conceptId ? (
          <ConceptExplainer conceptId={conceptId} tone="learn" />
        ) : (
          <span className="cursor-help text-xs text-muted" aria-label={metric.description} title={metric.description}>
            i
          </span>
        )}
      </div>
      <p className="metric-value mt-2">{metric.available ? metric.formatted : "—"}</p>
      {showBar && (
        <div className="score-bar mt-3" aria-hidden>
          <span style={{ width: `${Math.round((metric.value as number) * 100)}%` }} />
        </div>
      )}
      <p className="mt-2 text-sm leading-relaxed text-muted">{metric.interpretation}</p>
      {research && <p className="mt-2 text-xs text-muted">{metric.description}</p>}
    </article>
  );
}
