# Golden Month reference set

This directory is reserved for the owner-blessed, synthetic Golden Month reference set that will be
created at the first complete product build. Until then, no output is blessed and no absent fixture is a
pass.

The planned contents are canonical JSON/API reports, a hash manifest, and only small reviewed export
fixtures needed for structural regression comparison. Generated sample-data outputs do not belong here;
they remain ignored and regenerate from `sample-data/generate_sample_data.py`.

See `docs/14_TESTING_QA_PLAN.md` §5.6 for selection, blessing, diff and regeneration controls.
