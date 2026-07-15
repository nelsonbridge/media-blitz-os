# Branch Consolidation Trigger

This housekeeping change exists solely to trigger the governed post-merge branch consolidation workflow.

Expected post-merge state:

- `main`
- `sandbox`

All other branches are deleted. Any nonmerged unique tip is preserved by an archive tag before deletion.
