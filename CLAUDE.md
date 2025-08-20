# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Neeva-Crawler is a local-first website analysis tool that performs comprehensive quality assurance testing and evaluation. It uses Crawl4AI to crawl websites and generates structured QA test plans, accessibility audits, SEO analysis, and UX recommendations.

## Common Commands

### Environment Setup
```bash
# Set API keys (required for LLM-based analysis)
export GOOGLE_API_KEY="your-google-api-key-here"

# Or create a .env file
echo 'GOOGLE_API_KEY=your-google-api-key-here' > .env
```

### Setup and Execution
```bash
# Install dependencies
/opt/homebrew/bin/uv pip install -r requirements.txt

# Run full analysis on a website
/opt/homebrew/bin/uv run python main.py <url>
# Example: /opt/homebrew/bin/uv run python main.py https://www.example.com

# Use different LLM models
/opt/homebrew/bin/uv run python main.py <url> --model gemini/gemini-1.5-pro
/opt/homebrew/bin/uv run python main.py <url> --model gemini/gemini-1.5-flash
/opt/homebrew/bin/uv run python main.py <url> --model gemini/gemini-2.5-flash

# Run individual analysis modes (skips crawling)
/opt/homebrew/bin/uv run python main.py <url> --accessibility-only
/opt/homebrew/bin/uv run python main.py <url> --seo-only

# Regenerate QA tests with different models
/opt/homebrew/bin/uv run python main.py <url> --qa-only --model gemini/gemini-1.5-pro
/opt/homebrew/bin/uv run python main.py <url> --qa-only --model gemini/gemini-1.5-flash
/opt/homebrew/bin/uv run python main.py <url> --qa-only --model gemini/gemini-2.5-flash
```

## Architecture

### Core Structure
- **main.py**: Single orchestrator file containing all crawling, analysis, and report generation logic
- **schema.py**: Pydantic models for structured QA test plan outputs
- Uses async/await pattern with AsyncWebCrawler for all crawling operations

### Key Dependencies
- **Crawl4AI**: Web crawling and content extraction
- **NetworkX**: Graph-based site navigation analysis
- **Google Gemini**: LLM-powered test generation and UX analysis

### Data Flow
1. Crawls website recursively (configurable depth/page limits)
2. Builds directed graph of page relationships using NetworkX
3. Performs multi-modal analysis:
   - LLM-based: QA test plans, UX recommendations
   - CSS selector-based: Accessibility violations, SEO metadata
4. Outputs structured JSON reports to `qa_output/<domain>/`

### Output Structure
```
qa_output/
└── <domain>/
    ├── tests/             # YAML test files (multiple files)
    │   ├── test_1.yaml    # Individual QA test plans
    │   ├── test_2.yaml    # Each focuses on different aspects
    │   └── ...
    ├── accessibility.json  # Accessibility violations
    ├── seo.json           # SEO metadata analysis
    ├── ux.json            # UX recommendations
    ├── flows.json         # Site navigation graph
    └── screenshots/       # Page screenshots (JPEG format)
```

## Important Patterns

- All crawling uses `AsyncWebCrawler` with async/await
- LLM extraction uses `LLMExtractionStrategy` with defined schemas
- Graph analysis identifies user flows between pages
- Outputs are JSON-first with Pydantic validation
- Error handling uses basic success/failure checking