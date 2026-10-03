# Changelog: embedding-lifecycle

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.2] - 2026-09-15
### Fixed
- Drain reads no longer teach merging incompatible embedding spaces by
  `min(raw distance)`. Distances compare only inside one space (same model,
  dimension, preprocessing); rank independently and fuse or route with an
  evaluated rule. The `hnsw_scale_operations.md` `UNION ALL` + `min(dist)`
  pattern is same-spec index rebuild only.

## [1.0.1] - 2026-09-12
### Changed
- Established the per-skill changelog at the already-published metadata version; earlier revisions remain in Git history.
