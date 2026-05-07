# [Deprecated] Google AI Python SDK for the Gemini API

With Gemini 2.0, we took the chance to create a single unified SDK for all developers who want to use Google's GenAI models (Gemini, Veo, Imagen, etc). As part of that process, we took all of the feedback from this SDK and what developers like about other SDKs in the ecosystem to create the [Google Gen AI SDK](https://github.com/googleapis/python-genai). 

The full migration guide from the old SDK to new SDK is available in the [Gemini API docs](https://ai.google.dev/gemini-api/docs/migrate).

The Gemini API docs are fully updated to show examples of the new Google Gen AI SDK. We know how disruptive an SDK change can be and don't take this change lightly, but our goal is to create an extremely simple and clear path for developers to build with our models so it felt necessary to make this change.

Thank you for building with Gemini and [let us know](https://discuss.ai.google.dev/c/gemini-api/4) if you need any help!

**Please be advised that this repository is now considered legacy.** For the latest features, performance improvements, and active development, we strongly recommend migrating to the official **[Google Generative AI SDK for Python](https://github.com/googleapis/python-genai)**.

**Support Plan for this Repository:**

*   **Limited Maintenance:** Development is now restricted to **critical bug fixes only**. No new features will be added.
*   **Purpose:** This limited support aims to provide stability for users while they transition to the new SDK.
*   **End-of-Life Date:** All support for this repository (including bug fixes) will permanently end on **August 31st, 2025**.

We encourage all users to begin planning their migration to the [Google Generative AI SDK](https://github.com/googleapis/python-genai) to ensure continued access to the latest capabilities and support.

## Legacy Update Governance (Learn / Observe / Update)

For any exceptional maintenance decision in this legacy repository, use the following phased process:

1. **Learn**
   - Collect evidence in a separate evaluation track.
   - Review candidate model or dependency changes with a focus on security posture and operational risk.

2. **Observe**
   - Monitor safety, reliability, and regression signals over time.
   - Record outcomes and trends before considering a repository update.

3. **Update (only if needed)**
   - Proceed only when predefined acceptance criteria are met.
   - Keep changes minimal and scoped to the identified critical need.

### Acceptance criteria for any update

- **Security:** No known critical/high vulnerabilities and acceptable data-handling guarantees.
- **Reliability:** Stable test outcomes, acceptable error-rate behavior, and reproducible results.
- **Compatibility:** No breaking changes for existing users.

### Review cadence and release controls

- Run periodic checkpoints to reassess new risks, capabilities, and vendor changes.
- Document explicit "no change" outcomes when criteria are not met.
- If an update is approved, run full validation (`python -m unittest`) and complete a security review before release.
- Include clear rollback and communication notes for any approved update.

For broader capability or platform improvements, prefer migration to the actively maintained [Google Gen AI SDK](https://github.com/googleapis/python-genai) rather than expanding this legacy codebase.

<!-- 
[START update]
# With Gemini 2 we're launching a new SDK. See the following doc for details.
# https://ai.google.dev/gemini-api/docs/migrate
[END update]
 -->
