import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { EVENT, SERVICE_PARAM, track } from "@/lib/analytics";

interface Props {
  variant: "contact" | "application";
  successMessage: string;
  sourcePath: string;
  apiUrl: string;
  job?: { id: number; title: string };
}

type Status = "idle" | "sending" | "success" | "error";

export default function ContactForm({ variant, successMessage, sourcePath, apiUrl, job }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const startedAt = useRef(Date.now());
  const started = useRef(false);
  const uid = useId();
  const isApplication = variant === "application";
  // Service handed over by a CTA link (?leistung=…). Prefills the field; tracked as is,
  // because it comes from our own link and not from what the visitor typed.
  const [service, setService] = useState("");
  useEffect(() => {
    if (variant !== "contact") return;
    const fromLink = new URLSearchParams(window.location.search).get(SERVICE_PARAM)?.slice(0, 120) ?? "";
    setService(fromLink);
  }, [variant]);

  // Tracking: form type, job title and the linked service only, never what visitors type.
  const trackData = { form: variant, job: job?.title };
  function onFirstInput() {
    if (started.current) return;
    started.current = true;
    track(EVENT.formStart, trackData);
  }

  const endpoint = `${apiUrl.replace(/\/$/, "")}/${isApplication ? "application" : "contact"}/`;

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("sending");
    setErrors({});
    const form = e.currentTarget;
    const data = new FormData(form);
    data.set("started_at", String(startedAt.current));
    data.set("source_path", sourcePath);
    data.set("consent", data.get("consent") ? "true" : "false");
    if (job) {
      data.set("job_title", job.title);
      data.set("job_page_id", String(job.id));
    }
    try {
      const res = await fetch(endpoint, { method: "POST", body: data });
      const json = (await res.json()) as { ok: boolean; errors?: Record<string, string[]> };
      if (res.ok && json.ok) {
        setStatus("success");
        form.reset();
        if (isApplication) track(EVENT.applicationSent, { job: job?.title });
        else track(EVENT.inquirySent, { service });
        track(EVENT.lead, { channel: isApplication ? "application" : "form", service: isApplication ? undefined : service });
      } else {
        setErrors(json.errors ?? {});
        setStatus("error");
        track(EVENT.formError, { ...trackData, reason: json.errors ? "invalid" : "error", fields: Object.keys(json.errors ?? {}).join(",") });
      }
    } catch {
      setStatus("error");
      track(EVENT.formError, { ...trackData, reason: "error" });
    }
  }

  if (status === "success") {
    return (
      <p role="status" className="rounded-md bg-green-50 p-4 text-green-800">
        {successMessage}
      </p>
    );
  }

  const err = (k: string) => errors[k]?.[0];
  // `remountKey` re-creates the uncontrolled input when its default value arrives after hydration.
  const field = (name: string, label: string, props: React.InputHTMLAttributes<HTMLInputElement> = {}, remountKey?: string) => (
    <div>
      <label className="label" htmlFor={`${uid}-${name}`}>
        {label}
        {props.required && " *"}
      </label>
      <input key={remountKey} id={`${uid}-${name}`} name={name} className="field" {...props} />
      {err(name) && <p className="mt-1 text-sm text-red-700">{err(name)}</p>}
    </div>
  );

  return (
    <form onSubmit={onSubmit} onInput={onFirstInput} className="grid gap-5" noValidate={false}>
      {/* honeypot */}
      <div className="hidden" aria-hidden="true">
        <label htmlFor={`${uid}-website`}>Website</label>
        <input id={`${uid}-website`} name="website" type="text" tabIndex={-1} autoComplete="off" />
      </div>

      {job && (
        <p className="rounded-md bg-brand-50 p-3 text-sm">
          Bewerbung für: <strong>{job.title}</strong>
        </p>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        {field("name", "Name", { type: "text", required: true, autoComplete: "name" })}
        {field("email", "E-Mail", { type: "email", required: true, autoComplete: "email" })}
        {field("phone", "Telefon", { type: "tel", autoComplete: "tel" })}
        {isApplication
          ? !job && field("job_title", "Gewünschte Stelle", { type: "text" })
          : field("company", "Firma", { type: "text", autoComplete: "organization" })}
      </div>

      {!isApplication && field("service", "Gewünschte Leistung", { type: "text", placeholder: "z. B. Unterhaltsreinigung Bürogebäude", defaultValue: service }, service)}

      <div>
        <label className="label" htmlFor={`${uid}-message`}>
          {isApplication ? "Kurze Nachricht" : "Ihre Anfrage *"}
        </label>
        <textarea id={`${uid}-message`} name="message" rows={5} className="field" required={!isApplication} />
        {err("message") && <p className="mt-1 text-sm text-red-700">{err("message")}</p>}
      </div>

      {isApplication && (
        <div>
          <label className="label" htmlFor={`${uid}-cv`}>
            Lebenslauf (PDF oder Word, max. 10 MB)
          </label>
          <input id={`${uid}-cv`} name="cv" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" className="field" />
          {err("cv") && <p className="mt-1 text-sm text-red-700">{err("cv")}</p>}
        </div>
      )}

      <label className="flex items-start gap-3 text-sm text-ink-700">
        <input type="checkbox" name="consent" value="true" required className="mt-1" />
        <span>
          Ich habe die <a href="/datenschutz/" className="underline">Datenschutzerklärung</a> gelesen und stimme der Verarbeitung meiner Angaben zur Bearbeitung meiner {isApplication ? "Bewerbung" : "Anfrage"} zu. *
        </span>
      </label>
      {err("consent") && <p className="-mt-3 text-sm text-red-700">{err("consent")}</p>}

      {status === "error" && Object.keys(errors).length === 0 && (
        <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800">
          Das Senden hat nicht geklappt. Bitte versuchen Sie es erneut oder rufen Sie uns an.
        </p>
      )}

      <button type="submit" className="btn-primary justify-self-start" disabled={status === "sending"}>
        {status === "sending" ? "Wird gesendet …" : isApplication ? "Bewerbung absenden" : "Anfrage absenden"}
      </button>
    </form>
  );
}
