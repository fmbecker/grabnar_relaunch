import { useCallback, useEffect, useId, useMemo, useState } from "react";
import type { JobSummary } from "@/lib/types";
import { EVENT, track, umami } from "@/lib/analytics";

interface Props {
  jobs: JobSummary[];
}

/** Query parameters the selection is kept in, so a filtered list can be linked and shared. */
const PARAM = { location: "ort", type: "art" } as const;

type Filter = { location: string; type: string };

export default function JobFilter({ jobs }: Props) {
  const uid = useId();
  const [filter, setFilter] = useState<Filter>({ location: "", type: "" });
  // The live region stays empty until the visitor filters, so hydration announces nothing.
  const [announce, setAnnounce] = useState(false);

  const locations = useMemo(() => [...new Set(jobs.map((j) => j.location))].sort(), [jobs]);
  const types = useMemo(() => {
    const m = new Map<string, string>();
    for (const j of jobs) m.set(j.employment_type, j.employment_type_label);
    return [...m.entries()];
  }, [jobs]);

  // A value that no job has is dropped: a stale or hand-edited link must not leave the
  // select showing a choice that filters everything away.
  const fromUrl = useCallback((): Filter => {
    const p = new URLSearchParams(window.location.search);
    const location = p.get(PARAM.location) ?? "";
    const type = p.get(PARAM.type) ?? "";
    return {
      location: locations.includes(location) ? location : "",
      type: types.some(([k]) => k === type) ? type : "",
    };
  }, [locations, types]);

  // The page is static, so the URL is only known in the browser: start unfiltered and take
  // the selection over once hydrated. popstate makes the back button step through filters.
  useEffect(() => {
    const apply = () => setFilter(fromUrl());
    apply();
    window.addEventListener("popstate", apply);
    return () => window.removeEventListener("popstate", apply);
  }, [fromUrl]);

  function change(field: keyof Filter, value: string) {
    const next = { ...filter, [field]: value };
    setFilter(next);
    setAnnounce(true);

    const params = new URLSearchParams(window.location.search);
    for (const key of ["location", "type"] as const) {
      if (next[key]) params.set(PARAM[key], next[key]);
      else params.delete(PARAM[key]);
    }
    const query = params.toString();
    const url = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
    // One history entry per choice, so the back button undoes the last filter step.
    history.pushState(null, "", url);

    track(EVENT.jobFilter, { field: field === "location" ? "location" : "employment_type", value: value || "alle" });
  }

  const visible = jobs.filter((j) => (!filter.location || j.location === filter.location) && (!filter.type || j.employment_type === filter.type));

  return (
    <div>
      <search>
        <div className="mb-6 flex flex-wrap gap-4">
          <div>
            <label className="label" htmlFor={`${uid}-location`}>
              Arbeitsort
            </label>
            <select id={`${uid}-location`} className="field w-auto" value={filter.location} onChange={(e) => change("location", e.target.value)}>
              <option value="">Alle Orte</option>
              {locations.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor={`${uid}-type`}>
              Beschäftigungsart
            </label>
            <select id={`${uid}-type`} className="field w-auto" value={filter.type} onChange={(e) => change("type", e.target.value)}>
              <option value="">Alle Beschäftigungsarten</option>
              {types.map(([k, label]) => (
                <option key={k} value={k}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </search>

      <p role="status" className="sr-only">
        {announce ? `${visible.length} von ${jobs.length} Stellen entsprechen der Auswahl.` : ""}
      </p>

      {visible.length === 0 ? (
        <p className="text-ink-700">Keine Stellen für diese Auswahl.</p>
      ) : (
        <ul className="border-t-4 border-brand-500">
          {visible.map((j) => (
            <li key={j.id}>
              <a href={j.href} {...umami(EVENT.jobOpen, { job: j.title })} className="group flex items-center justify-between gap-6 border-b border-ink-100 bg-white px-1 py-6 hover:bg-brand-50 sm:px-4">
                <div>
                  <h3 className="h3 group-hover:text-brand-700">{j.title}</h3>
                  <p className="mt-2 text-ink-700">
                    {j.location} · {j.employment_type_label} · {j.start_date}
                  </p>
                </div>
                <span aria-hidden="true" className="grid h-11 w-11 shrink-0 place-items-center bg-brand-500 text-xl text-white">
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
