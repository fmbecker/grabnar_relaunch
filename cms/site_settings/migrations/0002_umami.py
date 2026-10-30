from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("site_settings", "0001_initial")]

    operations = [
        migrations.RenameField("sitesettings", "analytics_site_id", "analytics_website_id"),
        migrations.AlterField(
            model_name="sitesettings",
            name="analytics_website_id",
            field=models.CharField(
                blank=True,
                help_text="UUID aus Umami → Einstellungen → Websites.",
                max_length=64,
                verbose_name="Umami-Website-ID",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="analytics_script_url",
            field=models.URLField(
                blank=True,
                help_text="z. B. https://statistik.grabnar.de/script.js – leer lassen = kein Tracking.",
                verbose_name="Umami-Script-URL",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="analytics_host_url",
            field=models.URLField(
                blank=True,
                help_text="Nur nötig, wenn Daten an eine andere Adresse gehen als das Script.",
                verbose_name="Umami-Host-URL (optional)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="analytics_domains",
            field=models.CharField(
                blank=True,
                default="www.grabnar.de,grabnar.de",
                help_text="Kommagetrennt. Verhindert Zählungen von Staging und lokalen Builds.",
                max_length=255,
                verbose_name="Nur auf diesen Domains zählen",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="analytics_performance",
            field=models.BooleanField(default=True, verbose_name="Ladezeiten (Web Vitals) erfassen"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="analytics_do_not_track",
            field=models.BooleanField(
                default=True, verbose_name="„Do Not Track“ der Besucher respektieren"
            ),
        ),
    ]
