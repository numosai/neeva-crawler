"""
Configuration for CSS extraction schemas
"""

A11Y_SCHEMA = {
    "name": "AccessibilityReport",
    "baseSelector": "html",
    "fields": [
        {"name": "images_missing_alt", "selector": "img:not([alt])", "type": "list", "fields": [{"name": "src", "type": "attribute", "attribute": "src"}]},
        {"name": "buttons_without_labels", "selector": "button:not([aria-label]):not([title]):empty", "type": "list", "fields": [{"name": "text", "type": "text"}]},
        {"name": "links_without_text", "selector": "a:not(:has(*)):empty", "type": "list", "fields": [{"name": "href", "type": "attribute", "attribute": "href"}]},
        {"name": "total_images", "selector": "img", "type": "list", "fields": [{"name": "alt", "type": "attribute", "attribute": "alt"}, {"name": "src", "type": "attribute", "attribute": "src"}]},
        {"name": "total_links", "selector": "a", "type": "list", "fields": [{"name": "href", "type": "attribute", "attribute": "href"}]},
        {"name": "total_buttons", "selector": "button", "type": "list", "fields": [{"name": "text", "type": "text"}]},
        {"name": "headings_hierarchy", "selector": "h1, h2, h3, h4, h5, h6", "type": "list", "fields": [{"name": "tag", "type": "tag"}, {"name": "text", "type": "text"}]},
        {"name": "html_lang", "selector": "html", "type": "attribute", "attribute": "lang"}
    ]
}

SEO_SCHEMA = {
    "name": "SEOReport",
    "baseSelector": "html",
    "fields": [
        {"name": "title", "selector": "title", "type": "text"},
        {"name": "meta_description", "selector": "meta[name=description]", "type": "attribute", "attribute": "content"},
        {"name": "h1", "selector": "h1", "type": "text"},
        {"name": "h2", "selector": "h2", "type": "list", "fields": [{"name": "text", "type": "text"}]}
    ]
}