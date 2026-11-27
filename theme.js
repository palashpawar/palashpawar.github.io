// Dark by default; the top-right button switches to light and remembers the choice.
// data-theme="dark" stays on for the layout rules; data-mode picks the colours.
(function () {
  var root = document.documentElement;
  root.setAttribute("data-theme", "dark");
  var saved = null;
  try { saved = localStorage.getItem("mode"); } catch (e) {}
  root.setAttribute("data-mode", saved === "light" ? "light" : "dark");

  var sun = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var moon = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';

  // images with a light-background version carry it in data-light
  function swapImages() {
    var light = root.getAttribute("data-mode") === "light";
    document.querySelectorAll("img[data-light]").forEach(function (img) {
      if (!img.dataset.dark) img.dataset.dark = img.getAttribute("src");
      img.src = light ? img.dataset.light : img.dataset.dark;
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.createElement("button");
    btn.className = "theme-toggle";
    btn.type = "button";
    function render() {
      var dark = root.getAttribute("data-mode") === "dark";
      btn.innerHTML = dark ? sun : moon;
      btn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    }
    btn.addEventListener("click", function () {
      var next = root.getAttribute("data-mode") === "dark" ? "light" : "dark";
      root.setAttribute("data-mode", next);
      try { localStorage.setItem("mode", next); } catch (e) {}
      render();
      swapImages();
      document.dispatchEvent(new Event("modechange"));
    });
    render();
    swapImages();
    document.body.appendChild(btn);
  });
})();
