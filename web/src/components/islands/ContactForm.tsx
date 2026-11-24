import { useEffect, useId, useRef, useState, type SyntheticEvent } from "react";
import { EVENT, SERVICE_PARAM, track } from "@/lib/analytics";

interface Props {
  variant: "contact" | "application";
  successMessage: string;
  sourcePath: string;
  apiUrl: string;
  job?: { id: number; title: string };
}

type Status = "idle" | "sending" | "success" | "error";

/**
 * Error keys that have a control of their own here, so their message is shown at the field.
 * The serializers in cms/forms_api/views.py can also reject keys that this form never shows
 * (source_path, job_page_id, and DRF's non_field_errors); those need the general message.
 */
const FIELD_KEYS = ["name", "email", "phone", "company", "job_title", "service", "message", "cv", "consent"];

/** Form controls that carry a name and a validity state. */
type Control = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

function isControl(target: EventTarget | null): target is Control {
  return (
    target instanceof HTMLInputElement ||
    target instanceof HTMLSelectElement ||
    target instanceof HTMLTextAreaElement
  );
}

export default function ContactForm({ variant, successMessage, sourcePath, apiUrl, job }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  // What the browser itself rejects, mirrored from the CSS :user-invalid state. Kept apart
  // from `errors`, which only ever holds what the server sent back.
  const [userInvalid, setUserInvalid] = useState<Record<string, boolean>>({});
  const startedAt = useRef(Date.now());
  const started = useRef(false);
  const form = useRef<HTMLFormElement>(null);
  const alert = useRef<HTMLParagraphElement>(null);
  const success = useRef<HTMLParagraphElement>(null);
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

  // The submit button vanishes with the form, so focus has to be placed on the message that
  // replaces it – otherwise it falls back to the document and the visitor loses their place.
  useEffect(() => {
    if (status === "success") success.current?.focus();
  }, [status]);

  // Tracking: form type, job title and the linked service only, never what visitors type.
  const trackData = { form: variant, job: job?.title };

  /**
   * Mirror the browser's :user-invalid state into aria-invalid. Without this, Chromium does
   * not expose an empty required field as invalid to assistive technology even after the
   * visitor has left it, while :invalid would mark every empty required field from page load.
   * Where the pseudo-class is missing (before Nov 2023) the sync is skipped: the browser's
   * own validation still blocks the submit, and the server errors below stay fully labelled.
   */
  function syncValidity(e: SyntheticEvent) {
    const el = e.target;
    if (!isControl(el) || !el.name) return;
    if (!CSS.supports("selector(:user-invalid)")) return;
    const invalid = el.matches(":user-invalid");
    setUserInvalid((prev) => (prev[el.name] === invalid ? prev : { ...prev, [el.name]: invalid }));
  }

  function onInput(e: SyntheticEvent) {
    if (!started.current) {
      started.current = true;
      track(EVENT.formStart, trackData);
    }
    syncValidity(e);
    // Typing clears this field's server error right away; a new one only ever arrives with
    // the next answer from the server. Nothing is validated while the visitor is still typing.
    const el = e.target;
    if (!isControl(el) || !el.name) return;
    const name = el.name;
    setErrors((prev) => {
      if (!prev[name]) return prev;
      const next = { ...prev };
      delete next[name];
      return next;
    });
  }

  const endpoint = `${apiUrl.replace(/\/$/, "")}/${isApplication ? "application" : "contact"}/`;

  /**
   * Put focus on the first field the server rejected, so a screen reader reads its name and
   * its message. Runs after the next paint, because the message element it points to through
   * aria-describedby is only in the page once React has rendered the new state.
   * Keys without a control of their own (source_path, job_page_id, non_field_errors) fall
   * through to the general message.
   */
  function focusFirstError(el: HTMLFormElement, fieldErrors: Record<string, string[]>) {
    requestAnimationFrame(() => {
      for (const control of Array.from(el.elements)) {
        if (isControl(control) && control.name && fieldErrors[control.name]) {
          control.focus();
          return;
        }
      }
      alert.current?.focus();
    });
  }

  async function onSubmit(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("sending");
    setErrors({});
    const el = e.currentTarget;
    const data = new FormData(el);
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
        el.reset();
        setUserInvalid({});
        if (isApplication) track(EVENT.applicationSent, { job: job?.title });
        else track(EVENT.inquirySent, { service });
        track(EVENT.lead, { channel: isApplication ? "application" : "form", service: isApplication ? undefined : service });
      } else {
        const fieldErrors = json.errors ?? {};
        setErrors(fieldErrors);
        setStatus("error");
        focusFirstError(el, fieldErrors);
        track(EVENT.formError, { ...trackData, reason: json.errors ? "invalid" : "error", fields: Object.keys(fieldErrors).join(",") });
      }
    } catch {
      setStatus("error");
      focusFirstError(el, {});
      track(EVENT.formError, { ...trackData, reason: "error" });
    }
  }

  if (status === "success") {
    return (
      <p ref={success} tabIndex={-1} role="status" className="rounded-md bg-green-50 p-4 text-green-800">
        {successMessage}
      </p>
    );
  }

  const err = (k: string) => errors[k]?.[0];
  const errorId = (k: string) => `${uid}-${k}-error`;
  // aria-invalid is always written out, "false" included: Firefox and Safari report an empty
  // required field as invalid from page load, so leaving it off announces an error too early.
  const isInvalid = (k: string) => Boolean(err(k)) || userInvalid[k] === true;
  // Only referenced while the message is on screen – aria-describedby is read out even when
  // what it points to is hidden.
  const describedBy = (k: string) => (err(k) ? errorId(k) : undefined);
  const keys = Object.keys(errors);
  const showAlert = status === "error" && (keys.length === 0 || keys.some((k) => !FIELD_KEYS.includes(k)));

  // `remountKey` re-creates the uncontrolled input when its default value arrives after hydration.
  const field = (name: string, label: string, props: React.InputHTMLAttributes<HTMLInputElement> = {}, remountKey?: string) => (
    <div>
      <label className="label" htmlFor={`${uid}-${name}`}>
        {label}
        {props.required && " *"}
      </label>
      <input
        key={remountKey}
        id={`${uid}-${name}`}
        name={name}
        className="field"
        aria-invalid={isInvalid(name)}
        aria-describedby={describedBy(name)}
        onInvalid={syncValidity}
        {...props}
      />
      {err(name) && (
        <p id={errorId(name)} className="mt-1 text-sm text-red-700">
          {err(name)}
        </p>
      )}
    </div>
  );

  return (
    <form ref={form} onSubmit={onSubmit} onInput={onInput} onBlur={syncValidity} className="grid gap-5" noValidate={false}>
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
        <textarea
          id={`${uid}-message`}
          name="message"
          rows={5}
          className="field"
          required={!isApplication}
          aria-invalid={isInvalid("message")}
          aria-describedby={describedBy("message")}
          onInvalid={syncValidity}
        />
        {err("message") && (
          <p id={errorId("message")} className="mt-1 text-sm text-red-700">
            {err("message")}
          </p>
        )}
      </div>

      {isApplication && (
        <div>
          <label className="label" htmlFor={`${uid}-cv`}>
            Lebenslauf (PDF oder Word, max. 10 MB)
          </label>
          <input
            id={`${uid}-cv`}
            name="cv"
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="field"
            aria-invalid={isInvalid("cv")}
            aria-describedby={describedBy("cv")}
            onInvalid={syncValidity}
          />
          {err("cv") && (
            <p id={errorId("cv")} className="mt-1 text-sm text-red-700">
              {err("cv")}
            </p>
          )}
        </div>
      )}

      <div>
        <label className="flex items-start gap-3 text-sm text-ink-700">
          <input
            type="checkbox"
            name="consent"
            value="true"
            required
            className="mt-1"
            aria-invalid={isInvalid("consent")}
            aria-describedby={describedBy("consent")}
            onInvalid={syncValidity}
          />
          <span>
            Ich habe die <a href="/datenschutz/" className="underline">Datenschutzerklärung</a> gelesen und stimme der Verarbeitung meiner Angaben zur Bearbeitung meiner {isApplication ? "Bewerbung" : "Anfrage"} zu. *
          </span>
        </label>
        {err("consent") && (
          <p id={errorId("consent")} className="mt-1 text-sm text-red-700">
            {err("consent")}
          </p>
        )}
      </div>

      {/* Shown whenever something went wrong that no field explains, and then the target of
          focusFirstError. Never `hidden`: a hidden element cannot take focus. */}
      {showAlert && (
        <p ref={alert} tabIndex={-1} role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800">
          Das Senden hat nicht geklappt. Bitte versuchen Sie es erneut oder rufen Sie uns an.
        </p>
      )}

      <button type="submit" className="btn-primary justify-self-start" disabled={status === "sending"}>
        {status === "sending" ? "Wird gesendet …" : isApplication ? "Bewerbung absenden" : "Anfrage absenden"}
      </button>
    </form>
  );
}
