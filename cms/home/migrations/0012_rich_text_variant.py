"""Rewrites the stored rich text blocks for the StructBlock.

The block used to be a bare RichTextBlock, so its value was the HTML string itself. Now it is a
StructBlock with the text and the chosen surface, and the value has to be an object. Wagtail
would not read the old form: a string where a dict is expected renders as an empty block.

Both places have to be rewritten, the live pages and every revision - the revisions because the
editing area loads the latest one, not the live value, so an unconverted revision would wipe the
text the moment someone opens the page. The pages of all three apps are handled here in one
migration so the pass over the shared revision table happens exactly once.

The variant is "plain" everywhere, which is what every block looked like before the choice
existed; nothing changes visually until an editor switches one over.
"""

import json

from django.db import migrations

PAGE_MODELS = [
    ("home", "HomePage"),
    ("home", "StandardPage"),
    ("jobs", "JobIndexPage"),
    ("services", "ServiceIndexPage"),
    ("services", "ServicePage"),
]


def _rewrite(stream, to_struct):
    """Converts the rich text blocks in one parsed body. Returns True if anything changed."""
    changed = False
    for block in stream:
        if not isinstance(block, dict) or block.get("type") != "rich_text":
            continue
        value = block.get("value")
        if to_struct and isinstance(value, str):
            block["value"] = {"text": value, "variant": "plain"}
            changed = True
        elif not to_struct and isinstance(value, dict):
            block["value"] = value.get("text", "")
            changed = True
    return changed


def _migrate(apps, schema_editor, to_struct):
    # Raw SQL for the pages, deliberately: through the ORM the StreamField hands out a
    # deserialised StreamValue built from the CURRENT block definition, and the point here is
    # the stored JSON, not what today's blocks make of it.
    with schema_editor.connection.cursor() as cursor:
        for app_label, model_name in PAGE_MODELS:
            meta = apps.get_model(app_label, model_name)._meta
            table, pk_column = meta.db_table, meta.pk.column
            cursor.execute(f'SELECT "{pk_column}", "body" FROM "{table}"')  # noqa: S608
            rows = cursor.fetchall()
            for pk, body in rows:
                if not body:
                    continue
                stream = json.loads(body)
                if _rewrite(stream, to_struct):
                    cursor.execute(  # noqa: S608
                        f'UPDATE "{table}" SET "body" = %s WHERE "{pk_column}" = %s',
                        [json.dumps(stream), pk],
                    )

    # Revisions keep the whole page as a dict, with the body as a JSON string inside it.
    revision = apps.get_model("wagtailcore", "Revision")
    for rev in revision.objects.iterator():
        content = rev.content
        if not isinstance(content, dict) or not isinstance(content.get("body"), str):
            continue
        try:
            stream = json.loads(content["body"])
        except (TypeError, ValueError):
            continue
        if isinstance(stream, list) and _rewrite(stream, to_struct):
            content["body"] = json.dumps(stream)
            revision.objects.filter(pk=rev.pk).update(content=content)


def forwards(apps, schema_editor):
    _migrate(apps, schema_editor, to_struct=True)


def backwards(apps, schema_editor):
    _migrate(apps, schema_editor, to_struct=False)


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0011_alter_homepage_body_alter_standardpage_body"),
        ("jobs", "0010_alter_jobindexpage_body"),
        ("services", "0010_alter_serviceindexpage_body_alter_servicepage_body"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
