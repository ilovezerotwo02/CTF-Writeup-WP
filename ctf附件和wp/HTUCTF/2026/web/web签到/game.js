/* ============================================================
 * 零号终端 / TERMINAL ZERO
 * 五层内存分区 · 收齐校验令牌 · 抵达出口
 * ------------------------------------------------------------
 * 玩法：WASD / 方向键移动，每层收齐令牌后出口解锁，
 *       穿过五层即显示核心密钥（flag）。
 * ============================================================ */

(function () {
  'use strict';

  /* 核心密钥（Base64）。通关后解码展示。 */
  var FLAG_B64 = 'SFRVQ1RGe3czbGMwbTNfdDBfaHR1Y3RmXzIwMjZ9';

  var STEP = 0.155;        // 每移动一格消耗秒数
  var CELL_MIN = 22;
  var CELL_MAX = 60;
  var CATCH_DIST = 0.62;   // 与哨兵的距离小于该值即被捕获（单位：格）

  /* ---------- 关卡数据 ---------- */

  var LEVELS = [
    {
      name: '引导扇区',
      subtitle: 'BOOT SECTOR',
      time: 45,
      map: [
        '###############',
        '#P......#...#K#',
        '#####...#...#.#',
        '#.........#.#.#',
        '#.#######.#.#.#',
        '#.#.....#.....#',
        '#.##..#.#.#...#',
        '#.....#...#...#',
        '###.###.#.#.###',
        '#K...........E#',
        '###############'
      ],
      patrols: [
        [[1, 7], [2, 7], [3, 7], [4, 7], [5, 7]],
        [[7, 5], [7, 6], [7, 7], [7, 8], [7, 9]]
      ],
      speed: 1.25
    },
    {
      name: '页表区',
      subtitle: 'PAGE TABLE',
      time: 45,
      map: [
        '#################',
        '#P#...K.#.......#',
        '#.#.#.#...#####.#',
        '#.#...#.#.....#.#',
        '#.#.###.###.#.###',
        '#...#.#...#.#...#',
        '#.#.#.###.#.###.#',
        '#.......#...#..K#',
        '#.#.#######...#E#',
        '#.#.......#.....#',
        '#.#.#.....#.###.#',
        '#K....#.........#',
        '#################'
      ],
      patrols: [
        [[11, 9], [12, 9], [13, 9], [14, 9], [15, 9]],
        [[7, 1], [7, 2], [7, 3], [7, 4], [7, 5]]
      ],
      speed: 1.4
    },
    {
      name: '调度核心',
      subtitle: 'SCHEDULER',
      time: 50,
      map: [
        '###################',
        '#P......#.....K...#',
        '#.##.##.###...#####',
        '#..K........#.....#',
        '#.##.####.###.###.#',
        '#.......#...#...#.#',
        '#.#####.###...###.#',
        '#.#...#.....#.#...#',
        '#.###.###.#####...#',
        '#.#.......#.......#',
        '#.#.#..##.#.#.###.#',
        '#...........#...KE#',
        '###################'
      ],
      patrols: [
        [[7, 7], [8, 7], [9, 7], [10, 7], [11, 7]],
        [[5, 7], [5, 8], [5, 9], [5, 10], [5, 11]],
        [[13, 1], [13, 2], [13, 3], [13, 4], [13, 5], [13, 6], [13, 7]]
      ],
      speed: 1.55
    },
    {
      name: '内核栈',
      subtitle: 'KERNEL STACK',
      time: 60,
      map: [
        '#####################',
        '#P...K..#.....#.....#',
        '###.#.....#.#...###.#',
        '#.....#.#.#.....#K#.#',
        '#.###.#.#.#.###.#.#.#',
        '#.#...#...#.#...#.#.#',
        '#...###.#.#.#.###.#.#',
        '#.......#.#.#...#...#',
        '#####.###.#####.#...#',
        '#.....#...........#.#',
        '#.#######.#####.#.#.#',
        '#...#.......K.#.#...#',
        '###.#...#.#.#.###...#',
        '#K....#.....#.....#E#',
        '#####################'
      ],
      patrols: [
        [[13, 13], [14, 13], [15, 13], [16, 13], [17, 13]],
        [[7, 1], [7, 2], [7, 3], [7, 4], [7, 5], [7, 6], [7, 7]],
        [[11, 3], [12, 3], [13, 3], [14, 3], [15, 3]]
      ],
      speed: 1.7
    },
    {
      name: '零号核心',
      subtitle: 'CORE / 0',
      time: 70,
      map: [
        '#######################',
        '#P#.........#..K....#.#',
        '#...#####...#.###.#.#.#',
        '#...#.....#...#...#...#',
        '#####.#####.#.#.###.#.#',
        '#K#...#.#.............#',
        '#E#.###....####.#######',
        '#.#...#.....#.........#',
        '#.###.#####...##.####.#',
        '#...#...#.#.......#...#',
        '#.#####...###.##.##.#.#',
        '#.#...#.#K....#...#.#.#',
        '#.#.#...#.##.##.#.#.#.#',
        '#...#...........#....K#',
        '#######################'
      ],
      patrols: [
        [[7, 9], [7, 10], [7, 11], [7, 12], [7, 13]],
        [[7, 7], [8, 7], [9, 7], [10, 7], [11, 7]],
        [[11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9]],
        [[21, 1], [21, 2], [21, 3], [21, 4], [21, 5]]
      ],
      speed: 1.85
    }
  ];

  /* ---------- DOM ---------- */

  var canvas = document.getElementById('game');
  var ctx = canvas.getContext('2d');
  var $ = function (id) { return document.getElementById(id); };

  var elHud = $('hud');
  var elHudLevel = $('hudLevel');
  var elHudName = $('hudName');
  var elHudSub = $('hudSub');
  var elHudKeys = $('hudKeys');
  var elHudTime = $('hudTime');
  var elTimeFill = $('timeFill');
  var elStart = $('startScreen');
  var elOver = $('overScreen');
  var elOverReason = $('overReason');
  var elOverStat = $('overStat');
  var elWin = $('winScreen');
  var elFlag = $('flagText');
  var elWinStat = $('winStat');
  var elToast = $('toast');
  var elState = $('stateText');

  /* ---------- 状态 ---------- */

  var state = 'boot';       // boot | play | pause | over | win
  var levelIndex = 0;
  var level = null;         // 当前层运行时数据
  var timeLeft = 0;
  var elapsed = 0;
  var totalTime = 0;
  var lastFrame = 0;
  var rafId = 0;
  var shakeUntil = 0;
  var toastTimer = 0;

  var view = { w: 0, h: 0, cell: 36, cols: 0, rows: 0 };

  var player = null;
  var guards = [];
  var trail = [];

  /* 输入：按下的方向，最后按下的优先 */
  var held = [];
  var DIRS = {
    up: { x: 0, y: -1 },
    down: { x: 0, y: 1 },
    left: { x: -1, y: 0 },
    right: { x: 1, y: 0 }
  };
  var KEYMAP = {
    ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right',
    w: 'up', s: 'down', a: 'left', d: 'right',
    W: 'up', S: 'down', A: 'left', D: 'right'
  };

  /* ---------- 工具 ---------- */

  function pad(n, len) {
    var s = String(n);
    while (s.length < len) s = '0' + s;
    return s;
  }

  function toast(text, danger) {
    elToast.textContent = text;
    elToast.className = 'toast is-on' + (danger ? ' is-danger' : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      elToast.className = 'toast' + (danger ? ' is-danger' : '');
    }, 1600);
  }

  function setState(text) {
    if (elState) elState.textContent = text;
  }

  /* ---------- 关卡装载 ---------- */

  function loadLevel(idx, keepTotal) {
    var src = LEVELS[idx];
    var rows = src.map.length;
    var cols = src.map[0].length;
    var grid = [];
    var keys = [];
    var start = { x: 1, y: 1 };
    var exit = { x: cols - 2, y: rows - 2 };

    for (var y = 0; y < rows; y++) {
      grid.push([]);
      for (var x = 0; x < cols; x++) {
        var ch = src.map[y].charAt(x);
        grid[y].push(ch === '#');
        if (ch === 'P') start = { x: x, y: y };
        if (ch === 'E') exit = { x: x, y: y };
        if (ch === 'K') keys.push({ x: x, y: y, taken: false });
      }
    }

    level = {
      src: src,
      cols: cols,
      rows: rows,
      grid: grid,
      keys: keys,
      exit: exit,
      totalKeys: keys.length,
      gotKeys: 0,
      index: idx
    };

    guards = src.patrols.map(function (path, i) {
      return {
        path: path,
        seg: 0,
        dir: 1,
        frac: (i * 0.37) % 1,
        speed: src.speed,
        x: path[0][0],
        y: path[0][1]
      };
    });

    player = {
      x: start.x,
      y: start.y,
      rx: start.x,
      ry: start.y,
      from: { x: start.x, y: start.y },
      to: { x: start.x, y: start.y },
      moving: false,
      t: 0,
      face: { x: 1, y: 0 }
    };

    trail = [];
    tap.dir = null;
    timeLeft = src.time;
    elapsed = 0;
    if (!keepTotal) totalTime = 0;

    fitCanvas(cols, rows);
    syncHud(true);

    elHud.classList.remove('is-hidden');
    elHudLevel.textContent = (idx + 1) + '/' + LEVELS.length;
    elHudName.textContent = src.name;
    elHudSub.textContent = src.subtitle;
    elHudKeys.innerHTML = '';
    for (var k = 0; k < keys.length; k++) {
      var dotEl = document.createElement('b');
      dotEl.className = 'hkey';
      elHudKeys.appendChild(dotEl);
    }

    setState('RUNNING · L' + (idx + 1));
  }

  function fitCanvas(cols, rows) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var box = document.getElementById('screen');
    var avail = box ? box.clientWidth - 20 : window.innerWidth - 76;
    if (!avail || avail < 200) avail = Math.min(window.innerWidth - 76, 862);
    var cell = Math.floor(Math.min(avail, 862) / cols);
    cell = Math.max(CELL_MIN, Math.min(CELL_MAX, cell));
    view.cols = cols;
    view.rows = rows;
    view.cell = cell;
    view.w = cols * cell;
    view.h = rows * cell;

    canvas.width = Math.round(view.w * dpr);
    canvas.height = Math.round(view.h * dpr);
    canvas.style.maxWidth = view.w + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function cellCenter(gx, gy) {
    var c = view.cell;
    return { x: gx * c + c / 2, y: gy * c + c / 2 };
  }

  function isWall(gx, gy) {
    if (gx < 0 || gy < 0 || gx >= level.cols || gy >= level.rows) return true;
    return level.grid[gy][gx];
  }

  /* ---------- 输入 ---------- */

  /* 轻点缓冲：低帧率设备上“按下即抬起”可能整帧被跳过，留一个极短的输入余量 */
  var tap = { dir: null, until: 0 };

  function pushDir(dir) {
    if (held.indexOf(dir) === -1) held.push(dir);
    tap.dir = dir;
    tap.until = (window.performance ? performance.now() : Date.now()) + 140;
  }

  function popDir(dir) {
    var i = held.indexOf(dir);
    if (i !== -1) held.splice(i, 1);
  }

  function currentDir() {
    for (var i = held.length - 1; i >= 0; i--) {
      if (held[i]) return DIRS[held[i]];
    }
    var nowMs = window.performance ? performance.now() : Date.now();
    if (tap.dir && nowMs <= tap.until) {
      var d = DIRS[tap.dir];
      tap.dir = null;
      return d;
    }
    return null;
  }

  document.addEventListener('keydown', function (e) {
    var dir = KEYMAP[e.key];
    if (dir) {
      e.preventDefault();
      if (state === 'play') pushDir(dir);
      return;
    }
    if (e.key === 'Enter') {
      if (state === 'boot') startGame();
      return;
    }
    if (e.key === 'r' || e.key === 'R') {
      if (state === 'play' || state === 'over') restartLevel();
    }
  });

  document.addEventListener('keyup', function (e) {
    var dir = KEYMAP[e.key];
    if (dir) {
      e.preventDefault();
      popDir(dir);
    }
  });

  window.addEventListener('blur', function () { held = []; });

  /* 手机方向键 */
  Array.prototype.forEach.call(document.querySelectorAll('#dpad button'), function (btn) {
    var dir = btn.getAttribute('data-dir');
    var on = function (e) { e.preventDefault(); pushDir(dir); };
    var off = function (e) { e.preventDefault(); popDir(dir); };
    btn.addEventListener('pointerdown', on);
    btn.addEventListener('pointerup', off);
    btn.addEventListener('pointercancel', off);
    btn.addEventListener('pointerleave', off);
  });

  /* ---------- 开始 / 结束 ---------- */

  function startGame() {
    elStart.classList.add('is-hidden');
    elOver.classList.add('is-hidden');
    elWin.classList.add('is-hidden');
    levelIndex = 0;
    state = 'play';
    loadLevel(0, false);
    lastFrame = 0;
    cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(loop);
  }

  function restartLevel() {
    elOver.classList.add('is-hidden');
    tap.dir = null;
    state = 'play';
    loadLevel(levelIndex, true);
    lastFrame = 0;
    cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(loop);
  }

  function gameOver(reason) {
    if (state !== 'play') return;
    state = 'over';
    held = [];
    elToast.className = 'toast';
    setState('HALTED');
    elOverReason.textContent = reason;
    elOverStat.textContent =
      '停在 第 ' + (levelIndex + 1) + ' 层 · ' + level.src.name +
      ' · 令牌 ' + level.gotKeys + '/' + level.totalKeys;
    elOver.classList.remove('is-hidden');
  }

  function winGame() {
    state = 'win';
    held = [];
    elToast.className = 'toast';
    setState('CORE UNLOCKED');
    var flag = '';
    try { flag = atob(FLAG_B64); } catch (err) { flag = FLAG_B64; }
    elFlag.textContent = flag;
    elWinStat.textContent = '总耗时 ' + totalTime.toFixed(1) + 's · 五层全部清除';
    elWin.classList.remove('is-hidden');
  }

  function levelClear() {
    state = 'pause';
    setState('LAYER CLEAR');
    if (levelIndex >= LEVELS.length - 1) {
      winGame();
      return;
    }
    toast('第 ' + (levelIndex + 1) + ' 层已穿透 · 载入下一分区');
    setTimeout(function () {
      if (state !== 'pause') return;
      levelIndex += 1;
      state = 'play';
      loadLevel(levelIndex, true);
      lastFrame = 0;
    }, 900);
  }

  /* ---------- 逻辑更新 ---------- */

  function onEnterCell(x, y) {
    for (var i = 0; i < level.keys.length; i++) {
      var k = level.keys[i];
      if (!k.taken && k.x === x && k.y === y) {
        k.taken = true;
        level.gotKeys += 1;
        syncHud(false);
        toast('令牌 ' + level.gotKeys + '/' + level.totalKeys + ' 已校验');
        return;
      }
    }
    if (x === level.exit.x && y === level.exit.y) {
      if (level.gotKeys >= level.totalKeys) {
        levelClear();
      } else {
        toast('出口已锁定 · 还差 ' + (level.totalKeys - level.gotKeys) + ' 枚令牌', true);
        shakeUntil = elapsed + 0.28;
      }
    }
  }

  function updatePlayer(dt) {
    if (player.moving) {
      player.t += dt;
      var k = Math.min(1, player.t / STEP);
      player.rx = player.from.x + (player.to.x - player.from.x) * k;
      player.ry = player.from.y + (player.to.y - player.from.y) * k;
      if (k >= 1) {
        player.x = player.to.x;
        player.y = player.to.y;
        player.moving = false;
        onEnterCell(player.x, player.y);
      }
      return;
    }

    var d = currentDir();
    if (!d) return;
    player.face = d;
    if (isWall(player.x + d.x, player.y + d.y)) return;

    player.moving = true;
    player.t = 0;
    player.from = { x: player.x, y: player.y };
    player.to = { x: player.x + d.x, y: player.y + d.y };
  }

  function updateGuards(dt) {
    for (var i = 0; i < guards.length; i++) {
      var g = guards[i];
      if (g.path.length < 2) continue;
      g.frac += dt * g.speed;
      while (g.frac >= 1) {
        g.frac -= 1;
        g.seg += g.dir;
        if (g.seg >= g.path.length - 1) {
          g.seg = g.path.length - 1;
          g.dir = -1;
        } else if (g.seg <= 0) {
          g.seg = 0;
          g.dir = 1;
        }
      }
      var a = g.path[g.seg];
      var b = g.path[Math.max(0, Math.min(g.path.length - 1, g.seg + g.dir))];
      g.x = a[0] + (b[0] - a[0]) * g.frac;
      g.y = a[1] + (b[1] - a[1]) * g.frac;
    }
  }

  function checkCatch() {
    var px = player.rx + 0.5;
    var py = player.ry + 0.5;
    for (var i = 0; i < guards.length; i++) {
      var dx = guards[i].x + 0.5 - px;
      var dy = guards[i].y + 0.5 - py;
      if (dx * dx + dy * dy < CATCH_DIST * CATCH_DIST) {
        gameOver('哨兵捕获了你的执行流。');
        return true;
      }
    }
    return false;
  }

  var hudCache = {};
  function syncHud(force) {
    if (!level) return;
    var t = Math.max(0, timeLeft);
    var timeText = t.toFixed(1) + 's';
    if (force || hudCache.time !== timeText) {
      elHudTime.textContent = timeText;
      hudCache.time = timeText;
    }
    var low = t <= 10;
    elHudTime.classList.toggle('is-low', low);
    elTimeFill.classList.toggle('is-low', low);
    var ratio = Math.max(0, Math.min(1, t / level.src.time));
    elTimeFill.style.transform = 'scaleX(' + ratio.toFixed(3) + ')';

    if (force) {
      var dots = elHudKeys.children;
      for (var i = 0; i < dots.length; i++) dots[i].classList.remove('is-on');
    }
    var dots2 = elHudKeys.children;
    for (var j = 0; j < level.keys.length; j++) {
      if (dots2[j]) dots2[j].classList.toggle('is-on', level.keys[j].taken);
    }
  }

  /* ---------- 渲染 ---------- */

  function drawGrid() {
    var c = view.cell;
    ctx.fillStyle = '#060b0d';
    ctx.fillRect(0, 0, view.w, view.h);

    // 地面细网格
    ctx.save();
    ctx.strokeStyle = 'rgba(110, 243, 176, 0.05)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (var x = 1; x < view.cols; x++) {
      ctx.moveTo(x * c + 0.5, 0);
      ctx.lineTo(x * c + 0.5, view.h);
    }
    for (var y = 1; y < view.rows; y++) {
      ctx.moveTo(0, y * c + 0.5);
      ctx.lineTo(view.w, y * c + 0.5);
    }
    ctx.stroke();

    // 走廊交点微光
    ctx.fillStyle = 'rgba(110, 243, 176, 0.10)';
    for (var gy = 1; gy < view.rows - 1; gy++) {
      for (var gx = 1; gx < view.cols - 1; gx++) {
        if (level.grid[gy][gx]) continue;
        ctx.fillRect(gx * c + c / 2 - 0.5, gy * c + c / 2 - 0.5, 1, 1);
      }
    }
    ctx.restore();
  }

  function drawWalls() {
    var c = view.cell;
    var edge = Math.max(1, Math.round(c * 0.045));
    for (var y = 0; y < view.rows; y++) {
      for (var x = 0; x < view.cols; x++) {
        if (!level.grid[y][x]) continue;
        var px = x * c;
        var py = y * c;
        ctx.fillStyle = '#101f26';
        ctx.fillRect(px, py, c, c);

        // 朝向走廊的一侧做明暗处理，墙体才有体积
        if (!isWall(x, y - 1)) {
          ctx.fillStyle = 'rgba(110, 243, 176, 0.20)';
          ctx.fillRect(px, py, c, edge);
        }
        if (!isWall(x, y + 1)) {
          ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
          ctx.fillRect(px, py + c - edge, c, edge);
        }
        if (!isWall(x - 1, y)) {
          ctx.fillStyle = 'rgba(110, 243, 176, 0.08)';
          ctx.fillRect(px, py, edge, c);
        }
        if (!isWall(x + 1, y)) {
          ctx.fillStyle = 'rgba(0, 0, 0, 0.28)';
          ctx.fillRect(px + c - edge, py, edge, c);
        }
      }
    }
  }

  function drawExit(now) {
    var pos = cellCenter(level.exit.x, level.exit.y);
    var r = view.cell * 0.3;
    var open = level.gotKeys >= level.totalKeys;

    ctx.save();
    ctx.translate(pos.x, pos.y);

    if (open) {
      var pulse = 0.5 + Math.sin(now * 4) * 0.5;
      ctx.shadowColor = 'rgba(110, 243, 176, 0.9)';
      ctx.shadowBlur = 18 + pulse * 16;

      ctx.strokeStyle = 'rgba(110, 243, 176, ' + (0.65 + pulse * 0.35) + ')';
      ctx.lineWidth = Math.max(1.4, view.cell * 0.05);
      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(87, 217, 255, 0.55)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(0, 0, r * 1.55, now * 1.2, now * 1.2 + Math.PI * 1.2);
      ctx.stroke();

      ctx.fillStyle = 'rgba(110, 243, 176, ' + (0.16 + pulse * 0.18) + ')';
      ctx.beginPath();
      ctx.arc(0, 0, r * 0.55, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.strokeStyle = 'rgba(110, 243, 176, 0.34)';
      ctx.lineWidth = 1.4;
      ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = 'rgba(110, 243, 176, 0.5)';
      ctx.beginPath();
      ctx.arc(0, 0, view.cell * 0.07, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawKeys(now) {
    for (var i = 0; i < level.keys.length; i++) {
      var k = level.keys[i];
      if (k.taken) continue;
      var pos = cellCenter(k.x, k.y);
      var bob = Math.sin(now * 2.6 + i) * view.cell * 0.045;
      var size = view.cell * 0.22;

      ctx.save();
      ctx.translate(pos.x, pos.y + bob);
      ctx.rotate(Math.PI / 4 + now * 0.6);
      ctx.shadowColor = 'rgba(110, 243, 176, 0.85)';
      ctx.shadowBlur = 14;
      ctx.fillStyle = '#6ef3b0';
      ctx.fillRect(-size / 2, -size / 2, size, size);
      ctx.shadowBlur = 0;
      ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
      ctx.fillRect(-size / 6, -size / 6, size / 3, size / 3);
      ctx.restore();
    }
  }

  function drawGuards(now) {
    for (var i = 0; i < guards.length; i++) {
      var g = guards[i];
      var pos = cellCenter(g.x, g.y);
      var size = view.cell * 0.3;

      ctx.save();
      ctx.translate(pos.x, pos.y);

      // 扫描光晕
      var aura = ctx.createRadialGradient(0, 0, 0, 0, 0, size * 2.6);
      aura.addColorStop(0, 'rgba(255, 84, 112, 0.30)');
      aura.addColorStop(1, 'rgba(255, 84, 112, 0)');
      ctx.fillStyle = aura;
      ctx.beginPath();
      ctx.arc(0, 0, size * 2.6, 0, Math.PI * 2);
      ctx.fill();

      // 外圈
      ctx.strokeStyle = 'rgba(255, 84, 112, 0.55)';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 5]);
      ctx.beginPath();
      ctx.arc(0, 0, size * (1.5 + Math.sin(now * 3 + i) * 0.12), 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);

      // 本体：旋转方块
      ctx.rotate(now * 1.9 + i * 0.7);
      ctx.shadowColor = 'rgba(255, 84, 112, 0.9)';
      ctx.shadowBlur = 12;
      ctx.fillStyle = '#ff5470';
      ctx.beginPath();
      ctx.moveTo(0, -size);
      ctx.lineTo(size * 0.72, 0);
      ctx.lineTo(0, size);
      ctx.lineTo(-size * 0.72, 0);
      ctx.closePath();
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = 'rgba(18, 4, 10, 0.85)';
      ctx.beginPath();
      ctx.moveTo(0, -size * 0.4);
      ctx.lineTo(size * 0.3, 0);
      ctx.lineTo(0, size * 0.4);
      ctx.lineTo(-size * 0.3, 0);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
  }

  function drawPlayer(now) {
    var pos = cellCenter(player.rx, player.ry);
    var r = view.cell * 0.22;

    // 拖尾
    for (var i = trail.length - 1; i >= 0; i--) {
      var t = trail[i];
      var a = (i + 1) / trail.length * 0.22;
      ctx.beginPath();
      ctx.arc(t.x, t.y, r * (0.4 + a), 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(87, 217, 255, ' + a.toFixed(3) + ')';
      ctx.fill();
    }

    ctx.save();
    ctx.translate(pos.x, pos.y);
    ctx.shadowColor = 'rgba(174, 250, 255, 0.95)';
    ctx.shadowBlur = 16;
    ctx.fillStyle = '#eafcff';
    ctx.beginPath();
    ctx.arc(0, 0, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    ctx.fillStyle = '#6ef3b0';
    ctx.beginPath();
    ctx.arc(0, 0, r * 0.34, 0, Math.PI * 2);
    ctx.fill();

    // 朝向刻线
    ctx.strokeStyle = 'rgba(110, 243, 176, 0.9)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(player.face.x * r * 0.6, player.face.y * r * 0.6);
    ctx.lineTo(player.face.x * r * 1.7, player.face.y * r * 1.7);
    ctx.stroke();

    // 呼吸环
    ctx.strokeStyle = 'rgba(87, 217, 255, 0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(0, 0, r * (1.6 + Math.sin(now * 3.4) * 0.15), 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  function render(now) {
    if (!level) return;
    ctx.save();
    if (shakeUntil > elapsed) {
      var amp = view.cell * 0.06;
      ctx.translate((Math.random() - 0.5) * amp, (Math.random() - 0.5) * amp);
    }
    drawGrid();
    drawExit(now);
    drawKeys(now);
    drawWalls();
    drawGuards(now);
    drawPlayer(now);
    ctx.restore();
  }

  /* ---------- 主循环 ---------- */

  function loop(ts) {
    rafId = requestAnimationFrame(loop);
    if (state !== 'play') {
      // 关卡切换/结束时仍渲染一帧静态画面
      if (level) render(elapsed);
      return;
    }

    if (!lastFrame) lastFrame = ts;
    var dt = Math.min((ts - lastFrame) / 1000, 0.05);
    lastFrame = ts;
    elapsed += dt;
    totalTime += dt;
    timeLeft -= dt;

    if (timeLeft <= 0) {
      timeLeft = 0;
      syncHud(false);
      gameOver('内存回收超时，进程被清零。');
      return;
    }

    updatePlayer(dt);
    updateGuards(dt);

    if (state === 'play' && checkCatch()) {
      syncHud(false);
      return;
    }

    // 记录拖尾
    var pos = cellCenter(player.rx, player.ry);
    trail.push({ x: pos.x, y: pos.y });
    if (trail.length > 7) trail.shift();

    syncHud(false);
    render(elapsed);
  }

  /* ---------- 启动界面引导文字 ---------- */

  function playBootLog() {
    var el = $('bootlog');
    if (!el) return;
    var lines = [
      '> mount /dev/mem ............ <b>ok</b>',
      '> scan partitions ........... <b>5 found</b>',
      '> resident process .......... <b>pid 0</b>',
      '> reclaim scheduled in ...... <b>soon</b>'
    ];
    var i = 0;
    el.textContent = '';
    function tick() {
      if (i >= lines.length) return;
      el.innerHTML += (i ? '\n' : '') + lines[i];
      i += 1;
      setTimeout(tick, 220);
    }
    tick();
  }

  /* ---------- 事件绑定 ---------- */

  $('btnStart').addEventListener('click', startGame);
  $('btnRetry').addEventListener('click', restartLevel);
  $('btnAgain').addEventListener('click', startGame);

  window.addEventListener('resize', function () {
    if (!level || state === 'boot') return;
    fitCanvas(level.cols, level.rows);
    render(elapsed);
  });

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) held = [];
    lastFrame = 0;
  });

  playBootLog();

  // 初始静态画面：显示第一层的空场，避免开始前是纯黑
  state = 'boot';
  loadLevel(0, false);
  setState('READY');
  elHud.classList.add('is-hidden');
  fitCanvas(level.cols, level.rows);
  render(0);
})();
