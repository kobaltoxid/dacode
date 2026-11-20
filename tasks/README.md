# Task Briefs

Copy `TASK_TEMPLATE.md`, then write one task per Markdown file in this directory. State the outcome, scope, and constraints. Generate a model-neutral prompt with:

```sh
../scripts/dacode.py prompt < my-task.md
```

The DaCode skill is the simpler workflow when your agent supports skills.

The generated output is the complete prompt to give the agent.
