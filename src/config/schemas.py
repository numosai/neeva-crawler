"""
Configuration for CSS extraction schemas
"""

A11Y_SCHEMA = {
    "name": "AccessibilityReport",
    "baseSelector": "html",
    "fields": [
        {"name": "images_missing_alt", "selector": "img:not([alt])", "type": "count"},
        {"name": "buttons_without_labels", "selector": "button:empty", "type": "count"},
        {"name": "links_without_text", "selector": "a:not(:has(*)):empty", "type": "count"},
        {"name": "total_images", "selector": "img", "type": "count"},
        {"name": "total_links", "selector": "a", "type": "count"},
        {"name": "total_buttons", "selector": "button", "type": "count"},
        {"name": "headings_hierarchy", "selector": "h1, h2, h3, h4, h5, h6", "type": "list", "fields": [{"name": "tag", "type": "tag"}]},
        {"name": "missing_lang", "selector": "html:not([lang])", "type": "count"}
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