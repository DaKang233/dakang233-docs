(() => {
  "use strict";

  const dialog = document.querySelector("#search");
  const trigger = document.querySelector("#open-search");
  const input = document.querySelector("#search-input");
  const status = document.querySelector("#search-status");
  const results = document.querySelector("#search-results");
  const normalize = (value) => value.normalize("NFKC").toLowerCase();
  const compact = (value) => normalize(value).replace(/\s+/g, "");

  if (window.BOOK_SEARCH && typeof dialog.showModal === "function") {
    const index = window.BOOK_SEARCH.map(([url, part, title, body]) => ({
      url, part, title, body, titleKey: compact(title), bodyKey: compact(body),
    }));
    let focusedBeforeSearch;
    trigger.hidden = false;

    function appendHighlight(element, value, terms) {
      const folded = value.toLowerCase();
      let offset = 0;
      while (offset < value.length) {
        const hits = terms.map((term) => [folded.indexOf(term, offset), term.length])
          .filter(([position]) => position >= 0)
          .sort(([a, al], [b, bl]) => a - b || bl - al);
        if (!hits.length) {
          element.append(value.slice(offset));
          break;
        }
        const [position, length] = hits[0];
        element.append(value.slice(offset, position));
        const highlight = document.createElement("mark");
        highlight.textContent = value.slice(position, position + length);
        element.append(highlight);
        offset = position + length;
      }
    }

    function excerpt(body, terms) {
      const folded = body.toLowerCase();
      const match = terms.map((term) => folded.indexOf(term)).filter((position) => position >= 0);
      const start = match.length ? Math.max(0, Math.min(...match) - 35) : 0;
      const end = start + 135;
      return (start ? "…" : "") + body.slice(start, end) + (body.length > end ? "…" : "");
    }

    function search() {
      results.replaceChildren();
      const query = normalize(input.value).trim();
      if (!query) {
        status.textContent = "可搜索中文短语、实体名称或控制台命令。";
        return;
      }
      const terms = query.split(/\s+/).filter(Boolean);
      const best = new Map();
      for (const record of index) {
        if (!terms.every((term) => record.titleKey.includes(term) || record.bodyKey.includes(term))) continue;
        const titleHits = terms.filter((term) => record.titleKey.includes(term)).length;
        const bodyHits = terms.filter((term) => record.bodyKey.includes(term)).length;
        const score = titleHits * 5 + bodyHits * 2 + Number(record.titleKey === compact(query)) * 3;
        const previous = best.get(record.url);
        if (!previous || score > previous.score) best.set(record.url, { record, score });
      }
      const matches = [...best.values()].sort((a, b) => b.score - a.score);
      status.textContent = matches.length
        ? "找到 " + matches.length + " 处" + (matches.length > 30 ? "，显示前 30 处。" : "。")
        : "没有找到匹配内容。";
      for (const { record } of matches.slice(0, 30)) {
        const li = document.createElement("li");
        const link = document.createElement("a");
        link.href = record.url;
        const part = document.createElement("small");
        part.textContent = record.part;
        const title = document.createElement("strong");
        appendHighlight(title, record.title, terms);
        link.append(part, title);
        if (record.body) {
          const snippet = document.createElement("p");
          appendHighlight(snippet, excerpt(record.body, terms), terms);
          link.append(snippet);
        }
        link.addEventListener("click", () => dialog.close());
        li.append(link);
        results.append(li);
      }
    }

    function open() {
      if (dialog.open) return;
      focusedBeforeSearch = document.activeElement;
      dialog.showModal();
      input.focus();
      search();
    }

    trigger.addEventListener("click", open);
    input.addEventListener("input", search);
    dialog.addEventListener("close", () => focusedBeforeSearch?.focus({ preventScroll: true }));
    document.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        open();
      }
    });
  }

  if (navigator.clipboard?.writeText) {
    for (const block of document.querySelectorAll(".code-block")) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "copy-code";
      button.textContent = "复制";
      let timer;
      button.addEventListener("click", async () => {
        clearTimeout(timer);
        try {
          await navigator.clipboard.writeText(block.querySelector("code").textContent);
          button.textContent = "已复制";
        } catch {
          button.textContent = "请手动复制";
        }
        timer = setTimeout(() => { button.textContent = "复制"; }, 1800);
      });
      block.prepend(button);
    }
  }
})();
