fetch("news.json")
  .then(res => res.json())
  .then(data => {
    const container = document.getElementById("news");

    data.articles.forEach(article => {
      const el = document.createElement("article");
      el.className = "article";

      el.innerHTML = `
        ${article.image ? `<img src="${article.image}" />` : ""}
        <div class="article-content">
          <h2>${article.title}</h2>

          <div class="meta">
            ${article.source}
            ${article.publishedAt ? " • " + new Date(article.publishedAt).toLocaleString() : ""}
          </div>

          <p>${article.summary}</p>

          ${
            article.ai_summary
              ? `<div class="ai">${article.ai_summary}</div>`
              : ""
          }

          <div class="tags">
            ${article.tags.map(t => `<span class="tag">${t}</span>`).join("")}
          </div>

          <a class="read" href="${article.link}" target="_blank">
            Read full article →
          </a>
        </div>
      `;

      container.appendChild(el);
    });
  });
