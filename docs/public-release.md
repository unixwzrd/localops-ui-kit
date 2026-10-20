# Public release preparation

The project uses separate development and public Git histories. The private development checkout retains local coordination and historical evidence; the public repository receives only reviewed source snapshots and subsequent public changes. Package publication and consumer adoption remain separate decisions.

## Privacy gate

`docs/consumer-handoffs/` contains private local coordination. It is ignored in the shared `.gitignore`, not merely one developer's `.git/info/exclude`. Historical handoffs and a pre-public compatibility snapshot are retained in the private development workspace. Public checkouts intentionally contain neither these files nor their private qualification evidence.

**Deleting or ignoring a file does not remove it from Git history.** The chosen boundary is a fresh public history, not a force-push rewrite of private history. The former remote and its issues, merged dependency PR and Actions logs remain private. The canonical public repository is a new repository, not a fork. Never merge, mirror-push or otherwise import private Git ancestry into it. Normal merges between reviewed public branches are fine; promotion from private development is a reviewed file change, not a Git-history merge.

Run `python scripts/check_publication.py` to check the current candidate paths and public text. Run `python scripts/check_publication.py --history` to additionally check historical handoff paths. That history check must pass in the public checkout and may fail as expected in the historical development repository. This is a focused guard, not a comprehensive secret scanner. Review diffs, GitHub refs, PRs, release attachments, workflow artifacts and author identities separately. Ignored files are not access-controlled: never serve the repository root publicly or upload the full checkout as a Pages artifact.

The fresh public source identity differs from private historical commits. Preserve exact qualified wheels, hashes and private history; coordinate any new public Git pin with consumers rather than silently replacing their revision. An unchanged browser resource hash is useful compatibility evidence, not a claim of consumer adoption. The public Git remote is stable for future public commits; obsolete private commit IDs are not fetchable there.

## Development-to-public workflow

1. Work in the development checkout; keep agent conversations and consumer evidence in its ignored private handoff directory. Run tests and commit the reviewed code before export.
2. Run `python scripts/export_public.py ../public-candidate`. The destination must not already exist. The exporter requires a clean development worktree, validates current public text and copies tracked source through an approved path list. It refuses private coordination, generated files, symlinks and Git metadata. New top-level public surfaces require an explicit allowlist review.
3. For the first publication only, initialize a new repository in that snapshot with a public-safe author email. Do not copy `.git` or create a fork from the private repository. For later promotions, review the snapshot against the existing public checkout and apply only intended file additions/changes/deletions there; keep its existing public history.
4. Run the full validation suite and `check_publication.py --history` in the public checkout. Review `git diff --cached`, including dependency pins and author metadata, before committing/pushing a public branch.
5. Qualify public pull requests in the public repository. Bring accepted fixes back into development as reviewed changes, preserving upstream attribution as appropriate; never merge development ancestry in the opposite direction. Keep private-to-public commit/artifact mapping in the private ledger, not public release notes.

The exporter never commits, pushes, changes visibility, deletes old files or replaces an existing checkout. It is a boundary helper, not an unattended publishing service.

## Static demonstration

The showcase is a real browser UI, not screenshots. All data, path callbacks, task commands and preferences are synthetic and in memory. It performs no filesystem or process operation. Browser clipboard access requires HTTPS or localhost and permission. Direct ES modules require HTTP(S), not opening HTML with `file://`.

```bash
python scripts/build_showcase.py
python -m http.server 8765 --bind 127.0.0.1 --directory _site
```

Open `http://127.0.0.1:8765/`. Assembly copies an explicit set of showcase files and the asset manifest's canonical modules into `_site/`, preserving paths and bytes. It never copies handoffs, compatibility evidence, Python services, negative controls or the Git checkout. Existing output is not overwritten: use a fresh `--output` directory for subsequent builds or inspect and remove the old generated directory yourself.

The manual `.github/workflows/pages.yml` builds and uploads only that allowlisted directory. It fetches full history and refuses deployment while historical handoffs remain. After the privacy gate and source review, the maintainer can choose **Settings → Pages → GitHub Actions**, then run **Static widget showcase**. There is no automatic deployment on push. The expected project URL is `https://unixwzrd.github.io/localops-ui-kit/`; it is not advertised as live until deployment succeeds. Relative URLs support project subpaths. Other static hosts and Jekyll can serve the same directory unchanged; keep its assets and module paths together. A Jekyll build is optional, not required. The workflow follows the [GitHub Pages custom-workflow contract](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Qualification and publication sequence

1. Review the clean public checkout, private backup, ignored originals, public compatibility contract and history scan. Confirm the public remote is the new repository, not the old private repository.
2. Run Ruff, asset/publication checks and the full Python/Chromium/WebKit suites. Run the generated-site tests, including desktop/tablet/mobile in light/dark and direct focused component demos.
3. Build the wheel and sdist with Python only, verify source-byte equality and scan artifacts. Record exact hashes privately for consumers to qualify independently.
4. Preserve the merged urllib3 2.8.0 security update when promoting snapshots. Validate the lock independently: the pip CI workflow does not itself prove uv lock installation. Future dependency PRs belong in the public repository and must not be silently overwritten by an older development lock.
5. Commit/tag/push only with maintainer authorization. Publish a GitHub release or packages only with separate approval. The repository can be public without publishing to PyPI or npm.
6. Change visibility after history review, enable/deploy Pages if desired, and verify the actual public URL before linking it as live. Notify consumers of the exact artifact and retain their independent adoption gates.
