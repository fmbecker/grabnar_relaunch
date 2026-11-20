# Domainumzug: mbg.aivii.de → www.grabnar.de

Der Relaunch läuft auf einem **neuen VPS**, nicht auf dem Linode der Altseite (dessen OS ist zu alt).
Die Domain `grabnar.de` verwaltet Felix nicht selbst. Deshalb zwei Phasen:

| | Phase 1 – Abnahme | Phase 2 – live |
|---|---|---|
| Adresse | `https://mbg.aivii.de` | `https://www.grabnar.de` (`grabnar.de` und `mbg.aivii.de` leiten dorthin) |
| Zugang | ganze Seite hinter Basic-Auth | öffentlich (Admin optional per IP/Basic-Auth) |
| Suchmaschinen | `noindex` auf jeder Seite, `X-Robots-Tag`, `robots.txt: Disallow: /` | indexierbar, Sitemap in `robots.txt` |
| Nginx | `deploy/nginx/grabnar-staging.conf` | `deploy/nginx/grabnar.conf` |
| `/srv/grabnar/web.env` | `PUBLIC_SITE_URL=https://mbg.aivii.de`, `PUBLIC_ALLOW_INDEXING=false` | `PUBLIC_SITE_URL=https://www.grabnar.de`, `PUBLIC_ALLOW_INDEXING=true` |
| `/srv/grabnar/cms.env` | Hosts/URLs mit `mbg.aivii.de` | Hosts/URLs mit `www.grabnar.de` |

## Was an der Domain hängt

Alles, was die Adresse der Seite enthält, entsteht beim **Bauen** aus `PUBLIC_SITE_URL`
(`web/src/lib/site.ts`): Canonical, `og:url`/`og:image` (`web/src/components/Seo.astro`), Sitemap
(`@astrojs/sitemap`, `web/astro.config.ts`), JSON-LD (`web/src/lib/jsonld.ts`), `robots.txt`
(`web/src/pages/robots.txt.ts`), Ziele der Alt-URL-Weiterleitungen (`web/scripts/redirects.mjs`),
Formular-Endpunkt (Vorgabe `$PUBLIC_SITE_URL/api/forms`) und die Content-Security-Policy.
Interne Links sind ohnehin nur Pfade (`pathFromHtmlUrl` in `web/src/lib/wagtail.ts`).

Indexierung muss ausdrücklich eingeschaltet werden (`PUBLIC_ALLOW_INDEXING=true`); fehlt die
Variable, ist jede Seite `noindex`. Ein Umzug der Domain ist damit: Variablen ändern, neu bauen.

Im CMS hängen an der Domain: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `WAGTAILADMIN_BASE_URL`
(Links in Mails und API), `FRONTEND_URL` (Vorschau, CORS, Betreff der Formular-Mails),
`CORS_ALLOWED_ORIGINS` – alle in `/srv/grabnar/cms.env` (Vorlage `cms/.env.example`). Dazu im
Wagtail-Admin unter *Einstellungen → Websites* der Hostname der Standard-Website (für „Live ansehen“
im Admin) und unter *Website-Einstellungen → Statistik* „Nur auf diesen Domains zählen“.

## Mails

Formular-Mails gehen mit einem **Absender unter `aivii.de`** raus (`DEFAULT_FROM_EMAIL`,
z. B. `Website Grabnar <website@aivii.de>`), über den SMTP-Zugang des Postfachs (`EMAIL_URL`).
SPF/DKIM von `aivii.de` pflegt Felix selbst; ein `@grabnar.de`-Absender vom neuen Server würde am
SPF von `grabnar.de` scheitern. Damit „Antworten“ beim Empfänger zum Kunden bzw. Bewerber geht,
setzt das CMS `Reply-To` auf die Adresse aus dem Formular (`cms/forms_api/views.py`).
Daran ändert der Domainumzug nichts.

## Phase 1 – Abnahme unter mbg.aivii.de

👤 = Felix, 🌐 = Domain-Verwalter von grabnar.de

1. 👤 DNS `mbg.aivii.de` (A/AAAA) auf den neuen VPS.
2. 👤 Server nach `deploy/README.md` einrichten; `web.env` und `cms.env` mit `mbg.aivii.de`.
3. 👤 `sudo mkdir -p /var/www/certbot`, Basic-Auth anlegen:
   `sudo htpasswd -c /etc/nginx/grabnar-staging.htpasswd grabnar`
4. 👤 Erstes Zertifikat, solange noch keine Site-Config aktiv ist (`grabnar-staging.conf` verweist
   auf das Zertifikat, `nginx -t` scheitert ohne): `sudo systemctl stop nginx`,
   `sudo certbot certonly --standalone -d mbg.aivii.de`, `sudo systemctl start nginx`.
   Für die automatische Erneuerung danach auf Webroot umstellen:
   `sudo certbot reconfigure --cert-name mbg.aivii.de --webroot -w /var/www/certbot`
   (ältere certbot-Versionen: `authenticator = webroot` und `webroot_path` in
   `/etc/letsencrypt/renewal/mbg.aivii.de.conf`).
5. 👤 `sudo ln -s /srv/grabnar/repo/deploy/nginx/grabnar-staging.conf /etc/nginx/sites-enabled/grabnar.conf`,
   `sudo nginx -t && sudo systemctl reload nginx`.
6. 👤 Prüfen: `curl -I https://mbg.aivii.de/` → `401`; mit `-u grabnar:…` → `200` und
   `X-Robots-Tag: noindex, nofollow`; Quelltext enthält `<meta name="robots" content="noindex,nofollow">`;
   `https://mbg.aivii.de/robots.txt` → `Disallow: /`.
7. 👤 Test-Mail über das Kontaktformular: kommt an, Absender `@aivii.de`, „Antworten“ geht an die
   Formular-Adresse, nicht im Spam (Mail-Header: `spf=pass`, `dkim=pass`).
8. Abnahme durch die Firma (Zugang per Basic-Auth weitergeben).

## Phase 2 – Umzug auf www.grabnar.de

**Vorab (1–2 Tage vorher)**

- 🌐 TTL der A/AAAA-Einträge von `grabnar.de` und `www.grabnar.de` auf 300 s senken.
- 🌐 MX-, Mail- und sonstige Subdomain-Einträge **nicht** ändern.
- 👤 Termin in einer ruhigen Zeit festlegen; der Umzug dauert etwa 15–30 Minuten.

**Umzug**

1. 🌐 A/AAAA von `grabnar.de` und `www.grabnar.de` auf die IP des neuen VPS.
2. 👤 Warten, bis die neue IP sichtbar ist: `dig +short www.grabnar.de @1.1.1.1`.
   Bis zum Zertifikat beantwortet `grabnar-staging.conf` HTTP für beide Namen mit 503 und lässt nur
   die Let's-Encrypt-Prüfung durch.
3. 👤 `sudo certbot certonly --webroot -w /var/www/certbot -d www.grabnar.de -d grabnar.de`
4. 👤 `/srv/grabnar/web.env`: `PUBLIC_SITE_URL=https://www.grabnar.de`, `PUBLIC_ALLOW_INDEXING=true`.
5. 👤 `/srv/grabnar/cms.env`: in `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `WAGTAILADMIN_BASE_URL`,
   `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` `mbg.aivii.de` durch `www.grabnar.de` ersetzen
   (`ALLOWED_HOSTS=www.grabnar.de,grabnar.de,localhost,127.0.0.1`), dann
   `docker compose -f /srv/grabnar/repo/deploy/docker-compose.yml --env-file /srv/grabnar/cms.env up -d`.
6. 👤 Nginx umschalten:
   `sudo ln -sfn /srv/grabnar/repo/deploy/nginx/grabnar.conf /etc/nginx/sites-enabled/grabnar.conf`
   (die Datei wird von `build-web.sh` im nächsten Schritt mit `nginx -t` geprüft und neu geladen).
7. 👤 Neu bauen: `/srv/grabnar/repo/deploy/build-web.sh` (die Ausgabe nennt Domain und Indexierung).
8. 👤 Wagtail-Admin: *Einstellungen → Websites* → Hostname `www.grabnar.de`, Port 443.
   *Website-Einstellungen → Statistik*: Domains prüfen (Vorgabe `www.grabnar.de,grabnar.de`).

**Prüfen**

- `curl -sI https://www.grabnar.de/` → `200`, ohne `X-Robots-Tag`; `https://grabnar.de/x` und
  `https://mbg.aivii.de/x` → `301` auf `https://www.grabnar.de/x`; `http://…` → `301`.
- Quelltext der Startseite: `<link rel="canonical" href="https://www.grabnar.de/">`, kein `noindex`.
- `https://www.grabnar.de/robots.txt` mit Sitemap-Zeile; `https://www.grabnar.de/sitemap-index.xml`
  enthält nur `www.grabnar.de`-URLs.
- Alt-URLs aus `docs/redirects.csv` stichprobenartig: `301` auf `https://www.grabnar.de/…`.
- Formular absenden; Betreff lautet „… über www.grabnar.de“.
- `sudo certbot renew --dry-run` für beide Zertifikate.

**Danach**

- 👤 Google Search Console: Property `https://www.grabnar.de` per HTML-Datei bestätigen (kein
  DNS-Zugriff nötig: Datei in `web/public/` ablegen, committen, bauen), Sitemap einreichen.
- 👤 404-Report in den ersten Wochen wöchentlich prüfen.
- 👤 Altserver: Mediathek und MySQL-Dump offline sichern, nach 4 Wochen abschalten
  (`docs/04-aufgaben.md`, Phase 4).
- 👤 `mbg.aivii.de` und sein Zertifikat behalten – die Weiterleitung in `grabnar.conf` braucht es.

## Zurück

Bis zum Abschalten des Altservers: 🌐 A/AAAA wieder auf die alte IP. Bei 300 s TTL ist das in
wenigen Minuten wirksam; die neue Seite bleibt unter `mbg.aivii.de` erreichbar, sobald dort wieder
`grabnar-staging.conf` und die Phase-1-Werte in `web.env`/`cms.env` stehen.
