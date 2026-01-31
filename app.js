fetch("news.json")
  .then(res => {
    if (!res.ok) {
      throw new Error("Failed to load news.json");
    }
    return res.json();
  })
  .then(data => {
    const container = document.getElementById("news");

    data.articles.forEach(article => {
      const el = document.createElement("article");
      el.className = `card ${article.image ? "" : "no-image"}`;

      el.innerHTML = `
        ${
          article.image
            ? `<img src="${article.image}" alt="" loading="lazy" />`
            : ""
        }

        <div class="content">
          <h2>${article.title}</h2>

          <div class="meta">
            ${article.source}
            ${
              article.publishedAt
                ? " • " + new Date(article.publishedAt).toLocaleString()
                : ""
            }
          </div>

          <p class="summary">${article.summary || ""}</p>

          ${
            article.ai_summary
              ? `<div class="ai">${article.ai_summary}</div>`
              : ""
          }

          <div class="tags">
            ${(article.tags || [])
              .map(t => `<span class="tag">${t}</span>`)
              .join("")}
          </div>

          <a class="read" href="${article.link}" target="_blank">
            Read full →
          </a>
        </div>
      `;

      container.appendChild(el);
    });
  })
  .catch(err => {
    console.error(err);
    document.getElementById("news").innerHTML =
      "<p style='color:#a1a1aa;text-align:center'>Failed to load news.</p>";
  });
