from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from website.content_pipeline import (
  apply_generated_content,
  get_active_content_schema,
  mark_job_applied,
  mark_job_failed,
  mark_job_generated,
  sync_default_content_schema,
)
from website.models import ContentGenerationJob, ContentSchema
from website.openai_content_generator import generate_content_with_openai


class Command(BaseCommand):
  help = "Generate schema-valid brochure-site content with OpenAI Structured Outputs."

  def add_arguments(self, parser):
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--job-id", type=int, help="Existing ContentGenerationJob ID to run.")
    source.add_argument("--brief-file", help="Path to a plain-text site brief. Creates a ContentGenerationJob.")
    parser.add_argument("--name", default="Generated brochure site", help="Job name when using --brief-file.")
    parser.add_argument("--model", help="OpenAI model override.")
    parser.add_argument("--schema-id", type=int, help="ContentSchema ID override.")
    parser.add_argument("--sync-schema", action="store_true", help="Sync the default brochure JSON schema into the DB and exit.")
    parser.add_argument("--apply", action="store_true", help="Apply generated content to draft pages after generation.")
    parser.add_argument("--no-replace-sections", action="store_true", help="Do not replace existing sections when applying.")
    parser.add_argument("--no-replace-navigation", action="store_true", help="Do not replace navigation when applying.")

  def handle(self, *args, **options):
    if options["sync_schema"]:
      schema = sync_default_content_schema()
      self.stdout.write(self.style.SUCCESS(f"Synced content schema: {schema}"))
      return

    job = self.get_or_create_job(options)
    content_schema = self.resolve_schema(job, options.get("schema_id"))
    job.content_schema = content_schema
    if options.get("model"):
      job.model = options["model"]
    job.save(update_fields=["content_schema", "model", "updated_at"])

    try:
      generated_content = generate_content_with_openai(job, content_schema)
      mark_job_generated(job, generated_content)

      self.stdout.write(self.style.SUCCESS(f"Generated structured content for job {job.id}: {job.name}"))

      if options["apply"]:
        summary = apply_generated_content(
          generated_content,
          replace_sections=not options["no_replace_sections"] and job.replace_existing_sections,
          replace_navigation=not options["no_replace_navigation"] and job.replace_navigation,
          force_draft=True,
        )
        mark_job_applied(job)
        self.stdout.write(self.style.SUCCESS("Applied generated content to draft pages."))
        self.write_summary(summary)
      else:
        self.stdout.write("Generated JSON is stored on the job. Review it in admin or apply it later.")

    except Exception as exc:
      mark_job_failed(job, str(exc))
      raise

  def get_or_create_job(self, options):
    if options.get("job_id"):
      try:
        return ContentGenerationJob.objects.get(pk=options["job_id"])
      except ContentGenerationJob.DoesNotExist as exc:
        raise CommandError(f"ContentGenerationJob not found: {options['job_id']}") from exc

    brief_file = options.get("brief_file")
    if not brief_file:
      raise CommandError("Use --job-id, --brief-file, or --sync-schema.")

    path = Path(brief_file)
    if not path.exists():
      raise CommandError(f"Brief file not found: {path}")

    return ContentGenerationJob.objects.create(
      name=options["name"],
      brief=path.read_text(encoding="utf-8"),
      model=options.get("model") or ContentGenerationJob._meta.get_field("model").default,
    )

  def resolve_schema(self, job, schema_id):
    if schema_id:
      try:
        return ContentSchema.objects.get(pk=schema_id)
      except ContentSchema.DoesNotExist as exc:
        raise CommandError(f"ContentSchema not found: {schema_id}") from exc
    return job.content_schema or get_active_content_schema()

  def write_summary(self, summary):
    self.stdout.write("Apply summary:")
    for key, value in summary.items():
      self.stdout.write(f"  {key}: {value}")
