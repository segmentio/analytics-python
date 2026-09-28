Releasing
=========

Publishing happens in CI through PyPI Trusted Publishing (OIDC). There is no
PyPI token to hold locally, and `make release` is not the release path — it
uploads with a stored credential and skips provenance.

1. Update the version in **both** `pyproject.toml` and
   `segment/analytics/version.py`. The publish workflow validates the release
   tag against `pyproject.toml` and fails if the two disagree.
2. Update `HISTORY.md`.
3. `git commit -am "Release X.Y.Z."` (where X.Y.Z is the new version)
4. Open a PR and merge it to `master`.
5. Tag the merged commit and push it:
   `git tag -a X.Y.Z -m "Version X.Y.Z" && git push --tags`
6. Create a **GitHub Release** for that tag. The workflow triggers on
   `release: published`; pushing the tag by itself does not start it.

The workflow then runs the test matrix, builds with `uv`, and uploads to PyPI
with `--trusted-publishing=always`.
