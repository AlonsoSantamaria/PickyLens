/* Presentation-only Markdown. Never pass untrusted HTML directly to innerHTML. */
(function (root) {
  "use strict";
  const md = root.markdownit({html:false, linkify:false, typographer:false}).disable("image");
  const defaultValidate = md.validateLink.bind(md);
  md.validateLink = href => /^(https?:|mailto:)/i.test(href) && defaultValidate(href);
  const defaultLink = md.renderer.rules.link_open || ((tokens, index, options, env, renderer) => renderer.renderToken(tokens,index,options));
  md.renderer.rules.link_open = (tokens,index,options,env,renderer) => {
    tokens[index].attrSet("rel","noopener noreferrer");
    return defaultLink(tokens,index,options,env,renderer);
  };
  md.renderer.rules.table_open = () => '<div class="table-scroll" aria-label="Answer table"><table>';
  md.renderer.rules.table_close = () => '</table></div>';
  md.renderer.rules.th_open = (tokens,index,options,env,renderer) => {
    tokens[index].attrSet("scope","col");
    return renderer.renderToken(tokens,index,options);
  };
  // Answer headings remain subordinate to the workspace section heading.
  for (const type of ["heading_open","heading_close"]) {
    md.renderer.rules[type] = (tokens,index) => {
      const level = Math.min(6,Number(tokens[index].tag.slice(1))+2);
      return type === "heading_open" ? `<h${level}>` : `</h${level}>\n`;
    };
  }
  function html(text) { return md.render(String(text)); }
  const renderedSources = new WeakMap();
  function render(target,text) {
    if(renderedSources.get(target) === text) return;
    // Only the constrained parser's escaped output reaches this HTML sink.
    target.innerHTML = html(text);
    renderedSources.set(target,text);
  }
  root.PickyLensMarkdown = {html,render};
})(typeof window === "undefined" ? globalThis : window);
