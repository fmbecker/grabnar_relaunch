import type { ContactSettings, JobPageData } from "./types";

export function localBusiness(c: ContactSettings, site: string) {
  return {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    name: c.company_name,
    url: site,
    telephone: c.phone,
    email: c.email,
    address: { "@type": "PostalAddress", streetAddress: c.street, postalCode: c.postal_code, addressLocality: c.city, addressCountry: "DE" },
    ...(c.latitude && c.longitude ? { geo: { "@type": "GeoCoordinates", latitude: c.latitude, longitude: c.longitude } } : {}),
    areaServed: c.service_area || undefined,
  };
}

const EMPLOYMENT: Record<string, string> = {
  FULL_TIME: "FULL_TIME", PART_TIME: "PART_TIME", MINI_JOB: "PART_TIME", TEMPORARY: "TEMPORARY", APPRENTICE: "INTERN",
};

export function jobPosting(job: JobPageData, c: ContactSettings, site: string, path: string) {
  return {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    title: job.title,
    description: `<p>${job.teaser}</p>${job.tasks}${job.requirements}${job.benefits}`,
    datePosted: job.first_published_at?.slice(0, 10),
    validThrough: job.valid_through ?? undefined,
    employmentType: EMPLOYMENT[job.employment_type] ?? "FULL_TIME",
    url: new URL(path, site).toString(),
    hiringOrganization: { "@type": "Organization", name: c.company_name, sameAs: site },
    jobLocation: {
      "@type": "Place",
      address: { "@type": "PostalAddress", addressLocality: job.location, addressRegion: "Baden-Württemberg", addressCountry: "DE" },
    },
  };
}
