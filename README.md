YogaCat Django application with web templates and Vue components on the front end.

To run front end assets for development

cd frontend

npm run dev

Notes:

- Was having a problem referencing front end assets so disabled cache busting hashes in Vite.
- Django templates are in the frontend folder so that style changes are picked up by Vite.
- Deploy script takes care of building front end assets but at the moment they don't seem to be fully minimised.
