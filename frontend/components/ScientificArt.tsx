type ArtProps = { className?: string; title?: string };

const stroke = "#2F8B91";
const fill = "#71C9CE";
const soft = "#A6E3E9";
const warm = "#C45C26";

export function DecorativeNetwork({ className = "" }: ArtProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 720 220"
      aria-hidden
      role="presentation"
    >
      <g className="deco-line" fill="none" stroke={stroke} strokeWidth="1" opacity="0.22">
        <line x1="40" y1="140" x2="120" y2="70" />
        <line x1="120" y1="70" x2="220" y2="110" />
        <line x1="220" y1="110" x2="310" y2="50" />
        <line x1="220" y1="110" x2="280" y2="170" />
        <line x1="310" y1="50" x2="420" y2="80" />
        <line x1="280" y1="170" x2="420" y2="80" />
        <line x1="420" y1="80" x2="530" y2="140" />
        <line x1="530" y1="140" x2="640" y2="70" />
        <line x1="530" y1="140" x2="680" y2="180" />
      </g>
      <g fill={fill} opacity="0.28">
        <circle cx="40" cy="140" r="4" />
        <circle cx="120" cy="70" r="5" />
        <circle cx="220" cy="110" r="6" />
        <circle cx="310" cy="50" r="4" />
        <circle cx="280" cy="170" r="4" />
        <circle cx="420" cy="80" r="5" />
        <circle cx="530" cy="140" r="5" />
        <circle cx="640" cy="70" r="4" />
        <circle cx="680" cy="180" r="3" />
      </g>
    </svg>
  );
}

export function ProteinMachine({ className = "h-20 w-20" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 80 80" aria-hidden>
      <title>Decorative protein illustration — not measured data</title>
      <ellipse cx="40" cy="40" rx="22" ry="14" fill={soft} stroke={stroke} strokeWidth="1.5" transform="rotate(-20 40 40)" />
      <ellipse cx="40" cy="40" rx="22" ry="14" fill="none" stroke={fill} strokeWidth="1.5" transform="rotate(25 40 40)" />
      <circle cx="40" cy="40" r="5" fill={fill} />
    </svg>
  );
}

export function InteractionPair({ className = "h-20 w-28" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 120 64" aria-hidden>
      <title>Decorative protein interaction — not a measured edge</title>
      <line x1="28" y1="32" x2="92" y2="32" stroke={stroke} strokeWidth="2" />
      <circle cx="28" cy="32" r="10" fill={fill} />
      <circle cx="92" cy="32" r="10" fill={fill} />
    </svg>
  );
}

export function DiseaseCluster({ className = "h-20 w-28" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 120 72" aria-hidden>
      <title>Decorative disease-associated cluster — not a measured pathway</title>
      <line x1="36" y1="40" x2="60" y2="22" stroke={stroke} strokeWidth="1.6" />
      <line x1="60" y1="22" x2="86" y2="40" stroke={stroke} strokeWidth="1.6" />
      <line x1="36" y1="40" x2="86" y2="40" stroke={stroke} strokeWidth="1.6" />
      <line x1="60" y1="22" x2="60" y2="54" stroke={stroke} strokeWidth="1.6" />
      <circle cx="36" cy="40" r="7" fill={fill} />
      <circle cx="60" cy="22" r="7" fill={fill} />
      <circle cx="86" cy="40" r="7" fill={fill} />
      <circle cx="60" cy="54" r="7" fill={fill} />
    </svg>
  );
}

export function CandidateHighlight({ className = "h-20 w-28" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 120 72" aria-hidden>
      <title>Decorative candidate ranking — not a prediction result</title>
      <line x1="30" y1="36" x2="58" y2="24" stroke={stroke} strokeWidth="1.6" />
      <line x1="58" y1="24" x2="86" y2="38" stroke={stroke} strokeWidth="1.6" />
      <line x1="86" y1="38" x2="64" y2="56" stroke={stroke} strokeWidth="1.6" opacity="0.5" strokeDasharray="3 3" />
      <circle cx="30" cy="36" r="7" fill={fill} />
      <circle cx="58" cy="24" r="7" fill={fill} />
      <circle cx="86" cy="38" r="7" fill={fill} />
      <circle cx="64" cy="56" r="8" fill={warm} />
    </svg>
  );
}

export function GraphletMotif({ className = "h-20 w-24" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 80 64" aria-hidden>
      <title>Decorative graphlet motif — educational shape only</title>
      <line x1="16" y1="44" x2="40" y2="14" stroke={stroke} strokeWidth="2" />
      <line x1="40" y1="14" x2="64" y2="44" stroke={stroke} strokeWidth="2" />
      <line x1="16" y1="44" x2="64" y2="44" stroke={stroke} strokeWidth="2" />
      <circle cx="16" cy="44" r="6" fill={fill} />
      <circle cx="40" cy="14" r="6" fill={soft} />
      <circle cx="64" cy="44" r="6" fill={fill} />
    </svg>
  );
}

export function PipelineStrip() {
  const steps = [
    "Disease",
    "Protein interactions",
    "Disease network",
    "Prediction methods",
    "Combined ranking",
    "Network patterns",
    "Candidate proteins",
  ];
  return (
    <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-7">
      {steps.map((step, i) => (
        <li key={step} className="panel relative flex min-h-[92px] flex-col justify-between p-3">
          <span className="font-tech text-[11px] text-muted">{String(i + 1).padStart(2, "0")}</span>
          <span className="mt-2 text-sm font-medium leading-snug">{step}</span>
          {i < steps.length - 1 && (
            <span className="absolute -right-1 top-1/2 hidden text-accent lg:block" aria-hidden>
              →
            </span>
          )}
        </li>
      ))}
    </ol>
  );
}

export function IconHome({ className = "h-3.5 w-3.5" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M2.5 7.5 8 2.5l5.5 5V13a.5.5 0 0 1-.5.5H3a.5.5 0 0 1-.5-.5V7.5Z" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

export function IconDisease({ className = "h-3.5 w-3.5" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <circle cx="8" cy="8" r="5.2" stroke="currentColor" strokeWidth="1.3" />
      <circle cx="8" cy="8" r="1.6" fill="currentColor" />
    </svg>
  );
}

export function IconModels({ className = "h-3.5 w-3.5" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <rect x="2.5" y="8" width="3" height="5" stroke="currentColor" strokeWidth="1.3" />
      <rect x="6.5" y="5" width="3" height="8" stroke="currentColor" strokeWidth="1.3" />
      <rect x="10.5" y="3" width="3" height="10" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

export function IconGraphlets({ className = "h-3.5 w-3.5" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <circle cx="4" cy="11" r="1.6" fill="currentColor" />
      <circle cx="8" cy="4.5" r="1.6" fill="currentColor" />
      <circle cx="12" cy="11" r="1.6" fill="currentColor" />
      <path d="M4.6 10.2 7.4 5.6m1.3 0 2.7 4.6M5.4 11h5.2" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

export function IconMethod({ className = "h-3.5 w-3.5" }: ArtProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M3 4.5h10M3 8h10M3 11.5h7" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}
