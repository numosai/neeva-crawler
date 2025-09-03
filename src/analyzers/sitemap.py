"""
Sitemap generation module
"""
import json
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from urllib.parse import urlparse


class SitemapAnalyzer:
    """Handles visual sitemap generation from crawl data"""
    
    def __init__(self):
        pass
    
    def generate_sitemap(self, crawled_pages: list, flows_data: dict, output_dir: Path) -> bool:
        """
        Generate visual and text-based sitemaps from crawl data
        
        Args:
            crawled_pages: List of crawled page data
            flows_data: Flow data containing nodes and edges
            output_dir: Output directory (should be raw/ directory)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not isinstance(flows_data, dict):
                print("❌ flows_data must be a dictionary")
                return False
                
            if not isinstance(crawled_pages, list):
                print("❌ crawled_pages must be a list")
                return False
            
            # Create NetworkX graph from flow data
            graph = nx.DiGraph()
            url_titles = {}
            
            # Add nodes from flow data
            nodes_data = flows_data.get("nodes", [])
            if not nodes_data:
                print("⚠️  No nodes found in flows data")
                return False
            
            print(f"📊 Processing {len(nodes_data)} nodes from flows data")
                
            for node_item in nodes_data:
                if not isinstance(node_item, (list, tuple)) or len(node_item) < 2:
                    continue
                    
                node_id, node_data = node_item[0], node_item[1]
                if isinstance(node_data, dict) and node_data and 'url' in node_data:
                    url = node_data['url']
                    title = node_data.get('title', urlparse(url).path) or urlparse(url).path or 'Unknown'
                    url_titles[url] = title[:50]  # Truncate long titles
                    graph.add_node(url, title=title, node_id=node_id)
            
            # Add edges from flow data
            edges_data = flows_data.get("edges", [])
            print(f"🔗 Processing {len(edges_data)} edges from flows data")
            
            for edge in edges_data:
                if not isinstance(edge, dict):
                    continue
                    
                # Convert page node IDs back to URLs if needed
                from_node = edge.get("from")
                to_node = edge.get("to")
                
                if not from_node or not to_node:
                    continue
                
                # Find URLs for page nodes
                from_url = from_node
                to_url = to_node
                
                # If these are page node IDs, find corresponding URLs
                if isinstance(from_node, str) and from_node.startswith("page_"):
                    from_url = self._find_url_for_page_node(from_node, nodes_data)
                if isinstance(to_node, str) and not to_node.startswith("http"):
                    to_url = to_node  # Assume it's already a URL
                
                if from_url and to_url:
                    graph.add_edge(from_url, to_url, label=edge.get("label", ""))
            
            # Generate visual sitemap
            self._create_visual_sitemap(graph, output_dir)
            
            # Generate text-based sitemap
            self._create_text_sitemap(crawled_pages, graph, output_dir)
            
            print(f"✅ Sitemap saved to {output_dir}")
            print(f"📊 Total pages: {len(crawled_pages)}")
            print(f"🔗 Total unique URLs in graph: {len(graph.nodes())}")
            
            return True
            
        except Exception as e:
            import traceback
            print(f"❌ Error generating sitemap: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def _find_url_for_page_node(self, page_node: str, nodes: list) -> str:
        """Find URL for a given page node ID"""
        if not nodes:
            return ''
            
        for node_item in nodes:
            if not isinstance(node_item, (list, tuple)) or len(node_item) < 2:
                continue
                
            node_id, node_data = node_item[0], node_item[1]
            if node_id == page_node and isinstance(node_data, dict) and node_data:
                return node_data.get('url', '')
        return ''
    
    def _create_visual_sitemap(self, graph: nx.DiGraph, output_dir: Path) -> None:
        """Create visual PNG sitemap"""
        original_size = len(graph.nodes())
        
        if original_size > 50:
            print(f"📊 Large sitemap ({original_size} nodes) - creating simplified view")
            # Create subgraph with only high-importance nodes
            important_nodes = []
            for node in graph.nodes():
                in_degree = graph.in_degree(node)
                out_degree = graph.out_degree(node)
                # Include nodes that are major hubs (high connectivity)
                if in_degree >= 5 or out_degree >= 15:
                    important_nodes.append(node)
            
            # If we filtered too aggressively, use top nodes by degree
            if len(important_nodes) < 15:
                all_nodes_by_degree = sorted(graph.nodes(), 
                    key=lambda n: graph.in_degree(n) + graph.out_degree(n), 
                    reverse=True)
                important_nodes = all_nodes_by_degree[:20]
            elif len(important_nodes) > 30:
                # Sort by total degree and take top 30
                important_nodes = sorted(important_nodes, 
                    key=lambda n: graph.in_degree(n) + graph.out_degree(n), 
                    reverse=True)[:30]
            
            graph = graph.subgraph(important_nodes)
            print(f"📊 Simplified to {len(graph.nodes())} key nodes")
        
        plt.figure(figsize=(20, 15))
        
        # Use spring layout for better visualization
        pos = nx.spring_layout(graph, k=1.5, iterations=100, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, 
                              node_color='lightblue',
                              node_size=3000, 
                              alpha=0.7)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, 
                              edge_color='gray',
                              arrows=True, 
                              arrowsize=20, 
                              alpha=0.5)
        
        # Add labels (shortened URLs)
        labels = {}
        for url in graph.nodes():
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            if path_parts and path_parts[0]:
                labels[url] = path_parts[-1][:15]  # Last path segment, truncated
            else:
                labels[url] = 'home'
        
        nx.draw_networkx_labels(graph, pos, labels, font_size=8)
        
        plt.title("Site Map - Navigation Structure", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        # Save as SVG for better interactivity and scalability
        sitemap_path = output_dir / 'sitemap.svg'
        plt.savefig(sitemap_path, format='svg', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()  # Close to free memory
        
        print(f"📍 Visual sitemap saved: {sitemap_path}")
    
    def _create_text_sitemap(self, crawled_pages: list, graph: nx.DiGraph, output_dir: Path) -> None:
        """Create text-based sitemap"""
        sitemap_text_path = output_dir / 'sitemap.txt'
        
        with open(sitemap_text_path, 'w', encoding='utf-8') as f:
            f.write("WEBSITE SITEMAP\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Pages Crawled: {len(crawled_pages)}\n")
            f.write(f"Total Unique URLs: {len(graph.nodes())}\n")
            f.write(f"Total Links: {len(graph.edges())}\n\n")
            
            f.write("PAGE DETAILS\n")
            f.write("-" * 30 + "\n\n")
            
            for i, page in enumerate(crawled_pages, 1):
                if not isinstance(page, dict):
                    continue
                    
                url = page.get('url', 'Unknown URL')
                title = page.get('title', 'No title')
                page_id = page.get('id', f'page_{i}')
                
                f.write(f"{i}. {title}\n")
                f.write(f"   URL: {url}\n")
                f.write(f"   Page ID: {page_id}\n")
                
                # Find outgoing links from this page
                outgoing = []
                incoming = []
                
                for edge in graph.edges(data=True):
                    if edge[0] == url:
                        outgoing.append((edge[1], edge[2].get('label', '')))
                    elif edge[1] == url:
                        incoming.append((edge[0], edge[2].get('label', '')))
                
                if outgoing:
                    f.write(f"   Outgoing Links ({len(outgoing)}):\n")
                    for target_url, link_text in outgoing[:5]:  # Show first 5
                        link_display = link_text.strip() if link_text.strip() else 'No text'
                        f.write(f"     → {link_display}: {target_url}\n")
                    if len(outgoing) > 5:
                        f.write(f"     ... and {len(outgoing) - 5} more\n")
                
                if incoming:
                    f.write(f"   Incoming Links ({len(incoming)}):\n")
                    for source_url, link_text in incoming[:3]:  # Show first 3
                        link_display = link_text.strip() if link_text.strip() else 'No text'
                        f.write(f"     ← {link_display}: {source_url}\n")
                    if len(incoming) > 3:
                        f.write(f"     ... and {len(incoming) - 3} more\n")
                
                f.write("\n")
            
            # Add navigation summary
            f.write("NAVIGATION SUMMARY\n")
            f.write("-" * 30 + "\n\n")
            
            # Find pages with most outgoing links
            outgoing_counts = {}
            for url in graph.nodes():
                outgoing_counts[url] = len(list(graph.successors(url)))
            
            if outgoing_counts:
                top_hubs = sorted(outgoing_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                f.write("Top Navigation Hubs (most outgoing links):\n")
                for url, count in top_hubs:
                    parsed = urlparse(url)
                    page_name = parsed.path.strip('/').split('/')[-1] or 'homepage'
                    f.write(f"  {page_name}: {count} outgoing links\n")
                f.write("\n")
            
            # Find pages with most incoming links
            incoming_counts = {}
            for url in graph.nodes():
                incoming_counts[url] = len(list(graph.predecessors(url)))
            
            if incoming_counts:
                top_destinations = sorted(incoming_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                f.write("Most Referenced Pages (most incoming links):\n")
                for url, count in top_destinations:
                    parsed = urlparse(url)
                    page_name = parsed.path.strip('/').split('/')[-1] or 'homepage'
                    f.write(f"  {page_name}: {count} incoming links\n")
        
        print(f"📄 Text sitemap saved: {sitemap_text_path}")
    
    def generate_from_flows_file(self, flows_file: Path, output_dir: Path) -> bool:
        """
        Generate sitemap from an existing flows.json file
        
        Args:
            flows_file: Path to flows.json file
            output_dir: Output directory for sitemap files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not flows_file.exists():
                print(f"❌ Flows file not found: {flows_file}")
                return False
            
            with open(flows_file, 'r') as f:
                flows_data = json.load(f)
            
            # Reconstruct crawled pages from flow data
            crawled_pages = []
            nodes_data = flows_data.get("nodes", [])
            
            for node_item in nodes_data:
                if not isinstance(node_item, (list, tuple)) or len(node_item) < 2:
                    continue
                    
                node_id, node_data = node_item[0], node_item[1]
                if isinstance(node_data, dict) and isinstance(node_id, str) and node_id.startswith("page_"):
                    crawled_pages.append({
                        "id": node_id,
                        "url": node_data.get("url", ""),
                        "title": node_data.get("title", ""),
                        "markdown": node_data.get("markdown", "")
                    })
            
            return self.generate_sitemap(crawled_pages, flows_data, output_dir)
            
        except Exception as e:
            print(f"❌ Error reading flows file: {e}")
            return False