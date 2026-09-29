Releasing
=========

Publishing happens in CI through PyPI Trusted Publishing (OIDC). There is no PyPI token
to hold locally.

1. Update `VERSION` in `segment/analytics/version.py`. This is the only place the
   version lives — hatchling reads it at build time, and the publish workflow validates
   the release tag against it.
2. In `HISTORY.md`, change the `Unreleased` heading to `X.Y.Z / YYYY-M-D`.
3. `git commit -am "Release X.Y.Z."`
4. Open a PR and merge it to `master`.
5. Tag the merged commit — no `v` prefix:

   ```
   git tag X.Y.Z && git push origin X.Y.Z
   ```

6. Create a **GitHub Release** for that tag. The workflow triggers on
   `release: published`; pushing the tag by itself does not start it.
7. Approve the `production` environment when the publish job requests review.

The workflow runs the test matrix, builds with `uv`, and uploads with twine, which
performs the OIDC exchange itself — no flag is needed.

> **Note:** the workflow runs from the *tagged* commit. If it needs fixing, the tag has
> to be recreated after the fix lands; merging to `master` alone changes nothing for a
> release that is already tagged.
