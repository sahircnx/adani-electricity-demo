# Adani Electricity Demo

A mirrored, unstyled HTML representation of the [Adani Electricity](https://www.adanielectricity.com/) website created for search indexing (e.g., Coveo AI Search) and crawler testing.

## Key Files

- [sitemap.xml](file:///Users/sahir.khan/Desktop/adani-electricity-demo/sitemap.xml): Standard XML Sitemap (Sitemaps 0.9 protocol) listing all 408 valid, crawlable pages with calculated priorities and change frequencies.
- [robots.txt](file:///Users/sahir.khan/Desktop/adani-electricity-demo/robots.txt): Search crawler directives allowing public content while disallowing custom error pages (`CustomErrorPage/`, `page-not-found/`), login redirects, and OTP/portal routes.
- [sitemap.html](file:///Users/sahir.khan/Desktop/adani-electricity-demo/sitemap.html): Interactive visual directory of all pages categorized by locale (English, Hindi, Marathi) and functional section with real-time search filtering.
- [generate_sitemap.py](file:///Users/sahir.khan/Desktop/adani-electricity-demo/generate_sitemap.py): Automated script to regenerate `sitemap.xml`, `robots.txt`, and `sitemap.html`.

## Regenerating the Sitemap & Robots File

The default base URL is set to GitHub Pages:
`https://sahircnx.github.io/adani-electricity-demo`

To regenerate with the default URL:
```bash
python3 generate_sitemap.py
```

To regenerate for local development (e.g., VS Code Live Server on port 5501):
```bash
python3 generate_sitemap.py --base-url http://localhost:5501
```

To regenerate for production domain:
```bash
python3 generate_sitemap.py --base-url https://www.adanielectricity.com
```
