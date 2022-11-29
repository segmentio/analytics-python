Releasing
=========

1. Update `VERSION` in `segment/analytics/version.py` to the new version.
2. Update the `HISTORY.md` for the impending release.
3. `git commit -am "Release X.Y.Z."` (where X.Y.Z is the new version)
4. `git tag -a X.Y.Z -m "Version X.Y.Z"` (where X.Y.Z is the new version).
5. `git push && git push --tags`
6. `make release`.
