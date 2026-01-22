# CueX Skills System

Skills are specialized knowledge bases and toolsets that extend my capabilities for the CueX project. Unlike simple workflows, skills can include scripts, templates, and deep domain knowledge.

## Structure

Each skill is located in its own subdirectory under `.agent/skills/`:

```text
.agent/skills/
└── <skill-name>/
    ├── SKILL.md (Required) - Instructions and metadata
    ├── scripts/ (Optional) - Automation scripts (Python, Batch, etc.)
    └── resources/ (Optional) - Templates, assets, or example data
```

## How to use

When I (the AI) detect that a task falls under the domain of a specific skill, I will:
1.  Navigate to the skill directory.
2.  Read the `SKILL.md` to understand the specialized instructions.
3.  Utilize the provided scripts and resources to complete the task with high precision.

## Active Skills

| Skill Name | Description | Status |
| :--- | :--- | :--- |
| `ui-expert` | Maintains the "Rich Aesthetics" and design system of CueX. | [ ] Proposed |
| `gdtf-helper` | Specialized in GDTF data validation and API interaction. | [ ] Proposed |
| `export-master` | Manages consistency across PDF and MA3 export formats. | [ ] Proposed |
