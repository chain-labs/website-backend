# CHA-123: Backend prompt management progress tracker

## Issue Details
- **Identifier**: CHA-123
- **Title**: backend: try to use prompt from OpenAI based on prompt ID to improve prompt management
- **Status**: In Progress
- **Priority**: Medium
- **Assignee**: angel@chainlabs.in
- **Created By**: Mihirsinh Parmar (2025-09-18)
- **Project**: Revive Chainlabs
- **Linear URL**: https://linear.app/chainlabs/issue/CHA-123/backend-try-to-use-prompt-from-openai-based-on-prompt-id-to-improve
- **Git Branch**: cha-123
- **Issue Summary**: Replace hard-coded prompt strings with OpenAI managed prompts by invoking the Responses API using a stored prompt ID and version.

## Reference Snippet
    from openai import OpenAI
    client = OpenAI()

    response = client.responses.create(
      prompt={
        "id": "pmpt_68cb9c1171f88197b09009bd8bf4b02d021f4a211f1c4d51",
        "version": "6"
      }
    )

## Current Progress
- Status: Scoping (0% complete)
- Last Updated: 2025-09-20
- Notes: Document established; implementation not yet started.

## What Needs To Be Done
- Audit current prompt construction and identify all call sites that rely on inline prompt strings.
- Extend the OpenAI client wrapper (if any) to accept prompt IDs and resolve the correct version.
- Externalize prompt identifiers and versions into configuration (environment variables or settings file) with sensible defaults.
- Ensure fallbacks exist if the remote prompt ID is missing or the API returns HTTP 404 or 410 for a stale version.
- Update automated tests (unit and integration) to cover the new prompt lookup flow and failure recovery logic.
- Document usage so other services know how to register and roll prompts forward safely.

## Implementation Plan
1. Map the existing prompt usage in the backend (likely under src/services and src/routes) and catalog prompts that should move to managed IDs.
2. Prototype a helper in the OpenAI client module that builds the prompt payload and handles errors from the Responses API.
3. Inject the helper into each LLM entry point, replacing inline prompt strings with configurable prompt IDs.
4. Wire configuration through environment variables (for example OPENAI_PROMPT_ID_*) and update deployment manifests such as railway.toml and Procfile if needed.
5. Create or update tests to mock the Responses API call and verify prompt resolution and error handling.
6. Run the relevant pytest suites and update this tracker with results and code references.

## Open Questions
- Which environments already have managed prompts created in OpenAI, and what IDs or versions should be used for development, staging, and production?
- Do we need to support automatic prompt version upgrades, or will versions be bumped manually in configuration?
- Are there fallbacks or legacy prompts that must remain available for rollback scenarios?
- Is there existing telemetry on prompt performance that we should leverage when switching to managed prompts?

## Next Checkpoints
- [ ] Confirm prompt inventory and configuration requirements with product or ML stakeholders.
- [ ] Draft implementation notes once the code investigation (Plan Step 1) is complete.
- [ ] Schedule validation testing once code changes land on branch cha-123.
