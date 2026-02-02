let ALL_ARTICLES = [];
let ACTIVE_TAG = "all";

fetch("news.json")
  .then(res => res.json())
  .then(data => {
    ALL_ARTICLES = data.articles;
    renderFilters(ALL_ARTICLES);
    renderArticles(ALL_ARTICLES);
  });

function renderFilters(articles) {
  const filterBar = document.querySelector(".filters");

  const tags = new Set();
  articles.forEach(a => (a.tags || []).forEach(t => tags.add(t)));

  [...tags].sort().forEach(tag => {
    const btn = document.createElement("button");
    btn.className = "filter";
    btn.dataset.tag = tag;
    btn.textContent = tag;

    btn.onclick = () => setFilter(tag);
    filterBar.appendChild(btn);
  });
}

function setFilter(tag) {
  ACTIVE_TAG = tag;

  document.querySelectorAll(".filter").forEach(b =>
    b.classList.toggle("active", b.dataset.tag === tag)
  );

  const filtered =
    tag === "all"
      ? ALL_ARTICLES
      : ALL_ARTICLES.filter(a => a.tags && a.tags.includes(tag));

  renderArticles(filtered);
}

function renderArticles(articles) {
  const container = document.getElementById("news");
  container.innerHTML = "";

  if (!articles.length) {
    container.innerHTML =
      "<p style='text-align:center;color:#a1a1aa'>No articles for this tag.</p>";
    return;
  }

  articles.forEach(article => {
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
            .map(
              t =>
                `<span class="tag" onclick="setFilter('${t}')">${t}</span>`
            )
            .join("")}
        </div>

        <a class="read" href="${article.link}" target="_blank">
          Read full →
        </a>
      </div>
    `;

    container.appendChild(el);
  });
}
