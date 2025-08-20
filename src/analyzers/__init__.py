"""
Analysis modules for Neeva-Crawler
"""
from .accessibility import AccessibilityAnalyzer
from .seo import SEOAnalyzer
from .qa import QAAnalyzer
from .ux import UXAnalyzer
from .sitemap import SitemapAnalyzer
from .html_generator import HTMLGeneratorAnalyzer

__all__ = ['AccessibilityAnalyzer', 'SEOAnalyzer', 'QAAnalyzer', 'UXAnalyzer', 'SitemapAnalyzer', 'HTMLGeneratorAnalyzer']