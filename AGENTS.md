# Synesthetic Labs Agents

This document outlines the provenance and behavior of the agents within the Synesthetic Labs `v0.3.4` ecosystem.

## Generator Agent

The Generator agent is responsible for creating Synesthetic assets. Its behavior is governed by the following key aspects:

-   **Schema Branching**: The generator dynamically adjusts the asset structure based on the target `schema_version`. For `0.7.3`, it produces a legacy format, while `0.7.4` and later versions generate an enriched structure. This ensures backward compatibility while enabling new features.
-   **External Engines**: The generator can leverage external engines like Gemini and OpenAI. It constructs API requests tailored to each provider, including structured JSON output requests for Gemini.
-   **Normalization**: When integrating with external engines, the generator normalizes the received data, handling unknown keys and out-of-range values to produce a compliant Synesthetic asset.
-   **Error Handling**: The generator enforces request and response size limits and implements a no-retry policy for `4xx` client errors to prevent futile repeat attempts.

## Critic Agent

The Critic agent evaluates the assets produced by the Generator, ensuring they meet the required standards before they are persisted.

-   **Validation Modes**: The critic operates in both `strict` and `relaxed` modes. In `strict` mode, any MCP validation failures are treated as fatal. In `relaxed` mode, they are downgraded to warnings, allowing the workflow to proceed in a degraded state.
-   **MCP Integration**: The critic is responsible for invoking the Master Control Program (MCP) for validation. It correctly handles scenarios where the MCP is unavailable.

## Transport

-   **TCP Default**: The system defaults to TCP for MCP communication when the `MCP_ENDPOINT` is not set or is invalid, ensuring a reliable fallback mechanism.