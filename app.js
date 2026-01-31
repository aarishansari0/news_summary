el.innerHTML = `
  <div class="card ${article.image ? "has-image" : "no-image"}">
    ${
      article.image
        ? `<img src="${article.image}" alt="" loading="lazy" />`
        : ""
    }

    <div class="content">
      <h2>${article.title}</h2>

      <div class="meta">
        ${article.source}
        ${article.publishedAt ? " • " + new Date(article.publishedAt).toLocaleString() : ""}
      </div>

      <p class="summary">${article.summary}</p>

      ${
        article.ai_summary
          ? `<div class="ai">${article.ai_summary}</div>`
          : ""
      }

      <div class="tags">
        ${article.tags.map(t => `<span class="tag">${t}</span>`).join("")}
      </div>

      <a class="read" href="${article.link}" target="_blank">
        Read full →
      </a>
    </div>
  </div>
`;
