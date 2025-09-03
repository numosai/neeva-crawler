"""
HTML Generator for creating static analysis websites
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader, select_autoescape
try:
    from jinja2 import Markup
except ImportError:
    from markupsafe import Markup
from .data_processor import DataProcessor


class HTMLGenerator:
    """Generates static HTML website from analysis data"""
    
    def __init__(self, raw_dir: Path, html_dir: Path):
        self.raw_dir = raw_dir
        self.html_dir = html_dir
        self.data_processor = DataProcessor(raw_dir)
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Load CSS content for inline embedding
        css_file = Path(__file__).parent / "static" / "css" / "styles.css"
        css_text = css_file.read_text() if css_file.exists() else ""
        # Mark CSS as safe to prevent HTML escaping
        self.css_content = Markup(css_text)
    
    def generate_site(self, site_title: str = "Website Analysis") -> bool:
        """
        Generate complete static HTML site
        
        Args:
            site_title: Title for the website
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Process all data
            print("🔄 Processing analysis data...")
            data = self.data_processor.process_all_data()
            
            # Extract actual site title from data if available
            if data.get('overview', {}).get('site_title'):
                site_title = data['overview']['site_title']
            
            # Create output directories
            self.html_dir.mkdir(parents=True, exist_ok=True)
            (self.html_dir / "assets").mkdir(exist_ok=True)
            (self.html_dir / "assets" / "screenshots").mkdir(exist_ok=True)
            
            # Copy static assets
            print("📁 Copying static assets...")
            self._copy_assets(data)
            
            # Generate HTML pages
            print("📄 Generating HTML pages...")
            pages = [
                ('index.html', 'dashboard.html', 'dashboard'),
                ('seo-analysis.html', 'seo_analysis.html', 'seo'),
                ('accessibility.html', 'accessibility.html', 'accessibility'), 
                ('qa-tests.html', 'qa_tests.html', 'qa'),
                ('ux-analysis.html', 'ux_analysis.html', 'ux'),
                ('screenshots.html', 'screenshots.html', 'screenshots')
            ]
            
            for output_file, template_file, current_page in pages:
                success = self._generate_page(
                    output_file, template_file, site_title, data, current_page
                )
                if not success:
                    print(f"⚠️ Failed to generate {output_file}")
            
            # Generate README for deployment
            self._generate_readme(site_title)
            
            # Update main index.html with this domain
            self._update_main_index(site_title, data)
            
            print(f"✅ Static site generated successfully in {self.html_dir}")
            print(f"🚀 Ready for deployment to GitHub Pages or any static host")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating HTML site: {e}")
            return False
    
    def _generate_page(self, output_file: str, template_file: str, 
                      site_title: str, data: Dict[str, Any], current_page: str) -> bool:
        """Generate a single HTML page"""
        try:
            template = self.env.get_template(template_file)
            html_content = template.render(
                site_title=site_title,
                data=data,
                current_page=current_page,
                css_content=self.css_content
            )
            
            output_path = self.html_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📄 Generated {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating {output_file}: {e}")
            return False
    
    def _copy_assets(self, data: Dict[str, Any]) -> None:
        """Copy static assets to HTML directory"""
        assets_dir = self.html_dir / "assets"
        
        # Copy screenshots if they exist
        screenshots_src = self.raw_dir / "screenshots"
        screenshots_dst = assets_dir / "screenshots"
        
        if screenshots_src.exists():
            # Copy all JPEG screenshots
            for jpg_file in screenshots_src.glob("*.jpg"):
                dst_file = screenshots_dst / jpg_file.name
                shutil.copy2(jpg_file, dst_file)
            
            print(f"📸 Copied {len(list(screenshots_src.glob('*.jpg')))} screenshots")
        
        # Copy sitemap image if it exists
        sitemap_src = self.raw_dir / "sitemap.svg"
        if sitemap_src.exists():
            shutil.copy2(sitemap_src, assets_dir / "sitemap.svg")
            print("🗺️ Copied sitemap visualization")
        
        # Copy any other assets that might be useful
        for asset_file in ["flows.json", "sitemap.txt"]:
            src_file = self.raw_dir / asset_file
            if src_file.exists():
                shutil.copy2(src_file, assets_dir / asset_file)
        
        # Create a data directory for processed JSON if needed
        data_dir = assets_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Copy original data files for reference
        for data_file in ["accessibility.json", "seo.json", "ux.json"]:
            src_file = self.raw_dir / data_file
            if src_file.exists():
                shutil.copy2(src_file, data_dir / data_file)
        
        # Export processed data for JavaScript consumption
        self._export_processed_data(data, data_dir)
    
    def _export_processed_data(self, data: Dict[str, Any], data_dir: Path) -> None:
        """Export processed data as JSON files for JavaScript consumption"""
        import json
        
        try:
            # Export QA test data
            if 'qa_tests' in data and data['qa_tests'].get('test_files'):
                qa_data = {
                    'summary': data['qa_tests'].get('summary', {}),
                    'test_files': data['qa_tests'].get('test_files', [])
                }
                with open(data_dir / 'qa_tests.json', 'w') as f:
                    json.dump(qa_data, f, indent=2)
                print("📊 Exported QA test data for JavaScript loading")
            
            # Export other processed data if needed
            for data_type in ['seo', 'accessibility', 'ux']:
                if data_type in data and data[data_type]:
                    with open(data_dir / f'{data_type}_processed.json', 'w') as f:
                        json.dump(data[data_type], f, indent=2)
            
            # Export overview stats
            if 'overview' in data:
                with open(data_dir / 'overview.json', 'w') as f:
                    json.dump(data['overview'], f, indent=2)
                    
        except Exception as e:
            print(f"⚠️ Error exporting processed data: {e}")
    
    def _generate_readme(self, site_title: str) -> None:
        """Generate README.md for deployment instructions"""
        readme_content = f"""# {site_title} - Analysis Report

This is an automatically generated static website containing comprehensive analysis results for **{site_title}**.

> **Note:** This site uses dynamic data loading and must be served over HTTP/HTTPS to function properly. 
> It will not work when opened directly as local files due to browser CORS restrictions. 
> Deploy to GitHub Pages, Netlify, or any static hosting service for full functionality.

## 📊 What's Included

- **SEO Analysis**: Search engine optimization insights and recommendations
- **Accessibility Report**: WCAG 2.1 AA compliance analysis
- **QA Test Suite**: Automated testing scenarios and verification points  
- **UX Analysis**: User experience recommendations and improvements
- **Screenshots Gallery**: Visual documentation of all analyzed pages
- **Site Structure**: Interactive sitemap and navigation analysis

## 🚀 Deployment

This static website can be deployed to any static hosting service:

### GitHub Pages
1. Push this repository to GitHub
2. Go to Settings > Pages
3. Select source branch (usually `main` or `gh-pages`)
4. Your site will be available at `https://username.github.io/repository-name`

### Netlify
1. Drag and drop the entire folder to [netlify.com/drop](https://netlify.com/drop)
2. Or connect your GitHub repository for automatic deployments

### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in this directory
3. Follow the deployment prompts

### Other Static Hosts
This website works with any static hosting service including:
- AWS S3 + CloudFront
- Google Cloud Storage
- Azure Static Web Apps
- Surge.sh
- Firebase Hosting

## 📁 File Structure

```
├── index.html              # Main dashboard
├── seo-analysis.html       # SEO insights
├── accessibility.html      # Accessibility report
├── qa-tests.html          # QA test cases
├── ux-analysis.html       # UX recommendations
├── screenshots.html       # Visual gallery
├── assets/
│   ├── screenshots/       # Page screenshots
│   ├── sitemap.svg       # Site structure visualization
│   └── data/             # Raw analysis data
└── README.md             # This file
```

## 🔧 Generated By

This report was automatically generated by [Neeva-Crawler](https://github.com/anthropics/claude-code), a comprehensive website analysis tool.

---

*Report generated on {self._get_current_date()}*
"""
        
        readme_path = self.html_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print("📝 Generated README.md with deployment instructions")
    
    def _get_current_date(self) -> str:
        """Get current date for README"""
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")
    
    @staticmethod
    def generate_for_domain(url: str, base_output_dir: Path = None) -> bool:
        """
        Convenience method to generate HTML site for a specific domain
        
        Args:
            url: Website URL to determine domain
            base_output_dir: Base output directory (defaults to 'output')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not base_output_dir:
            base_output_dir = Path("output")
        
        # Extract domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc.replace(":", "_")
        
        # Setup paths
        domain_dir = base_output_dir / domain
        raw_dir = domain_dir / "raw"
        html_dir = domain_dir / "html"
        
        if not raw_dir.exists():
            print(f"❌ No raw data found at {raw_dir}")
            print("Run a full crawl analysis first to generate data")
            return False
        
        # Generate the site
        generator = HTMLGenerator(raw_dir, html_dir)
        return generator.generate_site()
    
    def _update_main_index(self, site_title: str, data: Dict[str, Any]) -> None:
        """Update the main index.html file with a new domain card"""
        try:
            # Get the domain from the current raw_dir path
            domain = self.raw_dir.parent.name
            
            # Get the project root directory (3 levels up from raw_dir)
            project_root = self.raw_dir.parent.parent.parent
            main_index_path = project_root / "index.html"
            
            if not main_index_path.exists():
                print(f"⚠️ Main index.html not found at {main_index_path}")
                return
            
            # Read the current main index.html
            content = main_index_path.read_text(encoding='utf-8')
            
            # Create the new domain card
            site_description = self._generate_domain_description(domain, data)
            new_card = f'''            <a href="output/{domain}/html/index.html" class="domain-card">
                <h3><i class="fas fa-globe"></i> {domain}</h3>
                <p>{site_description}</p>
                <div class="quick-links">
                    <span class="link-item"><i class="fas fa-tachometer-alt"></i> Dashboard</span>
                    <span class="link-item"><i class="fas fa-universal-access"></i> Accessibility</span>
                    <span class="link-item"><i class="fas fa-search"></i> SEO Analysis</span>
                    <span class="link-item"><i class="fas fa-tasks"></i> QA Tests</span>
                    <span class="link-item"><i class="fas fa-user-check"></i> UX Analysis</span>
                    <span class="link-item"><i class="fas fa-images"></i> Screenshots</span>
                </div>
            </a>'''
            
            # Check if this domain already exists in the index
            if f'href="output/{domain}/html/index.html"' in content:
                # Domain already exists, update the card
                import re
                pattern = rf'<a href="output/{re.escape(domain)}/html/index\.html".*?</a>'
                content = re.sub(pattern, new_card, content, flags=re.DOTALL)
                print(f"📝 Updated existing card for {domain} in main index.html")
            else:
                # Add new domain card before the closing </div> of domain-grid
                insertion_point = content.find('</div>\n    </div>\n\n    <script>')
                if insertion_point != -1:
                    content = content[:insertion_point] + f'\n{new_card}\n        ' + content[insertion_point:]
                    print(f"📝 Added new card for {domain} to main index.html")
                else:
                    print(f"⚠️ Could not find insertion point in main index.html")
                    return
            
            # Write the updated content back
            main_index_path.write_text(content, encoding='utf-8')
            
        except Exception as e:
            print(f"❌ Error updating main index.html: {e}")
    
    def _generate_domain_description(self, domain: str, data: Dict[str, Any]) -> str:
        """Generate a description for the domain based on analysis data"""
        
        # Try to get site title or description from the data
        if data.get('overview', {}).get('site_title'):
            title = data['overview']['site_title']
            # Create a description based on the title
            if 'goodbill' in domain.lower():
                return "Healthcare billing optimization service - hospital bill negotiations and savings analysis"
            elif 'stage' in domain.lower() or 'dev' in domain.lower():
                return "Staging environment analysis - development website testing and validation"
            elif 'atob' in domain.lower():
                return "Fleet fuel card and logistics solutions - comprehensive business services analysis"
            else:
                return f"Website analysis for {title} - comprehensive QA testing and recommendations"
        
        # Fallback generic description
        return "Complete website analysis with accessibility, SEO, and UX recommendations"
    
    def get_site_stats(self) -> Dict[str, Any]:
        """Get statistics about the generated site"""
        if not self.html_dir.exists():
            return {}
        
        html_files = list(self.html_dir.glob("*.html"))
        asset_files = list((self.html_dir / "assets").rglob("*")) if (self.html_dir / "assets").exists() else []
        
        total_size = sum(f.stat().st_size for f in html_files + asset_files if f.is_file())
        
        return {
            "html_files": len(html_files),
            "asset_files": len(asset_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "output_directory": str(self.html_dir),
            "ready_for_deployment": len(html_files) >= 5
        }