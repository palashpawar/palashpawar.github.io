// GitHub activity on the home page: contribution calendar from data/github.json
// (refreshed daily by .github/workflows/update-daily.yml, since the calendar needs a
// token) and my latest public repos live from GitHub's public API.
(function () {
  const USER = "palashpawar";
  const section = document.getElementById("ghSection");
  if (!section) return;
  const snapshot = fetch("data/github.json").then(r => r.json()).catch(() => null);

  const timeAgo = iso => {
    const days = Math.floor((Date.now() - new Date(iso)) / 86400000);
    if (days < 1) return "updated today";
    if (days === 1) return "updated yesterday";
    if (days < 30) return `updated ${days} days ago`;
    const months = Math.floor(days / 30);
    return `updated ${months} month${months === 1 ? "" : "s"} ago`;
  };

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  // One column per week with Sunday on top, like GitHub's own calendar
  function drawCalendar(data) {
    const cal = document.getElementById("ghCalendar");
    const months = document.getElementById("ghMonths");
    const active = data.days.map(d => d[1]).filter(c => c > 0).sort((a, b) => a - b);
    const q = p => (active.length ? active[Math.min(active.length - 1, Math.floor(p * active.length))] : 1);
    const cuts = [q(0.25), q(0.5), q(0.75)];   // quartiles of active days → 4 shades
    const level = c => (c === 0 ? 0 : c <= cuts[0] ? 1 : c <= cuts[1] ? 2 : c <= cuts[2] ? 3 : 4);

    const lead = new Date(data.days[0][0] + "T12:00:00").getDay();
    for (let i = 0; i < lead; i++) cal.append(el("span", "gh-day gh-pad"));   // align the first week
    let lastMonth = -1;
    data.days.forEach(([date, c], i) => {
      const d = new Date(date + "T12:00:00");
      const cell = el("span", `gh-day lv${level(c)}`);
      cell.title = `${c} contribution${c === 1 ? "" : "s"} on ${d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}`;
      cal.append(cell);
      // month label above the first full week of each month
      if (d.getDay() === 0 && d.getDate() <= 7 && d.getMonth() !== lastMonth) {
        const m = el("span", "gh-month", d.toLocaleDateString([], { month: "short" }));
        m.style.gridColumnStart = Math.floor((i + lead) / 7) + 1;
        months.append(m);
        lastMonth = d.getMonth();
      }
    });
    cal.setAttribute("aria-label", `${data.total} GitHub contributions in the last year`);
    document.getElementById("ghTotal").textContent = `${data.total.toLocaleString()} contributions in the last year`;
    const wrap = document.getElementById("ghCalendarWrap");
    wrap.scrollLeft = wrap.scrollWidth;   // narrow screens scroll; start at the most recent weeks
  }

  function drawRepos(repos) {
    document.getElementById("ghRepos").replaceChildren(...repos.slice(0, 6).map(r => {
      const a = el("a", "gh-repo");
      a.href = r.url;
      a.target = "_blank";
      a.rel = "noopener";
      a.append(el("span", "gh-repo-name", r.name), el("span", "gh-repo-desc", r.description || "No description"));
      const meta = el("span", "gh-repo-meta");
      if (r.language) {
        const dot = el("span", "gh-lang-dot");
        dot.style.background = r.color || "#888";
        meta.append(dot, `${r.language} · `);
      }
      meta.append(timeAgo(r.pushedAt));
      a.append(meta);
      return a;
    }));
  }

  // Latest repos live (no token needed); fall back to the daily snapshot
  const live = fetch(`https://api.github.com/users/${USER}/repos?sort=pushed&per_page=20`)
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(list => list.filter(r => !r.fork && !r.private).map(r => ({
      name: r.name, description: r.description, url: r.html_url, pushedAt: r.pushed_at, language: r.language,
    })))
    .catch(() => null);

  Promise.all([snapshot, live]).then(([snap, liveRepos]) => {
    if (!snap && !liveRepos) return;   // nothing to show; the section stays hidden
    section.hidden = false;
    if (snap) drawCalendar(snap);
    else document.getElementById("ghCalendarWrap").hidden = true;
    // the live list has no language colors; borrow them from the snapshot
    const colors = Object.fromEntries((snap?.repos || []).filter(r => r.language).map(r => [r.language, r.color]));
    drawRepos(liveRepos ? liveRepos.map(r => ({ ...r, color: colors[r.language] || null })) : snap.repos);
  });
})();
