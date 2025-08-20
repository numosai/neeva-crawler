# Neeva-Crawler

A local-first website crawler that uses [Crawl4AI](https://github.com/unclecode/crawl4ai) to:

- Crawl multiple pages of a website
- Take screenshots per page
- Build a graph of flows between pages
- Generate QA test plans (via LLM)
- Produce Accessibility, SEO, and UX reports

## Features

- **Multi-page crawling** with depth and limit
- **Screenshots** saved for each page
- **QA Plan** generated with LLM based on flows + content
- **Accessibility Report** (missing `alt`, empty buttons, empty links)
- **SEO Report** (title, description, headings)
- **UX Recommendations** (LLM suggestions)
- **Flow Graph** saved as JSON (`flows.json`)

## Requirements

- Python 3.9+
- [Crawl4AI](https://github.com/unclecode/crawl4ai)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the crawler with a starting URL:

```bash
python main.py https://www.atob.com/get-started
```

Outputs will be saved under `qa_output/<domain>/`:

- `qa_plan.json` → structured QA test plan
- `accessibility.json` → accessibility issues
- `seo.json` → SEO metadata and heading structure
- `ux.json` → UX improvement recommendations
- `flows.json` → nodes and edges of crawled site graph
- `screenshots/` → screenshots of each crawled page

## Extending

- Modify schemas in `main.py` to expand accessibility/SEO checks
- Adjust depth/limit in `crawl()` to crawl more pages
- Plug in your own LLM provider (local or cloud) in `LLMExtractionStrategy`
