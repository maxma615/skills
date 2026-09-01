---
name: gemini-cli
description: Use the locally configured Gemini CLI as an alternate model pass for coding, frontend iteration, UI copy, implementation brainstorming, or second-opinion review. Trigger this skill when the user explicitly asks to use Gemini, asks to compare with another model, wants a second frontend draft, or wants Gemini CLI recorded as an available workflow in this environment.
---

# Gemini CLI

## Overview

Use the local `gemini` command as a secondary assistant, not as the source of truth for workspace state. Keep file inspection, editing, validation, and final integration in Codex unless the user explicitly asks Gemini to author or change files directly.

## Quick Start

- Verify the command exists with `Get-Command gemini`.
- Prefer non-interactive mode for reproducibility: `gemini -p "<prompt>"`.
- Prefer concise prompts with explicit output format requirements.
- Pass only the minimum context Gemini needs. Do not dump the whole repository unless necessary.

## When To Use It

- Use Gemini for alternate frontend concepts, visual wording, layout ideas, or implementation suggestions.
- Use Gemini for a second opinion on bugs, architecture tradeoffs, or API shape decisions.
- Use Gemini when the user explicitly asks to use Gemini CLI.
- Do not use Gemini as a replacement for local code inspection or repository-specific verification.

## Working Pattern

1. Inspect the codebase locally first in Codex.
2. Form a narrow question for Gemini.
3. Run Gemini in headless mode and request structured output.
4. Review the response critically.
5. Apply and verify changes locally in Codex.

## Prompting Guidance

- Ask for bounded outputs such as:
  - "Give 3 layout options with tradeoffs."
  - "Return a single React component draft."
  - "Review this code and list concrete risks only."
- Ask Gemini to avoid assumptions about files it has not seen.
- If sending code, include the exact file path and goal in the prompt.
- If using Gemini for frontend help, specify:
  - target framework
  - existing style direction
  - constraints on layout
  - whether code or design guidance is desired

## Command Patterns

Run a plain prompt:

```powershell
gemini -p "Review this UI layout strategy and list the top 5 risks." --output-format text
```

Pass file contents through stdin:

```powershell
Get-Content -Raw .\src\app.tsx | gemini -p "Refactor this component for clearer state flow. Return code only."
```

Request machine-readable output:

```powershell
gemini -p "Return JSON with keys summary, risks, next_steps." --output-format json
```

Use the current workspace as context, but keep the prompt specific:

```powershell
gemini -p "In this repository, propose a better dashboard layout for the existing robot console. No code, just a compact plan."
```

## Caveats

- First response can be slow.
- Local Gemini CLI may require prior authentication outside this skill.
- Treat Gemini output as a draft or review signal, not verified fact.
- Re-check any repository-specific claim before acting on it.
