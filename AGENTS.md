# DaCode Contributor Entry Point

Before changing this project, read [RULESET.md](RULESET.md) and the task brief. The ruleset is the canonical source of writing policy.

Use the `dacode` skill for documentation tasks. Its source is in `skills/dacode/` and its command-line implementation is in `scripts/dacode.py`.

For local agents without skill support, generate a portable prompt with:

```sh
python3 scripts/dacode.py prompt < tasks/my-task.md
```

The command writes the fixed instructions, ruleset, and task brief to standard output. It does not call a model.

Use `dacode new` for new pages and diagram or chart sources. When DaCode targets another project, put new docs and diagram sources under that project's root `docs/` directory. Complete the ruleset's final audit before reporting work as done. Keep generated diagrams and charts reproducible from their checked-in text sources.
