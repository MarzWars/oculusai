# Requirements Document

## Introduction

This feature replaces the existing DuckDuckGo Search (DDGS) web search integration in the Oculus AI Flask application with the Tavily Search API. The current implementation uses the `duckduckgo_search` library via a `web_search()` function in `app.py`. The replacement must preserve all existing behaviour: the `should_search` / `SEARCH_YES` / `SEARCH_NO` trigger logic, the `refine_query` pre-processing step, and the formatted search-result block injected into the prompt. The Tavily API key must be supplied via an environment variable and must never be hardcoded.

## Glossary

- **Oculus_App**: The Oculus AI Flask application (`app.py`) built by Lex Digitals.
- **Web_Search_Module**: The section of `app.py` responsible for deciding whether to search, refining the query, calling the search provider, and formatting results.
- **DDGS**: The `duckduckgo_search` Python library — the search provider being replaced.
- **Tavily_Client**: The `tavily-python` SDK client used to call the Tavily Search API.
- **TAVILY_API_KEY**: The environment variable that holds the Tavily API key.
- **should_search**: The existing function in `app.py` that returns `True` when a user message warrants a live web search, based on `SEARCH_YES` and `SEARCH_NO` regex pattern lists.
- **refine_query**: The existing function in `app.py` that strips filler phrases from the raw user message to produce a focused search query.
- **Search_Result_Block**: The formatted string injected into the prompt under the `══════════ LIVE WEB SEARCH RESULTS ══════════` heading.
- **Prompt_Builder**: The `build_prompt` function in `app.py` that assembles the full prompt sent to the Xoltron model.

---

## Requirements

### Requirement 1: Replace DDGS with Tavily as the Search Provider

**User Story:** As a developer maintaining Oculus AI, I want the web search function to call the Tavily API instead of DuckDuckGo, so that search results are more reliable and the integration is officially supported.

#### Acceptance Criteria

1. THE `Web_Search_Module` SHALL import and use `Tavily_Client` from the `tavily-python` package instead of `DDGS` from `duckduckgo_search`.
2. WHEN `web_search()` is called with a raw query, THE `Web_Search_Module` SHALL pass the refined query (output of `refine_query`) to the Tavily Search API.
3. THE `Web_Search_Module` SHALL request a maximum of 6 search results per query, matching the existing `max_results=6` default.
4. IF the Tavily API returns zero results for the refined query, THEN THE `Web_Search_Module` SHALL retry with a broader query consisting of the first four words of the refined query and a `max_results` of 3, matching the existing fallback behaviour.
5. IF the Tavily API call raises an exception, THEN THE `Web_Search_Module` SHALL return the string `"Web search unavailable (<ExceptionType>)."` so that the `Prompt_Builder` can handle the empty-or-error case gracefully.

---

### Requirement 2: Tavily API Key Configuration

**User Story:** As a developer deploying Oculus AI, I want the Tavily API key to be read from an environment variable, so that credentials are never hardcoded in source code.

#### Acceptance Criteria

1. THE `Oculus_App` SHALL read the Tavily API key exclusively from the `TAVILY_API_KEY` environment variable at startup.
2. IF `TAVILY_API_KEY` is not set or is an empty string at startup, THEN THE `Oculus_App` SHALL raise a descriptive `Exception` that halts startup, consistent with the existing guard for `SUPABASE_URL` and `SUPABASE_KEY`.
3. THE `Oculus_App` SHALL initialise `Tavily_Client` using the value of `TAVILY_API_KEY` before any search request is made.

---

### Requirement 3: Preserve Search Trigger Logic

**User Story:** As a developer, I want the `should_search`, `SEARCH_YES`, and `SEARCH_NO` logic to remain unchanged, so that the decision to perform a web search is unaffected by the provider swap.

#### Acceptance Criteria

1. THE `Web_Search_Module` SHALL retain the `SEARCH_YES` regex pattern list without modification.
2. THE `Web_Search_Module` SHALL retain the `SEARCH_NO` regex pattern list without modification.
3. THE `Web_Search_Module` SHALL retain the `should_search` function signature and logic without modification.
4. THE `Web_Search_Module` SHALL retain the `refine_query` function signature and logic without modification.
5. WHEN `should_search` returns `False` for a given user message, THE `Prompt_Builder` SHALL not call `web_search()`, matching existing behaviour.

---

### Requirement 4: Preserve Search Result Prompt Injection Format

**User Story:** As a developer, I want the formatted search result block injected into the prompt to remain structurally identical, so that the Xoltron model receives results in the format it was prompted to handle.

#### Acceptance Criteria

1. WHEN Tavily returns results, THE `Web_Search_Module` SHALL format each result as `[N] <title>\n<body>\nSource: <url>`, where `N` is the 1-based result index, matching the existing block format.
2. THE `Web_Search_Module` SHALL truncate any result body exceeding 280 characters at the last word boundary before the limit and append `…`, matching the existing truncation behaviour.
3. THE `Web_Search_Module` SHALL prefix the formatted result block with `Search query: "<query>"\n\n`, matching the existing prefix.
4. WHEN `web_search()` returns a non-empty string, THE `Prompt_Builder` SHALL inject it under the `══════════ LIVE WEB SEARCH RESULTS ══════════` heading, unchanged from the current injection logic.

---

### Requirement 5: Remove DuckDuckGo Dependency

**User Story:** As a developer, I want the `duckduckgo_search` library removed from the project dependencies, so that the codebase has no unused packages.

#### Acceptance Criteria

1. THE `Oculus_App` SHALL NOT import `DDGS` or any symbol from `duckduckgo_search` after the migration.
2. THE `requirements.txt` file SHALL NOT list `duckduckgo-search` after the migration.
3. THE `requirements.txt` file SHALL list `tavily-python` with a pinned or minimum version after the migration.
