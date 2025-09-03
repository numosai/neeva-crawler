# Neeva-Crawler

A comprehensive website analysis tool that uses [Crawl4AI](https://github.com/unclecode/crawl4ai) to perform multi-page crawling, quality assurance testing, and automated reporting.

## Features

- **Multi-page crawling** with configurable depth and page limits
- **Complete QA test suite** generation using LLM analysis
- **Accessibility auditing** (WCAG compliance, missing alt text, empty links)
- **SEO analysis** (metadata, headings, page structure)
- **UX recommendations** powered by LLM
- **Visual screenshots** for every crawled page
- **Interactive HTML reports** with responsive design
- **Site flow mapping** and navigation analysis
- **Automated git workflow** for results management

## Quick Start

### Option 1: GitHub Actions (Recommended)

The easiest way to run analysis is through the GitHub Actions workflow:

1. **Set up repository secret:**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add new repository secret: `GOOGLE_API_KEY` with your Google API key

2. **Run analysis:**
   - Navigate to Actions tab in your GitHub repository
   - Click "Website Analyzer" workflow
   - Click "Run workflow" button
   - Enter the website URL to analyze
   - Select LLM model (optional)
   - Click "Run workflow"

3. **View results:**
   - Results are automatically committed to the `output/` directory
   - HTML reports are generated for easy viewing

### Option 2: Local Installation

**Requirements:**
- Python 3.9+
- Google API key for Gemini models

**Setup:**
```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt

# Set API key
export GOOGLE_API_KEY="your-google-api-key-here"
```

**Usage:**
```bash
# Full analysis with automatic git commit/push
uv run python main.py https://example.com --git-push

# Different LLM models
uv run python main.py https://example.com --model gemini/gemini-1.5-pro

# Individual analysis modes
uv run python main.py https://example.com --html-only  # Regenerate HTML from existing data
uv run python main.py https://example.com --qa-only
uv run python main.py https://example.com --sitemap-only  # Regenerate sitemap only

# Note: Always use full URL with protocol (https://) even when regenerating HTML
```

**Viewing HTML Reports Locally:**
```bash
# The HTML reports use JavaScript and require a web server to work properly
# To view locally without CORS issues:
cd output/example.com/html
uv run python -m http.server 9999

# Then open: http://localhost:9999
# This enables interactive features like zoom/pan on the sitemap
```

## Output Structure

Results are organized in `output/<domain>/`:

```
output/example.com/
├── html/                          # Interactive HTML reports
│   ├── index.html                # Main dashboard
│   ├── qa-tests.html            # QA test plans
│   ├── accessibility.html       # Accessibility audit
│   ├── seo-analysis.html        # SEO analysis
│   ├── ux-analysis.html         # UX recommendations
│   ├── screenshots.html         # Page screenshots
│   └── assets/                  # Static assets and data
└── raw/                         # Raw analysis data
    ├── tests/                   # YAML test files
    ├── screenshots/             # Page screenshots (JPEG)
    ├── accessibility.json       # Accessibility violations
    ├── seo.json                # SEO metadata
    ├── ux.json                 # UX recommendations
    ├── flows.json              # Site navigation graph
    └── sitemap.svg             # Interactive visual site map
```

## Configuration

### Environment Variables
- `GOOGLE_API_KEY` - Required for LLM-based analysis

### CLI Options
```bash
python main.py <url> [options]

Options:
  --model MODEL           LLM model (default: gemini/gemini-2.5-flash)
  --git-push             Auto commit and push results
  --html-only            Regenerate HTML from existing data (use full URL with https://)
  --qa-only              Run QA analysis only
  --sitemap-only         Regenerate sitemap from existing data
  --seo-only             Run SEO analysis only
```

### Customization

Key configuration files:
- `src/utils/crawler.py` - Crawling settings (max_pages: 20, max_depth: 2)
- `src/config/prompts.py` - LLM prompts for analysis
- `src/html_generator/templates/` - HTML report templates

## Architecture

- **Crawler Engine** (`src/crawler_engine.py`) - Main orchestrator
- **Web Crawler** (`src/utils/crawler.py`) - Multi-page crawling with Crawl4AI
- **Analyzers** (`src/analyzers/`) - Specialized analysis modules
- **HTML Generator** (`src/html_generator/`) - Interactive report generation
- **CLI** (`src/cli/main.py`) - Command-line interface

## Contributing

The tool is designed to be easily extensible:

1. **Add new analyzers** by extending the base analyzer class
2. **Customize HTML templates** in `src/html_generator/templates/`
3. **Modify crawling behavior** in `src/utils/crawler.py`
4. **Extend QA test generation** in `src/analyzers/qa.py`

## License

This project is for internal use and analysis purposes.