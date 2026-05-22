/* ===========================================================================
   OnPoint — Store Locator : browser logic
   Pick a brand + city, ask for GPS, POST /api/stores, render ranked outlets.
   =========================================================================== */
(function () {
  "use strict";

  var brandEl = document.getElementById("brand");
  var cityEl = document.getElementById("city");
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
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function stars(r) {
    if (!r) return "";
    var full = Math.round(r);
    return '<span class="stars">' + "★".repeat(full) + "☆".repeat(5 - full) + "</span> " + r.toFixed(1);
  }
  function avatarHtml(name) {
    var letter = esc((name || "?").charAt(0).toUpperCase());
    return '<div class="avatar" style="background:' + colorFor(name) + '">' + letter + "</div>";
  }
  function show(el) { el.classList.remove("hidden"); }
  function hide(el) { el.classList.add("hidden"); }

  /* ---------------- populate the brand dropdown ---------------- */
  async function loadBrands() {
    try {
      var res = await fetch("/api/brands");
      var data = await res.json();
      (data.brands || []).forEach(function (name) {
        var opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        brandEl.appendChild(opt);
      });
    } catch (e) {
      /* leave the placeholder option — the page still works if typed */
    }
  }

  /* ---------------- browser geolocation (best-effort) ---------------- */
  function getLocation() {
    return new Promise(function (resolve) {
      if (!navigator.geolocation) { resolve(null); return; }
      navigator.geolocation.getCurrentPosition(
        function (pos) { resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }); },
        function () { resolve(null); },               // denied / unavailable
        { timeout: 8000, maximumAge: 300000 }
      );
    });
  }

  /* ---------------- the request ---------------- */
  async function findStores() {
    var brand = brandEl.value;
    var city = cityEl.value.trim();
    if (!brand) { brandEl.focus(); return; }
    if (!city) { cityEl.focus(); return; }

    hide(errorEl); hide(resultsEl); show(loadingEl);
    goEl.disabled = true; goEl.textContent = "Searching…";

    try {
      var loc = await getLocation();                  // null if the user declines
      var body = { brand: brand, city: city };
      if (loc) { body.lat = loc.lat; body.lng = loc.lng; }

      var res = await fetch("/api/stores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      var data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong.");
      hide(loadingEl);
      render(data);
    } catch (e) {
      hide(loadingEl);
      errorEl.textContent = "⚠️  " + (e.message || "Couldn't find stores. Try again.");
      show(errorEl);
    } finally {
      goEl.disabled = false; goEl.textContent = "Find Stores";
    }
  }

  /* ---------------- rendering ---------------- */
  function storeRow(s) {
    var dist = s.distance_km != null ? s.distance_km + " km away" : "";
    var open =
      s.open_now === true ? '<span class="open-badge">OPEN NOW</span>'
      : s.open_now === false ? '<span class="closed-badge">CLOSED</span>'
      : "";
    var rating = s.rating ? stars(s.rating) : "";
    var bits = [rating, open].filter(Boolean).join(" &nbsp;·&nbsp; ");
    var directions = "https://www.google.com/maps/dir/?api=1&destination=" +
      encodeURIComponent(s.lat + "," + s.lng);
    return (
      '<div class="row">' +
        avatarHtml(s.brand) +
        '<div class="info">' +
          "<b>" + esc(s.name) + "</b>" +
          "<small>" + esc(s.address) + "</small>" +
          (bits ? "<small>" + bits + "</small>" : "") +
        "</div>" +
        '<div class="price-col">' +
          '<div class="distance">' + esc(dist) + "</div>" +
          '<a class="btn-buy" href="' + directions + '" target="_blank" rel="noopener">Directions →</a>' +
        "</div>" +
      "</div>"
    );
  }

  function render(data) {
    var stores = data.stores || [];
    if (!stores.length) {
      errorEl.textContent = "⚠️  No " + data.brand + " outlets found in " +
        data.city + ". Try another city.";
      show(errorEl);
      return;
    }

    // earn-rate banner — shown once, just below the search bar
    document.getElementById("earn-banner").innerHTML =
      "◆ Earn " + data.earn_rate + "% onpoints" +
      '<span class="earn-sub">on every ' + esc(data.brand) +
      " purchase made through OnPoint</span>";

    document.getElementById("ref-note").innerHTML =
      data.reference_source === "gps"
        ? "📍 Distances measured from your current location"
        : "📍 Distances measured from " + esc(data.city) +
          " centre — allow location access for exact distances";

    document.getElementById("store-head").innerHTML =
      "<h3>" + esc(data.brand) + " in " + esc(data.city) + "</h3>" +
      "<span>" + data.store_count + " outlet" +
      (data.store_count === 1 ? "" : "s") + " · nearest first</span>";

    document.getElementById("store-rows").innerHTML = stores.map(storeRow).join("");

    document.getElementById("note").textContent =
      data.data_source === "mock"
        ? "Showing demo data — add GOOGLE_PLACES_API_KEY in server/.env for live store data."
        : "Live store data via Google Places.";

    show(resultsEl);
    resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ---------------- wire up ---------------- */
  goEl.addEventListener("click", findStores);
  cityEl.addEventListener("keydown", function (e) { if (e.key === "Enter") findStores(); });
  loadBrands();
})();
