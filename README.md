Reusable Django brochure-site framework with Django admin content management, Tailwind CSS, DaisyUI, and OpenAI Structured Outputs for draft content generation.

CMS structure:

- `Page` controls slug, template choice, publishing, SEO, and page-level display options.
- `PageSection` controls ordered modular content blocks for each page.
- `SectionItem` powers repeatable cards, benefits, FAQs, testimonials, galleries, and link cards.
- `SiteSettings` controls global site name, logo URL, contact details, social links, default SEO, and navigation items.
- `CallToAction` provides reusable CTA snippets.
- `ContentSchema` stores the active OpenAI JSON Schema used for schema-constrained generation.
- `ContentGenerationJob` stores a client brief, generated structured JSON, and apply status.

Initial page templates:

- Homepage
- Standard page
- Service / landing page
- Simple text page
- Contact / CTA page

Initial section types:

- Hero
- Rich text
- Card grid
- Icon / benefit list
- CTA block
- Testimonial block
- FAQ block
- Quote block
- Link cards / child page cards
- Image + text split
- Simple gallery / image block

OpenAI structured content pipeline:

1. Sync the active content schema into the database.
2. Create a `ContentGenerationJob` in Django admin with the client/site brief.
3. Run the generation command with `OPENAI_API_KEY` set.
4. Apply generated JSON into draft `Page`, `PageSection`, `SectionItem`, navigation, settings, and CTA records.
5. Review/edit the draft pages in Django admin.
6. Publish pages when approved.

```bash
python3 manage.py generate_site_content --sync-schema
OPENAI_API_KEY=... python3 manage.py generate_site_content --job-id 1 --apply
```

You can also create a generation job from a text brief:

```bash
OPENAI_API_KEY=... python3 manage.py generate_site_content --brief-file briefs/yoga-site.txt --name "YogaCat draft" --apply
```

Generated CMS pages are forced to drafts by default. The OpenAI schema explicitly asks for structured plain-text fields and section/item records, not raw HTML.

To run front end assets for development

cd frontend

npm run dev

Notes:

- Was having a problem referencing front end assets so disabled cache busting hashes in Vite.
- Django templates are in the frontend folder so that style changes are picked up by Vite.
- Deploy script takes care of building front end assets but at the moment they don't seem to be fully minimised.
