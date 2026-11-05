/* HTU 档案库 · 档案资源管理平台 —— 前端 SPA */
(function () {
  "use strict";

  var app = document.getElementById("app");

  /* ---------------- 工具 ---------------- */

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fmtSize(n) {
    if (n == null) return "-";
    return n < 1024 ? n + " B" : (n / 1024).toFixed(1) + " KB";
  }

  async function api(path, options) {
    var opts = Object.assign({ credentials: "same-origin", headers: {} }, options || {});
    if (opts.body && typeof opts.body !== "string") {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    var res = await fetch(path, opts);
    var data = null;
    try { data = await res.json(); } catch (e) { /* 非 JSON 响应 */ }
    if (!res.ok) {
      var err = new Error((data && data.error) || ("请求失败（" + res.status + "）"));
      err.status = res.status;
      throw err;
    }
    return data;
  }

  function toast(msg, type) {
    var wrap = document.getElementById("toastWrap");
    var el = document.createElement("div");
    el.className = "toast" + (type ? " " + type : "");
    el.textContent = msg;
    wrap.appendChild(el);
    setTimeout(function () { el.style.opacity = "0"; el.style.transition = "opacity .3s"; }, 2600);
    setTimeout(function () { el.remove(); }, 3000);
  }

  /* ---------------- SVG 图标 ---------------- */

  var I = {
    dashboard: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1.5" y="1.5" width="5.2" height="5.2" rx="1.3"/><rect x="9.3" y="1.5" width="5.2" height="5.2" rx="1.3"/><rect x="1.5" y="9.3" width="5.2" height="5.2" rx="1.3"/><rect x="9.3" y="9.3" width="5.2" height="5.2" rx="1.3"/></svg>',
    profile: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="5.4" r="2.9"/><path d="M2.6 14.2c0-2.7 2.4-4.4 5.4-4.4s5.4 1.7 5.4 4.4"/></svg>',
    reports: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="2.8" y="1.8" width="10.4" height="12.4" rx="1.6"/><path d="M5.6 5.6h4.8M5.6 8h4.8M5.6 10.4h3"/></svg>',
    bell: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 1.8a4.3 4.3 0 0 0-4.3 4.3v2.6L2.6 11h10.8l-1.1-2.3V6.1A4.3 4.3 0 0 0 8 1.8Z"/><path d="M6.4 13.2a1.7 1.7 0 0 0 3.2 0"/></svg>',
    shield: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M8 1.6 13.4 3.8v4c0 3.2-2.2 5.4-5.4 6.6-3.2-1.2-5.4-3.4-5.4-6.6v-4L8 1.6Z"/></svg>',
    download: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v8.2M4.4 7.4 8 11l3.6-3.6M2.5 13.5h11"/></svg>',
    logout: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2H3.2A1.2 1.2 0 0 0 2 3.2v9.6A1.2 1.2 0 0 0 3.2 14H6M10.5 11 13.5 8l-3-3M13.5 8H6.5"/></svg>',
    lock: '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="10.5" width="16" height="10" rx="2.4"/><path d="M8 10.5V7.6a4 4 0 0 1 8 0v2.9"/><circle cx="12" cy="15.4" r="1.4"/></svg>',
    file: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9.2 1.8H4.6a1 1 0 0 0-1 1v10.4a1 1 0 0 0 1 1h6.8a1 1 0 0 0 1-1V5.4L9.2 1.8Z"/><path d="M9.2 1.8v3.6h3.2"/></svg>',
    arrow: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10M9.5 4.5 13 8l-3.5 3.5"/></svg>',
    user: '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="5.4" r="2.9"/><path d="M2.6 14.2c0-2.7 2.4-4.4 5.4-4.4s5.4 1.7 5.4 4.4"/></svg>',
    check: '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2.8 8.6 6.2 12 13.2 4.4"/></svg>'
  };

  /* ---------------- 状态与路由 ---------------- */

  var me = null;

  // 管理入口仅对管理员渲染；路由与接口路径仍写在前端代码里（前端隐藏 ≠ 安全）
  var NAV_ITEMS = [
    { path: "/dashboard", label: "仪表盘", icon: "dashboard" },
    { path: "/profile", label: "档案中心", icon: "profile" },
    { path: "/reports", label: "档案检索", icon: "reports" },
    { path: "/notifications", label: "消息通知", icon: "bell" },
    { path: "/admin", label: "系统管理", icon: "shield", adminOnly: true }
  ];

  var TITLES = {
    "/dashboard": "仪表盘",
    "/profile": "档案中心",
    "/reports": "档案检索",
    "/notifications": "消息通知",
    "/admin": "系统管理"
  };

  function initial() {
    return ((me && (me.nickname || me.username)) || "?").slice(0, 1);
  }

  async function boot() {
    try {
      var r = await api("/api/me");
      me = r.user;
    } catch (e) {
      me = null;
    }
    route();
  }

  function nav(path) {
    history.pushState(null, "", path);
    route();
  }

  window.addEventListener("popstate", route);

  function route() {
    var path = location.pathname;
    if (path === "/login") { renderAuth("login"); return; }
    if (!me) { history.replaceState(null, "", "/login"); renderAuth("login"); return; }
    if (path === "/" || !TITLES[path]) {
      history.replaceState(null, "", "/dashboard");
      path = "/dashboard";
    }
    renderShell(path);
  }

  /* ---------------- 控制台骨架 ---------------- */

  function renderShell(path) {
    var isAdmin = me && me.role === "admin";
    var navHtml = NAV_ITEMS
      .filter(function (item) { return !item.adminOnly || isAdmin; })
      .map(function (item) {
        return '<div class="nav-item' + (item.path === path ? " active" : "") + '" data-nav="' + item.path + '">' +
          I[item.icon] + '<span>' + item.label + '</span>' +
          (item.adminOnly ? '<i class="tag">ADMIN</i>' : "") + '</div>';
      }).join("");

    app.innerHTML =
      '<div class="layout">' +
        '<aside class="sidebar">' +
          '<div class="side-brand">' +
            '<div class="brand-mark">H</div>' +
            '<div><div class="side-brand-name">HTU 档案库</div><div class="side-brand-sub">档案资源管理平台</div></div>' +
          '</div>' +
          '<div class="nav-label">功能</div>' +
          '<nav>' + navHtml + '</nav>' +
          '<div class="side-spacer"></div>' +
          '<div class="side-user">' +
            '<div class="avatar">' + esc(initial()) + '</div>' +
            '<div class="side-user-meta">' +
              '<div class="side-user-name">' + esc(me.nickname || me.username) + '</div>' +
              '<div class="side-user-role">' + (isAdmin ? "管理员" : "普通用户") + '</div>' +
            '</div>' +
            '<button class="side-logout" id="logoutBtn" title="退出登录">' + I.logout + '</button>' +
          '</div>' +
        '</aside>' +
        '<div class="main">' +
          '<header class="topbar">' +
            '<h1>' + (TITLES[path] || "") + '</h1>' +
            '<div class="topbar-right">' +
              '<span class="badge ' + (isAdmin ? "badge-admin" : "badge-user") + '">' + (isAdmin ? "管理员" : "普通用户") + '</span>' +
              '<div class="topbar-user"><div class="avatar">' + esc(initial()) + '</div><span class="name">' + esc(me.username) + '</span></div>' +
            '</div>' +
          '</header>' +
          '<main class="content" id="content"></main>' +
        '</div>' +
      '</div>';

    Array.prototype.forEach.call(app.querySelectorAll("[data-nav]"), function (el) {
      el.addEventListener("click", function () { nav(el.getAttribute("data-nav")); });
    });
    document.getElementById("logoutBtn").addEventListener("click", doLogout);

    var view = {
      "/dashboard": viewDashboard,
      "/profile": viewProfile,
      "/reports": viewReports,
      "/notifications": viewNotifications,
      "/admin": viewAdmin
    }[path] || viewDashboard;
    view();
  }

  async function doLogout() {
    try { await api("/api/logout", { method: "POST" }); } catch (e) { /* 忽略 */ }
    me = null;
    toast("已退出登录");
    nav("/login");
  }

  /* ---------------- 仪表盘 ---------------- */

  function statCard(icon, label, value, unit, foot) {
    return '<div class="stat">' +
      '<div class="label">' + I[icon] + esc(label) + '</div>' +
      '<div class="value">' + esc(value) + (unit ? '<span class="unit">' + unit + '</span>' : "") + '</div>' +
      '<div class="delta">' + esc(foot) + '</div>' +
    '</div>';
  }

  function quickItem(icon, path, name) {
    return '<div class="quick-item" data-nav="' + path + '">' +
      '<div class="q-icon">' + I[icon] + '</div>' +
      '<div class="q-name">' + esc(name) + '</div>' +
      '<span class="q-arrow">' + I.arrow + '</span>' +
    '</div>';
  }

  async function viewDashboard() {
    var c = document.getElementById("content");
    var hour = new Date().getHours();
    var greet = hour < 6 ? "凌晨好" : hour < 12 ? "上午好" : hour < 14 ? "中午好" : hour < 18 ? "下午好" : "晚上好";
    var today = new Date();
    var dateStr = today.getFullYear() + " 年 " + (today.getMonth() + 1) + " 月 " + today.getDate() + " 日";
    var isAdmin = me.role === "admin";

    c.innerHTML =
      '<div class="banner">' +
        '<div>' +
          '<h2>' + greet + '，' + esc(me.nickname || me.username) + '</h2>' +
          '<div class="date">今天是 ' + dateStr + ' · 欢迎使用 HTU 档案库</div>' +
        '</div>' +
        '<span class="badge banner-badge">当前角色：' + (isAdmin ? "管理员" : "普通用户") + '</span>' +
      '</div>' +
      '<div class="stat-grid">' +
        statCard("user", "资料完整度", me.bio ? "100" : "80", "%", me.bio ? "已填写个人签名" : "还差个人签名") +
        statCard("reports", "在库档案", "…", "份", "来自档案检索") +
        statCard("bell", "站内通知", "…", "条", "来自消息通知") +
        statCard("shield", "账号角色", isAdmin ? "admin" : "user", "", "由系统管理员分配") +
      '</div>' +
        '<div class="dash-cols">' +
        '<div class="card">' +
          '<div class="card-title">最近动态</div>' +
          '<div class="act-list" id="actList"><div class="skel" style="height:118px"></div></div>' +
        '</div>' +
        '<div class="card">' +
          '<div class="card-title">快捷入口</div>' +
          '<div class="quick-grid">' +
            quickItem("profile", "/profile", "档案中心") +
            quickItem("reports", "/reports", "档案检索") +
            quickItem("bell", "/notifications", "消息通知") +
            (isAdmin ? quickItem("shield", "/admin", "系统管理") : "") +
          '</div>' +
        '</div>' +
      '</div>';

    // 快捷入口与侧边栏共用同一套跳转逻辑
    Array.prototype.forEach.call(c.querySelectorAll(".quick-item[data-nav]"), function (el) {
      el.addEventListener("click", function () { nav(el.getAttribute("data-nav")); });
    });

    try {
      var results = await Promise.all([api("/api/reports"), api("/api/notifications")]);
      var reports = results[0].reports;
      var notices = results[1].notices;
      var values = c.querySelectorAll(".stat .value");
      values[1].innerHTML = reports.length + '<span class="unit">份</span>';
      values[2].innerHTML = notices.length + '<span class="unit">条</span>';

      var iconCls = ["", "purple", "ok"];
      var iconName = ["user", "bell", "check"];
      document.getElementById("actList").innerHTML = notices.slice(0, 3).map(function (n, i) {
        return '<div class="act-item">' +
          '<div class="act-icon ' + iconCls[i % 3] + '">' + I[iconName[i % 3]] + '</div>' +
          '<div class="act-main">' +
            '<div class="act-title">' + esc(n.title) + '</div>' +
            '<div class="act-time">' + esc(n.kind) + ' · ' + esc(n.time) + '</div>' +
          '</div>' +
        '</div>';
      }).join("");
    } catch (e) {
      toast(e.message, "err");
    }
  }

  /* ---------------- 档案中心 ---------------- */

  function viewProfile() {
    var c = document.getElementById("content");
    var isAdmin = me.role === "admin";
    c.innerHTML =
      '<div class="profile-cols">' +
        '<div class="card profile-card">' +
          '<div class="avatar avatar-lg">' + esc(initial()) + '</div>' +
          '<div class="profile-name">' + esc(me.nickname || me.username) + '</div>' +
          '<div class="profile-bio">' + esc(me.bio || "这个人很懒，什么都没写") + '</div>' +
          '<div style="margin-top:12px"><span class="badge ' + (isAdmin ? "badge-admin" : "badge-user") + '">' + (isAdmin ? "管理员" : "普通用户") + '</span></div>' +
          '<div class="profile-meta">' +
            '<div class="meta-row"><span class="k">用户名</span><span class="v mono">' + esc(me.username) + '</span></div>' +
            '<div class="meta-row"><span class="k">用户 ID</span><span class="v mono">#' + me.uid + '</span></div>' +
            '<div class="meta-row"><span class="k">注册时间</span><span class="v">' + esc(me.created_at) + '</span></div>' +
            '<div class="meta-row"><span class="k">会话方式</span><span class="v mono">JWT · HS256</span></div>' +
          '</div>' +
        '</div>' +
        '<div class="card">' +
          '<div class="card-title">编辑资料</div>' +
          '<div style="margin-top:18px">' +
            '<div class="field">' +
              '<label>昵称</label>' +
              '<input class="input" id="pfNick" maxlength="20" value="' + esc(me.nickname || "") + '" placeholder="给自己起个昵称">' +
            '</div>' +
            '<div class="field">' +
              '<label>个人签名</label>' +
              '<textarea class="input" id="pfBio" rows="3" maxlength="120" placeholder="写点什么介绍一下自己…">' + esc(me.bio || "") + '</textarea>' +
              '<div class="hint">最多 120 字，会展示在资料卡片上。</div>' +
            '</div>' +
            '<div class="field">' +
              '<label>角色</label>' +
              '<input class="input" value="' + (isAdmin ? "管理员" : "普通用户") + '" disabled>' +
              '<div class="hint">角色由系统管理员分配，不可自行修改。</div>' +
            '</div>' +
            '<button class="btn btn-primary" id="pfSave">' + I.check + '保存修改</button>' +
          '</div>' +
        '</div>' +
      '</div>';

    document.getElementById("pfSave").addEventListener("click", async function () {
      var btn = document.getElementById("pfSave");
      btn.disabled = true;
      try {
        var r = await api("/api/profile", {
          method: "POST",
          body: {
            nickname: document.getElementById("pfNick").value,
            bio: document.getElementById("pfBio").value
          }
        });
        me = r.user;
        toast("资料已保存", "ok");
        renderShell("/profile");
      } catch (e) {
        toast(e.message, "err");
        btn.disabled = false;
      }
    });
  }

  /* ---------------- 档案检索 ---------------- */

  async function viewReports() {
    var c = document.getElementById("content");
    c.innerHTML =
      '<div class="card">' +
        '<div class="card-title">档案列表 <span class="more" id="reportCount"></span></div>' +
        '<div class="table-wrap"><table class="table">' +
          '<thead><tr><th>文件</th><th style="width:110px">大小</th><th style="width:170px">更新时间</th><th style="width:110px">操作</th></tr></thead>' +
          '<tbody id="reportBody"><tr><td colspan="4"><div class="skel" style="height:92px;margin:8px"></div></td></tr></tbody>' +
        '</table></div>' +
      '</div>';

    try {
      var r = await api("/api/reports");
      document.getElementById("reportCount").textContent = "共 " + r.reports.length + " 份";
      document.getElementById("reportBody").innerHTML = r.reports.map(function (item) {
        return '<tr>' +
          '<td><div class="file-cell">' + I.file + '<div>' +
            '<div class="file-name">' + esc(item.name) + '</div>' +
            '<div class="file-title">' + esc(item.title) + '</div>' +
          '</div></div></td>' +
          '<td>' + fmtSize(item.size) + '</td>' +
          '<td>' + esc(item.updated_at) + '</td>' +
          '<td><button class="btn btn-ghost btn-sm" data-dl="' + item.id + '">' + I.download + '下载</button></td>' +
        '</tr>';
      }).join("");
      Array.prototype.forEach.call(c.querySelectorAll("[data-dl]"), function (b) {
        b.addEventListener("click", function () {
          location.href = "/api/reports/download?id=" + b.getAttribute("data-dl");
        });
      });
    } catch (e) {
      toast(e.message, "err");
    }
  }

  /* ---------------- 消息通知 ---------------- */

  async function viewNotifications() {
    var c = document.getElementById("content");
    c.innerHTML = '<div id="noticeList">' +
      '<div class="skel" style="height:110px;margin-bottom:12px"></div>' +
      '<div class="skel" style="height:110px"></div></div>';

    try {
      var r = await api("/api/notifications");
      document.getElementById("noticeList").innerHTML = r.notices.map(function (n) {
        var unread = n.id >= 2;
        return '<div class="notice ' + (unread ? "unread" : "read") + '">' +
          '<div class="n-dot"></div>' +
          '<div class="n-main">' +
            '<div class="n-head"><span class="badge badge-blue">' + esc(n.kind) + '</span><span class="n-title">' + esc(n.title) + '</span></div>' +
            '<div class="n-body">' + esc(n.body) + '</div>' +
            '<div class="n-time">' + esc(n.time) + '</div>' +
          '</div>' +
        '</div>';
      }).join("");
    } catch (e) {
      toast(e.message, "err");
    }
  }

  /* ---------------- 系统管理（admin only） ---------------- */

  function renderRestricted(c, message) {
    c.innerHTML =
      '<div class="card restricted">' +
        '<div class="lock-circle">' + I.lock + '</div>' +
        '<h2>' + esc(message || "只有管理员才能使用") + '</h2>' +
        '<p>该功能仅对管理员开放。如果你需要使用，请联系系统管理员开通权限。</p>' +
        '<button class="btn btn-ghost" id="backDash">返回仪表盘</button>' +
      '</div>';
    document.getElementById("backDash").addEventListener("click", function () { nav("/dashboard"); });
  }

  async function viewAdmin() {
    var c = document.getElementById("content");
    c.innerHTML = '<div class="skel" style="height:220px"></div>';

    var usersRes;
    try {
      usersRes = await api("/api/admin/users");
    } catch (e) {
      // 服务端只认 JWT 里的 role；普通用户在这里被 403 拦下
      renderRestricted(c, e.message);
      return;
    }

    c.innerHTML =
      '<div class="card">' +
        '<div class="card-title">调阅日志导出</div>' +
        '<p class="page-desc">从档案库目录导出调阅日志或档案目录文件，用于线下审计与归档。</p>' +
        '<div class="export-row">' +
          '<input class="input mono" id="exFile" value="monthly.csv" spellcheck="false">' +
          '<button class="btn btn-primary" id="exBtn">' + I.download + '导出</button>' +
        '</div>' +
        '<div class="export-tip">仅支持导出 <span class="mono">/var/htu/archives</span> 目录下的文件，目录穿越与敏感路径会被安全策略拦截。</div>' +
        '<div class="export-result" id="exResult"></div>' +
      '</div>' +
      '<div class="card" style="margin-top:16px">' +
        '<div class="card-title">用户列表 <span class="more">共 ' + usersRes.total + ' 人</span></div>' +
        '<div class="table-wrap"><table class="table">' +
          '<thead><tr><th style="width:80px">ID</th><th>用户名</th><th>昵称</th><th style="width:120px">角色</th><th style="width:170px">注册时间</th></tr></thead>' +
          '<tbody>' + usersRes.users.map(function (u) {
            return '<tr>' +
              '<td class="mono">#' + u.uid + '</td>' +
              '<td class="mono">' + esc(u.username) + '</td>' +
              '<td>' + esc(u.nickname) + '</td>' +
              '<td><span class="badge ' + (u.role === "admin" ? "badge-admin" : "badge-user") + '">' + (u.role === "admin" ? "管理员" : "普通用户") + '</span></td>' +
              '<td>' + esc(u.created_at) + '</td>' +
            '</tr>';
          }).join("") + '</tbody>' +
        '</table></div>' +
      '</div>';

    document.getElementById("exBtn").addEventListener("click", async function () {
      var file = document.getElementById("exFile").value.trim();
      var box = document.getElementById("exResult");
      box.className = "export-result show";
      box.textContent = "正在导出 " + file + " …";
      try {
        var res = await fetch("/api/admin/export?file=" + encodeURIComponent(file), { credentials: "same-origin" });
        var text = await res.text();
        if (!res.ok) {
          var msg = text;
          try { msg = JSON.parse(text).error; } catch (e2) { /* 保留原文 */ }
          box.classList.add("err");
          box.textContent = "导出失败（" + res.status + "）：" + msg;
        } else {
          box.textContent = text;
        }
      } catch (e) {
        box.classList.add("err");
        box.textContent = "网络错误：" + e.message;
      }
    });
  }

  /* ---------------- 登录 / 注册 ---------------- */

  function renderAuth(mode) {
    mode = mode || "login";
    var isLogin = mode === "login";

    app.innerHTML =
      '<div class="auth">' +
        '<div class="auth-brand">' +
          '<div class="auth-brand-row"><div class="brand-mark">H</div><div class="brand-name">HTU 档案库</div></div>' +
          '<div class="auth-hero">' +
            '<h1>校内档案资源<br>统一管理平台</h1>' +
            '<p>档案归档 · 检索调阅 · 借阅审批统一出口</p>' +
          '</div>' +
          '<div class="auth-features">' +
            '<div class="auth-feature"><span class="dot"></span>档案中心：校内档案、制度、图纸统一归档</div>' +
            '<div class="auth-feature"><span class="dot"></span>档案检索：目录检索、调阅申请在线办理</div>' +
            '<div class="auth-feature"><span class="dot"></span>调阅出口：调阅日志统一导出与归档</div>' +
          '</div>' +
          '<div class="auth-foot">© 2026 HTU 档案馆 · 仅限校内使用</div>' +
        '</div>' +
        '<div class="auth-side">' +
          '<div class="auth-card">' +
            '<h2>' + (isLogin ? "登录 HTU 档案库" : "注册账号") + '</h2>' +
            '<div class="sub">' + (isLogin ? "使用校园网账号登录，首次使用请先注册" : "注册即代表同意《HTU 档案库使用规范》") + '</div>' +
            '<div class="seg">' +
              '<button type="button" id="tabLogin" class="' + (isLogin ? "on" : "") + '">登录</button>' +
              '<button type="button" id="tabReg" class="' + (isLogin ? "" : "on") + '">注册</button>' +
            '</div>' +
            '<form id="authForm">' +
              '<div class="field">' +
                '<label>用户名</label>' +
                '<input class="input" id="fUser" autocomplete="username" maxlength="20" placeholder="3-20 位字母、数字或下划线">' +
              '</div>' +
              '<div class="field">' +
                '<label>密码</label>' +
                '<input class="input" id="fPass" type="password" autocomplete="' + (isLogin ? "current-password" : "new-password") + '" placeholder="至少 6 位">' +
              '</div>' +
              (isLogin ? "" :
                '<div class="field">' +
                  '<label>确认密码</label>' +
                  '<input class="input" id="fPass2" type="password" autocomplete="new-password" placeholder="再输入一次密码">' +
                '</div>') +
              '<button class="btn btn-primary btn-block" id="authBtn" type="submit">' + (isLogin ? "登 录" : "注册并登录") + '</button>' +
            '</form>' +
            '<div class="auth-note">登录状态保存在 Cookie（htu_token，7 天有效）</div>' +
          '</div>' +
        '</div>' +
      '</div>';

    document.getElementById("tabLogin").addEventListener("click", function () { renderAuth("login"); });
    document.getElementById("tabReg").addEventListener("click", function () { renderAuth("register"); });

    document.getElementById("authForm").addEventListener("submit", async function (e) {
      e.preventDefault();
      var username = document.getElementById("fUser").value.trim();
      var password = document.getElementById("fPass").value;
      var btn = document.getElementById("authBtn");
      if (!username || !password) { toast("请输入用户名和密码", "err"); return; }
      if (!isLogin) {
        var p2 = document.getElementById("fPass2").value;
        if (p2 !== password) { toast("两次输入的密码不一致", "err"); return; }
      }
      btn.disabled = true;
      btn.textContent = "请稍候…";
      try {
        var r = await api(isLogin ? "/api/login" : "/api/register", {
          method: "POST",
          body: { username: username, password: password }
        });
        me = r.user;
        toast(isLogin ? "欢迎回来，" + (r.user.nickname || r.user.username) : "注册成功，已自动登录", "ok");
        nav("/dashboard");
      } catch (err) {
        toast(err.message, "err");
        btn.disabled = false;
        btn.textContent = isLogin ? "登 录" : "注册并登录";
      }
    });
  }

  boot();
})();
