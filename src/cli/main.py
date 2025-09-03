"""
CLI entry point for Neeva-Crawler
"""
import asyncio
import argparse
from dotenv import load_dotenv
from ..crawler_engine import CrawlerEngine


def create_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Neeva-Crawler: Website analysis tool",
        epilog="""
Three analysis stages:
1. Full run (default): crawl website + run all analyzers + generate HTML
2. --analyze-and-html: run all analyzers + generate HTML (requires existing crawl data)
3. --html-only: generate HTML only (requires existing analysis data)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("url", help="URL to analyze")
    parser.add_argument("--model", default="gemini/gemini-2.5-flash", 
                       help="LLM model to use (default: gemini/gemini-2.5-flash, also supports: gemini/gemini-1.5-flash, gemini/gemini-1.5-pro)")
    parser.add_argument("--analyze-and-html", action="store_true",
                       help="Run all analyses and generate HTML from existing crawl data (stage 2)")
    parser.add_argument("--html-only", action="store_true",
                       help="Generate HTML site from existing analysis data only (stage 3)")
    parser.add_argument("--qa-only", action="store_true",
                       help="Run QA analysis only from existing crawl data")
    parser.add_argument("--sitemap-only", action="store_true",
                       help="Regenerate sitemap only from existing crawl data")
    parser.add_argument("--git-push", action="store_true",
                       help="Automatically git add, commit, and push results after analysis")
    return parser


async def main():
    """Main CLI entry point"""
    load_dotenv()
    
    parser = create_parser()
    args = parser.parse_args()
    
    engine = CrawlerEngine()
    
    if args.analyze_and_html:
        await engine.analyze_and_html(args.url, model=args.model)
    elif args.html_only:
        await engine.generate_html_only(args.url)
    elif args.qa_only:
        await engine.analyze_qa_only(args.url, model=args.model)
    elif args.sitemap_only:
        await engine.regenerate_sitemap_only(args.url)
    else:
        await engine.full_crawl_and_analyze(args.url, model=args.model, git_push=args.git_push)


if __name__ == "__main__":
    asyncio.run(main())