/* ===========================================================================
   OnPoint — AI Price Agent : browser logic
   Sends the user's input to POST /api/compare and renders the comparison.
   =========================================================================== */
(function () {
  "use strict";

  var qEl = document.getElementById("q");
  var goEl = document.getElementById("go");
  var loadingEl = document.getElementById("loading");
  var errorEl = document.getElementById("error");
  var resultsEl = document.getElementById("results");

  /* ---------------- small helpers ---------------- */
  var AVATAR_COLORS = ["#7048e8","#e8590c","#1098ad","#2f9e44","#c2255c","#5f3dc4","#f08c00","#1971c2"];

  function colorFor(name) {
    var s = 0, n = name || "?";
    for (var i = 0; i < n.length; i++) s = (s + n.charCodeAt(i)) % AVATAR_COLORS.length;
    return AVATAR_COLORS[s];
  }
  function rupee(n) {
    return "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
  }
  function intFmt(n) { return Number(n).toLocaleString("en-IN"); }
  function stars(r) {
    if (!r) return "";
    var full = Math.round(r);
    return '<span class="stars">' + "★".repeat(full) + "☆".repeat(5 - full) + "</span> " + r.toFixed(1);
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function show(el) { el.classList.remove("hidden"); }
  function hide(el) { el.classList.add("hidden"); }

  // An avatar that shows the real merchant logo, falling back to a colour
  // tile with the store's initial if the logo fails to load.
  function avatarHtml(name, logoUrl, modifier) {
    var letter = esc((name || "?").charAt(0).toUpperCase());
    var img = logoUrl
      ? '<img src="' + esc(logoUrl) + '" alt="" onerror="this.remove()" />'
      : "";
    return '<div class="avatar ' + (modifier || "") + '" style="background:' +
      colorFor(name) + '">' + letter + img + "</div>";
  }

  /* ---------------- animated loading steps ---------------- */
  var stepTimers = [];

  function runSteps() {
    var steps = loadingEl.querySelectorAll(".lstep");
    steps.forEach(function (s) { s.className = "lstep"; });
    function activate(i) {
      if (i > 0) steps[i - 1].className = "lstep done";
      if (i < steps.length) {
        steps[i].className = "lstep run on";
        stepTimers.push(setTimeout(function () { activate(i + 1); }, i === 0 ? 900 : 1600));
      }
    }
    activate(0);
  }
  function stopSteps() {
    stepTimers.forEach(clearTimeout);
    stepTimers = [];
    loadingEl.querySelectorAll(".lstep").forEach(function (s) { s.className = "lstep done"; });
  }

  /* ---------------- the request ---------------- */
  async function compare() {
    var input = qEl.value.trim();
    if (!input) { qEl.focus(); return; }

    hide(errorEl); hide(resultsEl); show(loadingEl);
    runSteps();
    goEl.disabled = true; goEl.textContent = "Scanning…";

    try {
      var res = await fetch("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: input })
      });
      var data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong.");
      stopSteps();
      setTimeout(function () { hide(loadingEl); render(data); }, 350);
    } catch (e) {
      stopSteps(); hide(loadingEl);
      errorEl.textContent = "⚠️  " + (e.message || "Could not compare prices. Try again.");
      show(errorEl);
    } finally {
      goEl.disabled = false; goEl.textContent = "Compare Prices";
    }
  }

  /* ---------------- rendering ---------------- */

  function rowHtml(r) {
    var bestTag = r.is_best ? '<span class="tag-best">BEST PRICE</span>' : "";
    var earn = r.onpoints
      ? '<div class="earn-line">◆ Earn ' + r.onpoints +
        ' onpoints with OnPoint <span class="rate">· ' + r.cashback_rate + '% back</span></div>'
      : "";
    var rating = r.rating
      ? "<small>" + stars(r.rating) +
        (r.reviews ? " · " + intFmt(r.reviews) + " reviews" : "") + "</small>"
      : "";
    var deliv = r.delivery ? '<small class="deliv">🚚 ' + esc(r.delivery) + "</small>" : "";
    return (
      '<div class="row' + (r.is_best ? " best" : "") + '">' +
        avatarHtml(r.platform, r.logo_url) +
        '<div class="info">' +
          "<b>" + esc(r.platform) + " " + bestTag + "</b>" +
          earn + rating + deliv +
        "</div>" +
        '<div class="price-col">' +
          '<div class="amt">' + rupee(r.price_value) + "</div>" +
          '<a class="btn-buy" href="' + esc(r.link) + '" target="_blank" rel="noopener">Buy →</a>' +
        "</div>" +
      "</div>"
    );
  }

  // "You came from here" — the retailer behind the pasted URL. When that store
  // is itself an OnPoint partner, its cashback is shown even if it never turned
  // up in the price-search results.
  function renderOrigin(origin) {
    var el = document.getElementById("origin");
    if (!origin) { el.innerHTML = ""; return; }
    var price = origin.price
      ? '<div class="origin-price">' + rupee(origin.price) + "</div>"
      : '<div class="origin-price na">price n/a</div>';
    var earn = "";
    if (origin.is_onpoint_partner && origin.cashback_rate > 0) {
      earn = origin.onpoints
        ? '<div class="earn-line">◆ Earn ' + origin.onpoints +
          ' onpoints with OnPoint <span class="rate">· ' + origin.cashback_rate + '% back</span></div>'
        : '<div class="earn-line">◆ Earn ' + origin.cashback_rate + '% back with OnPoint</div>';
    }
    el.innerHTML =
      '<div class="origin-card">' +
        '<div class="origin-tag">📍 You came from here</div>' +
        '<div class="origin-row">' +
          avatarHtml(origin.store, origin.logo_url, "sm") +
          '<div class="origin-info"><b>' + esc(origin.store) + "</b>" + earn + "</div>" +
          price +
        "</div>" +
      "</div>";
  }

  // Shown when a pasted product link resolved fine, but the exact product
  // isn't sold at any other store. Keeps the "You came from here" origin
  // card (and its OnPoint cashback); replaces the rest with a calm note.
  function renderNotAvailable(data) {
    var p = data.product || {};
    var img = p.thumbnail
      ? '<img src="' + esc(p.thumbnail) + '" alt="" onerror="this.style.display=\'none\'" />'
      : "";
    document.getElementById("summary").innerHTML =
      img +
      '<div class="meta">' +
        "<b>" + esc(p.title || data.query) + "</b>" +
        '<span class="via">Identified from the product URL</span>' +
      "</div>";

    renderOrigin(data.origin);

    var store = esc((data.origin && data.origin.store) || "the original store");
    var bestEl = document.getElementById("best");
    bestEl.className = "best-banner not-found";
    bestEl.innerHTML =
      '<svg width="26" height="26" viewBox="0 0 24 24" fill="none">' +
        '<circle cx="12" cy="12" r="9" stroke="#f0a830" stroke-width="2"/>' +
        '<path d="M12 7.5v6M12 16.4v.2" stroke="#f0a830" stroke-width="2.4" stroke-linecap="round"/>' +
      "</svg>" +
      "<div><div class='big'>Not available at other stores</div>" +
      "<small>The agent checked, but couldn't find this exact product anywhere " +
      "else — it looks like " + store + " is the only store carrying it.</small></div>";

    document.getElementById("onpoint-section").innerHTML = "";
    document.getElementById("recommended-section").innerHTML = "";
    document.getElementById("other-section").innerHTML = "";
    document.getElementById("note").textContent = "";

    hide(errorEl);
    show(resultsEl);
  }

  function sectionHtml(containerId, title, subtitle, offers) {
    var el = document.getElementById(containerId);
    if (!offers.length) { el.innerHTML = ""; return; }
    el.innerHTML =
      '<div class="section-head"><h3>' + title + "</h3><span>" + subtitle + "</span></div>" +
      '<div class="rows">' +
        offers.map(function (r) { return rowHtml(r); }).join("") +
      "</div>";
  }

  function render(data) {
    var results = data.results || [];
    if (!results.length) {
      // A pasted brand-store link that no other store carries — a real
      // answer, not an error. Keep the origin card, drop the comparison.
      if (data.not_available && data.origin) { renderNotAvailable(data); return; }
      errorEl.textContent = "⚠️  No stores found for “" + data.query + "”. Try a more specific name.";
      show(errorEl);
      return;
    }

    // --- product summary ---
    var p = data.product || {};
    var img = p.thumbnail
      ? '<img src="' + esc(p.thumbnail) + '" alt="" onerror="this.style.display=\'none\'" />'
      : "";
    var viaText = {
      "page-title": "Identified from the link you pasted",
      "url-slug": "Identified from the product URL",
      "search-term": "Searched by name"
    }[data.resolved_via] || "Product identified";
    document.getElementById("summary").innerHTML =
      img +
      '<div class="meta">' +
        "<b>" + esc(p.title || data.query) + "</b>" +
        "<small>Compared across " + results.length + " stores · prices in INR</small>" +
        '<span class="via">' + esc(viaText) + "</span>" +
      "</div>";

    // --- "you came from here" anchor ---
    renderOrigin(data.origin);

    // --- cheapest banner ---
    var best = data.best || results[0];
    var bestEl = document.getElementById("best");
    bestEl.className = "best-banner";   // reset (a prior render may have set not-found)
    bestEl.innerHTML =
      '<svg width="30" height="30" viewBox="0 0 24 24" fill="none"><path d="m12 2 3 6 6 1-4.5 4.3L17.5 20 12 16.8 6.5 20l1-6.7L3 9l6-1 3-6Z" fill="#51cf66"/></svg>' +
      "<div><div class='big'>Lowest price: <span>" + rupee(best.price_value) + "</span> at " + esc(best.platform) + "</div>" +
      "<small>Best of " + results.length + " stores the agent checked</small></div>";

    // --- "Earn with OnPoint" section: partner stores pinned on top ---
    var partners = results
      .filter(function (r) { return r.onpoints > 0; })
      .sort(function (a, b) { return b.onpoints - a.onpoints; });
    var opEl = document.getElementById("onpoint-section");
    if (partners.length) {
      opEl.innerHTML =
        '<div class="section-head">' +
          '<h3><span class="gem">◆</span> Earn with OnPoint</h3>' +
          "<span>Shop via OnPoint at these stores — earn up to " +
            partners[0].onpoints + " onpoints on this product</span>" +
        "</div>" +
        '<div class="onpoint-zone">' +
          partners.map(function (r) { return rowHtml(r); }).join("") +
        "</div>";
    } else {
      opEl.innerHTML =
        '<div class="section-head"><h3><span class="gem">◆</span> Earn with OnPoint</h3></div>' +
        '<div class="onpoint-zone"><div class="onpoint-empty">' +
          "None of the retailers carrying this product are OnPoint partner stores, " +
          "so no onpoints apply here. Onpoints are earned at Amazon, Myntra, Ajio, " +
          "Adidas, H&amp;M, Uniqlo, Forest Essentials, Sugar Cosmetics &amp; Mokobara." +
        "</div></div>";
    }

    // --- trust-tiered retailer lists ---
    var recommended = results.filter(function (r) { return r.is_recommended; });
    var other = results.filter(function (r) { return !r.is_recommended; });
    sectionHtml(
      "recommended-section", "Recommended retailers",
      recommended.length + " trusted stores · lowest price first",
      recommended
    );
    sectionHtml(
      "other-section", "Other stores",
      other.length + " more · lowest price first",
      other
    );

    document.getElementById("note").textContent =
      data.data_source === "mock"
        ? "Showing demo data — add a SerpAPI key in server/.env for live prices."
        : "Live prices via Google Shopping · onpoints from OnPoint's live cashback rates.";

    show(resultsEl);
    resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ---------------- wire up events ---------------- */
  goEl.addEventListener("click", compare);
  qEl.addEventListener("keydown", function (e) { if (e.key === "Enter") compare(); });
  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      qEl.value = chip.getAttribute("data-q");
      compare();
    });
  });
})();
