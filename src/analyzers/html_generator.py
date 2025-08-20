"""
HTML Generator analyzer module
"""
from pathlib import Path
from urllib.parse import urlparse
from ..html_generator import HTMLGenerator


class HTMLGeneratorAnalyzer:
    """Handles static HTML site generation from analysis data"""
    
    def __init__(self):
        pass
    
    def generate_site(self, url: str, raw_dir: Path, html_dir: Path) -> bool:
        """
        Generate static HTML site from analysis data
        
        Args:
            url: Website URL for title extraction
            raw_dir: Directory containing raw analysis data
            html_dir: Output directory for HTML files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clean up existing HTML directory for fresh generation
            if html_dir.exists():
                import shutil
                shutil.rmtree(html_dir)
                print("🗑️ Cleared existing HTML files")
            
            generator = HTMLGenerator(raw_dir, html_dir)
            
            # Extract site title from URL as fallback
            parsed = urlparse(url)
            site_title = parsed.netloc.replace("www.", "").title()
            
            return generator.generate_site(site_title)
            
        except Exception as e:
            print(f"❌ Error generating HTML site: {e}")
            return False
    
    def generate_from_domain_data(self, url: str, output_dir: Path = None) -> bool:
        """
        Generate HTML site for a domain using existing analysis data
        
        Args:
            url: Website URL to determine domain
            output_dir: Base output directory (defaults to 'output')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not output_dir:
            output_dir = Path("output")
        
        parsed = urlparse(url)
        domain = parsed.netloc.replace(":", "_")
        
        raw_dir = output_dir / domain / "raw"
        html_dir = output_dir / domain / "html"
        
        if not raw_dir.exists():
            print(f"❌ No analysis data found for {domain}")
            print(f"Expected data at: {raw_dir}")
            return False
        
        return self.generate_site(url, raw_dir, html_dir)