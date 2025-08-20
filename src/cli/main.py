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
    parser.add_argument("--model", default="google/gemini-flash-2.5", 
                       help="LLM model to use (default: google/gemini-flash-2.5, also supports: openai/gpt-4o-mini, openai/gpt-4o, google/gemini-flash-1.5)")
    parser.add_argument("--analyze-and-html", action="store_true",
                       help="Run all analyses and generate HTML from existing crawl data (stage 2)")
    parser.add_argument("--html-only", action="store_true",
                       help="Generate HTML site from existing analysis data only (stage 3)")
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
    else:
        await engine.full_crawl_and_analyze(args.url, model=args.model)


if __name__ == "__main__":
    asyncio.run(main())