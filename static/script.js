/* TOUCH GRASS - client logic */
(function () {
  "use strict";

  var PHASES = [
    "TRIANGULATING...",
    "CALIBRATING...",
    "SYNTHESIZING...",
    "INTERPOLATING...",
    "EXTRAPOLATING...",
    "AGGREGATING...",
  ];

  var dz = document.getElementById("dropzone");
  var fileInput = document.getElementById("file");
  var loading = document.getElementById("loading");
  var loadText = document.getElementById("load-text");
  var bar = document.getElementById("progress-bar");
  var errorBox = document.getElementById("error");
  var results = document.getElementById("results");
  var again = document.getElementById("again");

  document.getElementById("year").textContent = new Date().getFullYear();

  /* ------------------------------------------------------------------ */
  /*  8-BIT SOUND (Web Audio, no files needed)                          */
  /* ------------------------------------------------------------------ */
  function ac() {
    if (!window.__ac) {
      window.__ac = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (window.__ac.state === "suspended") window.__ac.resume();
    return window.__ac;
  }

  function tone(freq, when, dur, type, vol) {
    var c = ac(),
      o = c.createOscillator(),
      g = c.createGain();
    o.type = type || "square";
    o.frequency.value = freq;
    o.connect(g);
    g.connect(c.destination);
    var t0 = c.currentTime + when;
    g.gain.setValueAtTime(vol || 0.1, t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.start(t0);
    o.stop(t0 + dur + 0.03);
  }

  /* little retro game-start jingle */
  function playOpenJingle() {
    var seq = [523, 659, 784, 1047, 784, 1047, 1319];
    seq.forEach(function (f, i) {
      var last = i === seq.length - 1;
      tone(f, i * 0.11, last ? 0.55 : 0.13, "square", last ? 0.16 : 0.09);
    });
    tone(262, 0.77, 0.6, "triangle", 0.1);
  }

  /* mechanical grinding noise while the leaf is being processed */
  var procTimer = null,
    procTick = 0;
  function startProcessing() {
    stopProcessing();
    procTick = 0;
    procTimer = setInterval(function () {
      tone(190 + Math.random() * 70, 0, 0.06, "square", 0.045);
      if (procTick % 4 === 3) {
        tone(85, 0, 0.1, "sawtooth", 0.06); /* heavy clunk */
      }
      if (procTick % 5 === 2) {
        tone(420 + Math.random() * 80, 0, 0.03, "square", 0.03); /* tick */
      }
      procTick++;
    }, 130);
  }
  function stopProcessing() {
    if (procTimer) {
      clearInterval(procTimer);
      procTimer = null;
    }
  }

  /* play on load; retry on first user gesture (autoplay lock) */
  var played = false;
  function tryPlay() {
    if (played) return;
    played = true;
    try {
      playOpenJingle();
    } catch (e) {}
  }
  window.addEventListener("load", tryPlay);
  document.addEventListener("pointerdown", tryPlay);
  document.addEventListener("keydown", tryPlay);

  /* ------------------------------------------------------------------ */
  /*  LOADING SEQUENCE                                                   */
  /* ------------------------------------------------------------------ */
  function showLoading() {
    dz.hidden = true;
    errorBox.hidden = true;
    errorBox.textContent = "";
    results.hidden = true;
    loading.hidden = false;
    loadText.textContent = PHASES[0];
    bar.style.width = "5%";
    var i = 0;
    window._phaseTimer = setInterval(function () {
      i = (i + 1) % PHASES.length;
      loadText.textContent = PHASES[i];
      bar.style.width = Math.min(90, 8 + (i / PHASES.length) * 82) + "%";
    }, 850);
    startProcessing();
  }

  function hideLoading() {
    clearInterval(window._phaseTimer);
    stopProcessing();
    loading.hidden = true;
    dz.hidden = false;
  }

  function showError(msg) {
    hideLoading();
    errorBox.hidden = false;
    errorBox.textContent = "!! " + (msg || "Oops, something went wrong.");
  }

  function upload(file) {
    showLoading();

    var data = new FormData();
    data.append("file", file);

    fetch("/analyze", { method: "POST", body: data })
      .then(function (resp) {
        return resp.json().then(function (body) {
          return { ok: resp.ok, body: body };
        });
      })
      .then(function (res) {
        hideLoading();
        tone(784, 0, 0.12, "square", 0.1); /* ding */
        tone(1319, 0.13, 0.35, "square", 0.12);
        if (!res.ok) {
          showError(res.body.error);
          return;
        }
        render(res.body);
      })
      .catch(function (err) {
        showError("Network error: " + err.message);
      });
  }

  /* ------------------------------------------------------------------ */
  /*  LIGHTBOX (click any stage photo)                                   */
  /* ------------------------------------------------------------------ */
  function buildLightbox() {
    var ids = ["img-original", "img-skeleton", "img-overlay", "img-clean"];
    var caps = ["ORIGINAL LEAF", "SKELETON", "GRAPH OVERLAY", "CLEAN GRAPH"];
    var el = ids.map(function (id) { return document.getElementById(id); });

    var ov = document.createElement("div");
    ov.className = "lightbox";
    ov.innerHTML =
      '<button class="lb-close" aria-label="close">X</button>' +
      '<button class="lb-nav lb-prev" aria-label="previous">&lt;</button>' +
      '<figure><img alt=""><figcaption></figcaption></figure>' +
      '<button class="lb-next lb-nav" aria-label="next">&gt;</button>';
    document.body.appendChild(ov);

    var img = ov.querySelector("img"),
      cap = ov.querySelector("figcaption");
    var cur = 0;

    function show(i) {
      cur = (i + el.length) % el.length;
      img.src = el[cur].src;
      cap.textContent = caps[cur];
    }
    function open(i) {
      show(i);
      ov.classList.add("open");
    }
    function close() {
      ov.classList.remove("open");
    }

    el.forEach(function (thumb, i) {
      thumb.style.cursor = "zoom-in";
      thumb.addEventListener("click", function () { open(i); });
    });

    ov.addEventListener("click", function (e) {
      if (e.target === ov || e.target.classList.contains("lb-close")) close();
    });
    ov.querySelector(".lb-prev").addEventListener("click", function (e) {
      e.stopPropagation();
      show(cur - 1);
    });
    ov.querySelector(".lb-next").addEventListener("click", function (e) {
      e.stopPropagation();
      show(cur + 1);
    });
    document.addEventListener("keydown", function (e) {
      if (!ov.classList.contains("open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") show(cur - 1);
      if (e.key === "ArrowRight") show(cur + 1);
    });
  }

  /* ------------------------------------------------------------------ */
  /*  RENDER RESULTS                                                     */
  /* ------------------------------------------------------------------ */
  function render(body) {
    var imgs = body.images, s = body.stats;

    document.getElementById("img-original").src = imgs.original;
    document.getElementById("img-skeleton").src = imgs.skeleton;
    document.getElementById("img-overlay").src = imgs.overlay;
    document.getElementById("img-clean").src = imgs.clean;

    document.getElementById("stat-N").textContent = s.N;
    document.getElementById("stat-E").textContent = s.E;
    document.getElementById("stat-C").textContent = s.C;
    document.getElementById("stat-mu").textContent = s.mu;
    document.getElementById("stat-L").textContent = s.L;
    document.getElementById("stat-R").textContent = s.R;

    var steps = document.getElementById("steps");
    steps.innerHTML = "";
    body.steps.forEach(function (step) {
      var li = document.createElement("li");
      li.innerHTML = step[0] + " <span>" + step[1] + "</span>";
      steps.appendChild(li);
    });

    renderVideo(body.video);

    var filename = fileInput.files[0] && fileInput.files[0].name;
    var meta = document.getElementById("video-meta");
    meta.textContent = "analyzed in " + body.elapsed + "s" +
      (filename ? " from " + filename : "") +
      " | R = " + s.R +
      " | method " + s.method + " thr " + s.threshold +
      " | connectivity " + (s.connectivity * 100).toFixed(1) + "%";

    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderVideo(v) {
    var vb = document.getElementById("video-body");
    vb.classList.remove("ready");
    vb.innerHTML = "";

    if (v.mode === "embed") {
      var ifr = document.createElement("iframe");
      ifr.className = "video-frame";
      ifr.src = v.embed + "?rel=0";
      ifr.allowFullscreen = true;
      ifr.setAttribute("allow",
        "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture");
      vb.appendChild(ifr);

      var link = document.createElement("a");
      link.href = v.watch;
      link.target = "_blank";
      link.textContent = '"' + v.title + '" - ' + v.channel;
      vb.appendChild(link);
      link.style.display = "block";
      link.style.marginTop = "12px";
      link.style.fontSize = "9px";
      link.style.color = "var(--lime)";
      vb.classList.add("ready");
    } else {
      var hint = document.createElement("div");
      hint.className = "video-hint";
      var p = document.createElement("p");
      p.textContent = v.error || "Searching long nature videos...";
      hint.appendChild(p);
      var a = document.createElement("a");
      a.className = "pix-link";
      a.href = v.search_url;
      a.target = "_blank";
      a.textContent = "OPEN YOUTUBE: " + v.query;
      hint.appendChild(a);
      vb.appendChild(hint);
      vb.classList.add("ready");
    }
  }

  /* ------------------------------------------------------------------ */
  /*  EVENTS                                                             */
  /* ------------------------------------------------------------------ */
  buildLightbox();

  dz.addEventListener("click", function () { fileInput.click(); });
  ["dragover", "drop"].forEach(function (evt) {
    dz.addEventListener(evt, function (e) {
      e.preventDefault();
    });
  });
  dz.addEventListener("dragover", function () {
    dz.classList.add("dragover");
  });
  dz.addEventListener("dragleave", function () {
    dz.classList.remove("dragover");
  });
  dz.addEventListener("drop", function (e) {
    dz.classList.remove("dragover");
    if (e.dataTransfer.files.length) upload(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", function () {
    if (fileInput.files.length) upload(fileInput.files[0]);
  });
  again.addEventListener("click", function () {
    results.hidden = true;
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
})();