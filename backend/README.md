# Backend

Each module under `modules/` may import another module only through that module's `public.py`.
Never import another module's models, services or tasks; Import Linter fails `pnpm check` if you do.
