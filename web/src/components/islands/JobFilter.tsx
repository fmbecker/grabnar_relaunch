import { useMemo, useState } from "react";
import type { JobSummary } from "@/lib/types";

interface Props {
  jobs: JobSummary[];
}

export default function JobFilter({ jobs }: Props) {
  const [location, setLocation] = useState("");
  const [type, setType] = useState("");

  const locations = useMemo(() => [...new Set(jobs.map((j) => j.location))].sort(), [jobs]);
  const types = useMemo(() => {
    const m = new Map<string, string>();
    for (const j of jobs) m.set(j.employment_type, j.employment_type_label);
    return [...m.entries()];
  }, [jobs]);

  const visible = jobs.filter((j) => (!location || j.location === location) && (!type || j.employment_type === type));

  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-3">
        <select className="field w-auto" value={location} onChange={(e) => setLocation(e.target.value)} aria-label="Arbeitsort">
          <option value="">Alle Orte</option>
          {locations.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
        <select className="field w-auto" value={type} onChange={(e) => setType(e.target.value)} aria-label="Beschäftigungsart">
          <option value="">Alle Beschäftigungsarten</option>
          {types.map(([k, label]) => (
            <option key={k} value={k}>
              {label}
            </option>
          ))}
        </select>
      </div>
      {visible.length === 0 ? (
        <p className="text-ink-700">Keine Stellen für diese Auswahl.</p>
      ) : (
        <ul className="grid gap-4">
          {visible.map((j) => (
            <li key={j.id}>
              <a href={j.href} className="flex items-center justify-between rounded-lg border border-ink-100 bg-white p-5 hover:border-brand-300">
                <div>
                  <h3 className="h3">{j.title}</h3>
                  <p className="mt-1 text-sm text-ink-500">
                    {j.location} · {j.employment_type_label} · {j.start_date}
                  </p>
                </div>
                <span aria-hidden="true" className="text-brand-600">
                  →
                </span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
