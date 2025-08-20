"""
CLI entry point for Neeva-Crawler
"""
import asyncio
import argparse
from dotenv import load_dotenv
from ..crawler_engine import CrawlerEngine


def create_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(description="Neeva-Crawler: Website analysis tool")
    parser.add_argument("url", help="URL to analyze")
    parser.add_argument("--model", default="openai/gpt-4o-mini", 
                       help="LLM model to use (default: openai/gpt-4o-mini, also supports: openai/gpt-4o, google/gemini-flash-1.5, google/gemini-flash-2.5)")
    parser.add_argument("--accessibility-only", action="store_true", 
                       help="Run accessibility analysis only (skip crawling)")
    parser.add_argument("--seo-only", action="store_true", 
                       help="Run SEO analysis only (skip crawling)")
    parser.add_argument("--qa-only", action="store_true",
                       help="Regenerate QA test plan from existing crawl data")
    parser.add_argument("--html-only", action="store_true",
                       help="Generate HTML site from existing analysis data (skip crawling)")
    return parser


async def main():
    """Main CLI entry point"""
    load_dotenv()
    
    parser = create_parser()
    args = parser.parse_args()
    
    engine = CrawlerEngine()
    
    if args.accessibility_only:
        await engine.analyze_accessibility_only(args.url)
    elif args.seo_only:
        await engine.analyze_seo_only(args.url)
    elif args.qa_only:
        await engine.analyze_qa_only(args.url, model=args.model)
    elif args.html_only:
        await engine.generate_html_only(args.url)
    else:
        await engine.full_crawl_and_analyze(args.url, model=args.model)


if __name__ == "__main__":
    asyncio.run(main())