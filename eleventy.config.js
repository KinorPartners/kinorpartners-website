// Kinor Partners - static site build.
//
// The page bodies are hand-written/scraped HTML that contains plenty of
// literal braces, so html/markdown template engines are switched OFF: pages
// are copied through verbatim and only the .njk layout is rendered. Front
// matter and layouts still work.
module.exports = function (eleventyConfig) {
  for (const file of [
    "src/assets",
    "src/CNAME",
    "src/robots.txt",
    "src/sitemap.xml",
    "src/site.webmanifest",
    "src/favicon.ico",
  ]) {
    eleventyConfig.addPassthroughCopy(file);
  }

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
    },
    htmlTemplateEngine: false,
    markdownTemplateEngine: false,
  };
};
