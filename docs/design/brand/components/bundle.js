/* @ds-bundle: {"format":4,"namespace":"GaugePrep","components":[{"name":"Button"},{"name":"LevelBadge"},{"name":"ScoreGauge"}]} */
(function () {
  var R = window.React, h = R.createElement;
  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(" "); }

  function Button(p) {
    var variant = p.variant || "primary", size = p.size || "md";
    var rest = Object.assign({}, p); delete rest.variant; delete rest.size; delete rest.className;
    return h("button", Object.assign({ type: "button" }, rest, { className: cx("gp-btn", "gp-btn-" + variant, "gp-btn-" + size, p.className) }), p.children);
  }

  function LevelBadge(p) {
    var tone = p.tone || "neutral";
    return h("span", { className: cx("gp-badge", "gp-badge-" + tone, p.className) },
      h("span", { className: "gp-badge-level" }, p.level),
      p.label ? h("span", { className: "gp-badge-label" }, p.label) : null);
  }

  function pt(cx0, cy0, r, deg) { var a = deg * Math.PI / 180; return [cx0 + r * Math.cos(a), cy0 - r * Math.sin(a)]; }
  function sector(c, r0, r1, a0, a1) {
    var p = pt(c[0], c[1], r0, a1), q = pt(c[0], c[1], r1, a1), s = pt(c[0], c[1], r1, a0), t = pt(c[0], c[1], r0, a0);
    var f = function (v) { return v.toFixed(2); };
    return "M" + f(p[0]) + " " + f(p[1]) + " L" + f(q[0]) + " " + f(q[1]) +
      " A" + r1 + " " + r1 + " 0 0 1 " + f(s[0]) + " " + f(s[1]) +
      " L" + f(t[0]) + " " + f(t[1]) + " A" + r0 + " " + r0 + " 0 0 0 " + f(p[0]) + " " + f(p[1]) + " Z";
  }
  var RAMP = ["var(--sea)", "var(--lagoon)", "var(--mist)"];

  function ScoreGauge(p) {
    var levels = p.levels || ["A1", "A2", "B1", "B2", "C1", "C2"];
    var n = levels.length, reading = Math.max(0, Math.min(n - 1, p.reading == null ? 0 : p.reading));
    var c = [120, 112], from = 162, to = 18, gap = n > 8 ? 2 : 3, step = (from - to) / n;
    var pages = levels.map(function (lv, i) {
      var a1 = from - i * step - gap / 2, a0 = a1 - step + gap;
      var fill = i < reading ? RAMP[Math.min(2, Math.floor(i * 3 / Math.max(1, reading)))] : i === reading ? "var(--amber)" : "var(--unreached)";
      return h("path", { key: lv, d: sector(c, 20, i === reading ? 98 : 82, a0, a1), fill: fill });
    });
    return h("figure", { className: cx("gp-gauge", p.className), role: "img", "aria-label": (p.label || "Estimated level") + ": " + (p.value || levels[reading]) + (p.caption ? ". " + p.caption : "") },
      h("svg", { viewBox: "0 0 240 124", "aria-hidden": "true", className: "gp-gauge-dial" }, pages),
      h("figcaption", { className: "gp-gauge-text" },
        h("span", { className: "gp-gauge-label" }, p.label || "Estimated level"),
        h("span", { className: "gp-gauge-value" }, p.value || levels[reading]),
        p.caption ? h("span", { className: "gp-gauge-caption" }, p.caption) : null));
  }

  window.GaugePrep = Object.assign(window.GaugePrep || {}, { Button: Button, LevelBadge: LevelBadge, ScoreGauge: ScoreGauge });
})();
