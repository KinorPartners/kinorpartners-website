# Kinor Partners website

Static website for [kinorpartners.com](https://kinorpartners.com), hosted free on **GitHub Pages**. This replaces the old Shopify store (which cost $39/month).

## How it works

Every page is plain HTML - no build step, no framework. GitHub Pages serves the files in this repo directly. Edit a file, commit, push, and the live site updates in about a minute.

## Structure

```
/                     Home (index.html)
/assets/              site.css, js/nav.js, img/ (all images live here)
/pages/<name>/        Each page is a folder with an index.html
/blogs/news/<name>/   Blog posts
CNAME                 Custom domain (kinorpartners.com) - do not delete
sitemap.xml           Lists all pages for search engines
robots.txt            Search-engine rules
404.html              Not-found page
```

The URL of a page matches its folder. For example
`/pages/amazon-seo-guide-how-to-rank-higher-on-amazon-search/index.html`
is served at `kinorpartners.com/pages/amazon-seo-guide-how-to-rank-higher-on-amazon-search/`.
These match the old Shopify URLs exactly, so Google rankings carry over.

## Editing

- **Change text on a page:** open its `index.html`, edit the words, commit.
- **Header / footer / colors:** shared markup is baked into each page's `index.html`; global styling is in `assets/site.css` (brand colors are the CSS variables at the top).
- **Add a new page:** copy an existing folder under `/pages/`, rename it, edit the content and the `<title>`/description. Add its URL to `sitemap.xml`.
- **Images:** put new images in `/assets/img/` and reference them as `/assets/img/yourfile.png`.

## Contact form

The form on `/pages/contact/` posts to **Formspree**. Before it works you must:
1. Create a free account at https://formspree.io and add a form.
2. Copy your form ID and replace `REPLACE_WITH_YOUR_FORM_ID` in `pages/contact/index.html`.

Until then, the page still shows the direct email link (oz@kinorpartners.com).

## Analytics

Google Analytics 4 (`G-H6T60VVJ27`) is included on every page.
