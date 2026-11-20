// Midnight Apex sprite-stack look test.
// Draw matches tools/stack_math.py: sheet faces +y, turn = atan2(vy, vx) - PI/2,
// canvas rotation (clockwise in y-down), then squash, then 1px lift per slice.
// World buffer is 640x480. RGB555 + 4x4 Bayer, then 2x nearest. UI is after that.

(function () {
  const VIEW_W = 640;
  const VIEW_H = 480;
  const SCALE = 2;
  const PPM = window.STACK_MANIFEST.ppm;
  const ANCHOR_X = 312;
  const ANCHOR_Y = 338;
  const ROAD_LEN = 168;
  const HALF_W = 4.05;
  const FINISH = 156;
  const FOG = [0x0b / 255, 0x17 / 255, 0x2b / 255];
  const ZENITH = [0x01 / 255, 0x04 / 255, 0x08 / 255];
  const FOG_NEAR = 8;
  const FOG_FAR = 34;
  const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
  const INK = [4, 8, 16, 255];

  const params = new URLSearchParams(location.search);
  let spacing = 1;
  let squash = 0.75;
  let camX = 0;
  let camZ = 0;

  const view = document.getElementById("view");
  const vctx = view.getContext("2d");
  const world = document.createElement("canvas");
  world.width = VIEW_W;
  world.height = VIEW_H;
  const wctx = world.getContext("2d", { willReadFrequently: true });
  let frame = wctx.createImageData(VIEW_W, VIEW_H);
  const depth = new Float32Array(VIEW_W * VIEW_H);
  const keys = Object.create(null);

  const FONT = {
    " ": [0, 0, 0, 0, 0, 0, 0],
    A: [14, 17, 17, 31, 17, 17, 17],
    B: [30, 17, 17, 30, 17, 17, 30],
    C: [14, 17, 16, 16, 16, 17, 14],
    D: [30, 17, 17, 17, 17, 17, 30],
    E: [31, 16, 16, 30, 16, 16, 31],
    F: [31, 16, 16, 30, 16, 16, 16],
    G: [14, 17, 16, 23, 17, 17, 14],
    H: [17, 17, 17, 31, 17, 17, 17],
    I: [31, 4, 4, 4, 4, 4, 31],
    J: [31, 2, 2, 2, 2, 18, 12],
    K: [17, 18, 20, 24, 20, 18, 17],
    L: [16, 16, 16, 16, 16, 16, 31],
    M: [17, 27, 21, 21, 17, 17, 17],
    N: [17, 25, 21, 19, 17, 17, 17],
    O: [14, 17, 17, 17, 17, 17, 14],
    P: [30, 17, 17, 30, 16, 16, 16],
    Q: [14, 17, 17, 17, 21, 18, 13],
    R: [30, 17, 17, 30, 20, 18, 17],
    S: [14, 17, 16, 14, 1, 17, 14],
    T: [31, 4, 4, 4, 4, 4, 4],
    U: [17, 17, 17, 17, 17, 17, 14],
    V: [17, 17, 17, 17, 17, 10, 4],
    W: [17, 17, 17, 21, 21, 21, 10],
    X: [17, 17, 10, 4, 10, 17, 17],
    Y: [17, 17, 10, 4, 4, 4, 4],
    Z: [31, 1, 2, 4, 8, 16, 31],
    0: [14, 17, 19, 21, 25, 17, 14],
    1: [4, 12, 4, 4, 4, 4, 14],
    2: [14, 17, 1, 6, 8, 16, 31],
    3: [14, 17, 1, 6, 1, 17, 14],
    4: [2, 6, 10, 18, 31, 2, 2],
    5: [31, 16, 30, 1, 1, 17, 14],
    6: [14, 16, 16, 30, 17, 17, 14],
    7: [31, 1, 2, 4, 8, 8, 8],
    8: [14, 17, 17, 14, 17, 17, 14],
    9: [14, 17, 17, 15, 1, 1, 14],
    ".": [0, 0, 0, 0, 0, 12, 12],
    "/": [1, 2, 4, 4, 4, 8, 16],
    ":": [0, 12, 12, 0, 12, 12, 0],
    "-": [0, 0, 0, 31, 0, 0, 0],
    "+": [0, 4, 4, 31, 4, 4, 0],
  };

  function setStatus(text) {
    const el = document.getElementById("status");
    if (el) el.textContent = text;
  }

  function clamp(v, a, b) {
    return v < a ? a : v > b ? b : v;
  }

  function iround(v) {
    return Math.floor(v + 0.5);
  }

  function wrap(a) {
    while (a > Math.PI) a -= Math.PI * 2;
    while (a < -Math.PI) a += Math.PI * 2;
    return a;
  }

  function smoothstep(a, b, x) {
    const t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function lerp3(a, b, t) {
    return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
  }

  function buildRoad() {
    const pts = [];
    let x = 0;
    let z = 0;
    for (let s = 0; s <= ROAD_LEN; s += 1) {
      const heading = 1.18 * smoothstep(26, 116, s);
      const dx = -Math.sin(heading);
      const dz = -Math.cos(heading);
      // Visual left when +x is screen right and +z is screen down.
      const lx = dz;
      const lz = -dx;
      pts.push({ s, x, z, dx, dz, lx, lz, heading });
      x += dx;
      z += dz;
    }
    return pts;
  }

  const road = buildRoad();

  function roadAt(s) {
    const c = clamp(s, 0, ROAD_LEN);
    const i = Math.floor(c);
    const f = c - i;
    const a = road[i];
    const b = road[Math.min(i + 1, road.length - 1)];
    return {
      s: c,
      x: a.x + (b.x - a.x) * f,
      z: a.z + (b.z - a.z) * f,
      dx: a.dx + (b.dx - a.dx) * f,
      dz: a.dz + (b.dz - a.dz) * f,
      lx: a.lx,
      lz: a.lz,
      heading: a.heading,
    };
  }

  function nearestPoint(x, z, hint) {
    let best = hint || 0;
    let bestD = 1e9;
    const i0 = Math.max(0, best - 30);
    const i1 = Math.min(road.length - 1, best + 40);
    for (let i = i0; i <= i1; i++) {
      const p = road[i];
      const d = (p.x - x) * (p.x - x) + (p.z - z) * (p.z - z);
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    }
    return road[best];
  }

  function lateral(x, z, p) {
    return (x - p.x) * p.lx + (z - p.z) * p.lz;
  }

  const objects = {};

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("missing " + src));
      img.src = src;
    });
  }

  async function loadSheets() {
    const man = window.STACK_MANIFEST.objects;
    const embedded = window.STACK_SHEETS || {};
    for (const id of Object.keys(man)) {
      const spec = man[id];
      const img = await loadImage(embedded[id] || "slices/" + spec.file);
      const c = document.createElement("canvas");
      c.width = img.width;
      c.height = img.height;
      const ctx = c.getContext("2d", { willReadFrequently: true });
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(img, 0, 0);
      const pixels = ctx.getImageData(0, 0, c.width, c.height).data;
      objects[id] = {
        id,
        name: spec.name,
        w: spec.w,
        h: spec.h,
        slices: spec.slices,
        pixels,
        role: spec.role,
      };
    }
  }

  function forward(heading) {
    return [-Math.sin(heading), -Math.cos(heading)];
  }

  function turnFromHeading(heading) {
    const f = forward(heading);
    return Math.atan2(f[1], f[0]) - Math.PI / 2;
  }

  function renderStack(obj, turn) {
    const sw = obj.w;
    const sh = obj.h;
    const count = obj.slices;
    const src = obj.pixels;
    const sheetW = sw * count;
    const cos = Math.cos(turn);
    const sin = Math.sin(turn);
    const cx = sw >> 1;
    const cy = sh >> 1;
    const corners = [
      [-cx, -cy],
      [sw - 1 - cx, -cy],
      [sw - 1 - cx, sh - 1 - cy],
      [-cx, sh - 1 - cy],
    ];
    let minDx = 1e9;
    let maxDx = -1e9;
    let minDy = 1e9;
    let maxDy = -1e9;
    for (const [sx, sy] of corners) {
      const rx = sx * cos - sy * sin;
      const ry = (sx * sin + sy * cos) * squash;
      if (rx < minDx) minDx = rx;
      if (rx > maxDx) maxDx = rx;
      if (ry < minDy) minDy = ry;
      if (ry > maxDy) maxDy = ry;
    }
    minDx = Math.floor(minDx) - 1;
    maxDx = Math.ceil(maxDx) + 1;
    minDy = Math.floor(minDy) - 1;
    maxDy = Math.ceil(maxDy) + 1;
    const top = -iround((count - 1) * spacing) + minDy;
    const bot = maxDy;
    const left = minDx;
    const right = maxDx;
    const bw = right - left + 1;
    const bh = bot - top + 1;
    const data = new Uint8ClampedArray(bw * bh * 4);
    for (let z = 0; z < count; z++) {
      const lift = iround(z * spacing);
      const ox = z * sw;
      for (let dy = minDy; dy <= maxDy; dy++) {
        const sy = -lift + dy - top;
        if (sy < 0 || sy >= bh) continue;
        const ry = dy / squash;
        for (let dx = minDx; dx <= maxDx; dx++) {
          const sx = dx - left;
          if (sx < 0 || sx >= bw) continue;
          const u = dx * cos + ry * sin;
          const v = -dx * sin + ry * cos;
          const ix = iround(u + cx);
          const iy = iround(v + cy);
          if (ix < 0 || iy < 0 || ix >= sw || iy >= sh) continue;
          const si = (iy * sheetW + ox + ix) * 4;
          if (src[si + 3] < 128) continue;
          const di = (sy * bw + sx) * 4;
          data[di] = src[si];
          data[di + 1] = src[si + 1];
          data[di + 2] = src[si + 2];
          data[di + 3] = 255;
        }
      }
    }
    return { w: bw, h: bh, data, ax: -left, ay: -top };
  }

  function outlineSprite(spr) {
    const w = spr.w;
    const h = spr.h;
    const s = spr.data;
    const o = new Uint8ClampedArray(s);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        if (s[i + 3] >= 128) continue;
        let hit = false;
        if (x > 0 && s[i - 4 + 3] >= 128) hit = true;
        else if (x + 1 < w && s[i + 4 + 3] >= 128) hit = true;
        else if (y > 0 && s[i - w * 4 + 3] >= 128) hit = true;
        else if (y + 1 < h && s[i + w * 4 + 3] >= 128) hit = true;
        if (hit) {
          o[i] = INK[0];
          o[i + 1] = INK[1];
          o[i + 2] = INK[2];
          o[i + 3] = 255;
        }
      }
    }
    spr.data = o;
  }

  function bakeStatic() {
    for (const id of Object.keys(objects)) {
      const obj = objects[id];
      if (obj.role === "car") continue;
      const spr = renderStack(obj, 0);
      outlineSprite(spr);
      obj.baked = spr;
    }
  }

  let cars = [];
  let props = [];
  let finished = false;
  let trailTick = 0;

  function makeProps() {
    props = [];
    for (let s = 4; s <= ROAD_LEN - 2; s += 6) {
      if (Math.abs(s - FINISH) < 3) continue;
      for (const side of [-1, 1]) {
        const p = roadAt(s);
        const lat = side * (HALF_W + 0.35);
        props.push({
          id: "post",
          x: p.x + p.lx * lat,
          z: p.z + p.lz * lat,
        });
      }
    }
    for (let s = 6; s <= ROAD_LEN; s += 9) {
      const p = roadAt(s);
      const side = -1;
      const lat = side * (HALF_W + 4.2 + (s % 5) * 0.2);
      props.push({ id: "cedar", x: p.x + p.lx * lat, z: p.z + p.lz * lat });
      if (s % 27 === 6) {
        const latIn = HALF_W + 4.6;
        props.push({ id: "cedar", x: p.x + p.lx * latIn, z: p.z + p.lz * latIn });
      }
    }
    for (let s = 10; s < ROAD_LEN; s += 18) {
      const p = roadAt(s);
      const lat = -(HALF_W + 0.9);
      props.push({
        id: "lamp",
        x: p.x + p.lx * lat,
        z: p.z + p.lz * lat,
        lamp: true,
      });
    }
    const hutP = roadAt(72);
    props.push({
      id: "hut",
      x: hutP.x + hutP.lx * (HALF_W + 2.4),
      z: hutP.z + hutP.lz * (HALF_W + 2.4),
    });
    for (const side of [-1, 1]) {
      const p = roadAt(FINISH);
      props.push({
        id: "gate",
        x: p.x + p.lx * side * (HALF_W + 0.15),
        z: p.z + p.lz * side * (HALF_W + 0.15),
      });
    }
  }

  function reset() {
    finished = false;
    const spawn = [
      { id: "kite", name: "KITE", s: 6, speed: 14, lane: -0.15, ai: false },
      { id: "daybreak", name: "DAYBREAK", s: 14, speed: 15.3, lane: 1.15, ai: true },
      { id: "hatchet", name: "HATCHET", s: 21, speed: 15.7, lane: -1.05, ai: true },
      { id: "chalk", name: "CHALK", s: 28, speed: 14.9, lane: 0.25, ai: true },
    ];
    cars = spawn.map((sp) => {
      const p = roadAt(sp.s);
      const [fvx, fvz] = forward(p.heading);
      return {
        id: sp.id,
        name: sp.name,
        ai: sp.ai,
        s: sp.s,
        lane: sp.lane,
        speed: sp.speed,
        heading: p.heading,
        x: p.x + p.lx * sp.lane,
        z: p.z + p.lz * sp.lane,
        vx: fvx * sp.speed,
        vz: fvz * sp.speed,
        trail: [],
        sheet: objects[sp.id],
      };
    });
    makeProps();
  }

  function separate() {
    for (let i = 0; i < cars.length; i++) {
      for (let j = i + 1; j < cars.length; j++) {
        const a = cars[i];
        const b = cars[j];
        let dx = b.x - a.x;
        let dz = b.z - a.z;
        const d = Math.hypot(dx, dz);
        if (d > 2.35 || d < 1e-4) continue;
        const push = (2.35 - d) * 0.5;
        dx /= d;
        dz /= d;
        a.x -= dx * push;
        a.z -= dz * push;
        b.x += dx * push;
        b.z += dz * push;
        if (!a.ai) a.speed *= 0.992;
        if (!b.ai) b.speed *= 0.992;
      }
    }
  }

  function inputFor(car, auto) {
    if (car.ai) return null;
    if (auto) {
      const p = roadAt(car.s + 8);
      const dx = p.x - car.x;
      const dz = p.z - car.z;
      const desired = Math.atan2(-dx, -dz);
      const diff = wrap(desired - car.heading);
      return { steer: clamp(diff * 2.4, -1, 1), throttle: finished ? 0 : 1 };
    }
    let steer = 0;
    let throttle = 0;
    if (keys["a"] || keys["arrowleft"]) steer -= 1;
    if (keys["d"] || keys["arrowright"]) steer += 1;
    if (keys["w"] || keys["arrowup"]) throttle += 1;
    if (keys["s"] || keys["arrowdown"]) throttle -= 1;
    return { steer, throttle };
  }

  function step(dt, auto) {
    trailTick++;
    for (const car of cars) {
      if (car.ai) {
        if (!finished) car.s += car.speed * dt;
        if (car.s > ROAD_LEN) car.s = ROAD_LEN;
        const p = roadAt(car.s);
        car.heading = p.heading;
        car.x = p.x + p.lx * car.lane;
        car.z = p.z + p.lz * car.lane;
      } else {
        const inp = inputFor(car, auto);
        const rate = 1.65 * (0.4 + 0.6 * clamp(Math.abs(car.speed) / 14, 0, 1));
        car.heading = wrap(car.heading + inp.steer * rate * dt);
        let accel = -1.6;
        if (inp.throttle > 0) accel = 11;
        if (inp.throttle < 0) accel = -16;
        if (!finished) car.speed = clamp(car.speed + accel * dt, -3.5, 18.5);
        else car.speed *= Math.pow(0.02, dt);
        const [fvx, fvz] = forward(car.heading);
        car.x += fvx * car.speed * dt;
        car.z += fvz * car.speed * dt;
        const near = nearestPoint(car.x, car.z, Math.round(car.s));
        const lat = lateral(car.x, car.z, near);
        const limit = HALF_W - 0.95;
        if (Math.abs(lat) > limit) {
          const sign = lat < 0 ? -1 : 1;
          const over = Math.abs(lat) - limit;
          car.x -= near.lx * sign * over;
          car.z -= near.lz * sign * over;
          car.speed *= 0.99;
        }
        car.s = near.s;
        if (car.s >= FINISH) finished = true;
      }
      if (trailTick % 2 === 0 && car.speed > 7) {
        const [fvx, fvz] = forward(car.heading);
        const rx = -fvz;
        const rz = fvx;
        car.trail.push({ x: car.x - fvx * 1.7 + rx * 0.55, z: car.z - fvz * 1.7 + rz * 0.55 });
        car.trail.push({ x: car.x - fvx * 1.7 - rx * 0.55, z: car.z - fvz * 1.7 - rz * 0.55 });
        if (car.trail.length > 16) car.trail.splice(0, car.trail.length - 16);
      }
    }
    separate();
  }

  function worldToScreen(x, z) {
    return [
      iround((x - camX) * PPM + ANCHOR_X),
      iround((z - camZ) * PPM * squash + ANCHOR_Y),
    ];
  }

  function fogAmt(dist, sy) {
    const d = clamp((dist - FOG_NEAR) / (FOG_FAR - FOG_NEAR), 0, 1);
    const sky = clamp((168 - sy) / 168, 0, 1);
    const s = sky * sky;
    return d > s ? d : s;
  }

  function writePx(x, y, rgb) {
    if (x < 0 || y < 0 || x >= VIEW_W || y >= VIEW_H) return;
    const i = (y * VIEW_W + x) * 4;
    frame.data[i] = rgb[0];
    frame.data[i + 1] = rgb[1];
    frame.data[i + 2] = rgb[2];
    frame.data[i + 3] = 255;
  }

  function clearSky() {
    const d = frame.data;
    for (let y = 0; y < VIEW_H; y++) {
      const t = Math.pow(Math.min(1, y / 188), 0.82);
      const r = (ZENITH[0] + (FOG[0] - ZENITH[0]) * t) * 255;
      const g = (ZENITH[1] + (FOG[1] - ZENITH[1]) * t) * 255;
      const b = (ZENITH[2] + (FOG[2] - ZENITH[2]) * t) * 255;
      for (let x = 0; x < VIEW_W; x++) {
        const i = (y * VIEW_W + x) * 4;
        d[i] = r;
        d[i + 1] = g;
        d[i + 2] = b;
        d[i + 3] = 255;
      }
    }
    depth.fill(-1);
  }

  function lampLight(x, z) {
    let light = 0;
    for (const prop of props) {
      if (!prop.lamp) continue;
      const dx = x - prop.x;
      const dz = z - prop.z;
      const d2 = dx * dx + dz * dz;
      if (d2 < 196) light += Math.exp(-d2 / 56);
    }
    return light > 1 ? 1 : light;
  }

  function drawGround() {
    const player = cars[0];
    const s0 = clamp(player.s - 16, 0, ROAD_LEN);
    const s1 = clamp(player.s + 42, 0, ROAD_LEN);
    const ds = 1 / (PPM * squash);
    const dl = 1 / PPM;
    for (let s = s1; s >= s0; s -= ds) {
      const p = roadAt(s);
      for (let lat = -HALF_W - 8; lat <= HALF_W + 8; lat += dl) {
        const x = p.x + p.lx * lat;
        const z = p.z + p.lz * lat;
        const sx = iround((x - camX) * PPM + ANCHOR_X);
        const sy = iround((z - camZ) * PPM * squash + ANCHOR_Y);
        if (sx < 0 || sy < 0 || sx >= VIEW_W || sy >= VIEW_H) continue;
        const dist = Math.hypot(x - camX, z - camZ);
        const f = fogAmt(dist, sy);
        if (f > 0.97) continue;
        const alat = Math.abs(lat);
        let base;
        if (alat < HALF_W) {
          base = [0.055, 0.062, 0.085];
          const edge = HALF_W - 0.22;
          if (Math.abs(alat - edge) < 0.09) base = [0.30, 0.28, 0.24];
          if (alat < 0.09 && (Math.floor(s) & 3) < 2) base = [0.26, 0.25, 0.22];
          if (s >= FINISH && s <= FINISH + 1.35) {
            const check = (Math.floor((lat + HALF_W) * 2) + Math.floor(s * 2)) & 1;
            base = check ? [0.48, 0.46, 0.40] : [0.07, 0.07, 0.08];
          }
          const light = lampLight(x, z);
          if (light > 0.03) base = lerp3(base, [0.42, 0.34, 0.22], Math.min(0.5, light * 0.48));
        } else if (alat < HALF_W + 1.5) {
          base = [0.045, 0.055, 0.048];
        } else {
          base = [0.035, 0.048, 0.046];
        }
        const rgb = lerp3(base, FOG, f);
        const i = (sy * VIEW_W + sx) * 4;
        frame.data[i] = rgb[0] * 255;
        frame.data[i + 1] = rgb[1] * 255;
        frame.data[i + 2] = rgb[2] * 255;
        depth[sy * VIEW_W + sx] = dist;
      }
    }
  }

  function drawBanner() {
    const p = roadAt(FINISH);
    const pts = [];
    for (const side of [-1, 1]) {
      const lat = side * HALF_W;
      const x = p.x + p.lx * lat;
      const z = p.z + p.lz * lat;
      const sc = worldToScreen(x, z);
      pts.push(sc);
    }
    const lift0 = iround(1.7 * PPM);
    const lift1 = iround(3.05 * PPM);
    const quad = [
      { x: pts[0][0], y: pts[0][1] - lift0 },
      { x: pts[1][0], y: pts[1][1] - lift0 },
      { x: pts[1][0], y: pts[1][1] - lift1 },
      { x: pts[0][0], y: pts[0][1] - lift1 },
    ];
    const dist = Math.hypot(p.x - camX, p.z - camZ);
    fillConvex(quad, (x, y) => {
      const check = ((x >> 4) + (y >> 3)) & 1;
      let base = check ? [0.50, 0.48, 0.42] : [0.08, 0.08, 0.09];
      const f = fogAmt(dist, y);
      const rgb = lerp3(base, FOG, f);
      writePx(x, y, [rgb[0] * 255, rgb[1] * 255, rgb[2] * 255]);
      depth[y * VIEW_W + x] = dist;
    });
  }

  function fillConvex(pts, shade) {
    let minY = 1e9;
    let maxY = -1e9;
    for (const p of pts) {
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    }
    minY = Math.max(0, Math.floor(minY));
    maxY = Math.min(VIEW_H - 1, Math.ceil(maxY));
    for (let y = minY; y <= maxY; y++) {
      const xs = [];
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i];
        const b = pts[(i + 1) % pts.length];
        if ((a.y <= y && b.y > y) || (b.y <= y && a.y > y)) {
          const t = (y - a.y) / (b.y - a.y);
          xs.push(a.x + (b.x - a.x) * t);
        }
      }
      if (xs.length < 2) continue;
      let x0 = xs[0];
      let x1 = xs[0];
      for (const x of xs) {
        if (x < x0) x0 = x;
        if (x > x1) x1 = x;
      }
      const a0 = Math.max(0, Math.ceil(x0));
      const a1 = Math.min(VIEW_W - 1, Math.floor(x1));
      for (let x = a0; x <= a1; x++) shade(x, y);
    }
  }

  function darkenOval(cx, cy, rx, ry) {
    for (let y = -ry; y <= ry; y++) {
      const sy = cy + y;
      if (sy < 0 || sy >= VIEW_H) continue;
      for (let x = -rx; x <= rx; x++) {
        const sx = cx + x;
        if (sx < 0 || sx >= VIEW_W) continue;
        const e = (x * x) / (rx * rx) + (y * y) / (ry * ry);
        if (e > 1) continue;
        const i = (sy * VIEW_W + sx) * 4;
        if (depth[sy * VIEW_W + sx] < 0) continue;
        const k = e < 0.45 ? 0.45 : 0.68;
        frame.data[i] *= k;
        frame.data[i + 1] *= k;
        frame.data[i + 2] *= k;
      }
    }
  }

  function addLight(cx, cy, rad, rgb, gain) {
    const r = Math.ceil(rad);
    for (let y = -r; y <= r; y++) {
      const sy = cy + y;
      if (sy < 0 || sy >= VIEW_H) continue;
      for (let x = -r; x <= r; x++) {
        const sx = cx + x;
        if (sx < 0 || sx >= VIEW_W) continue;
        const d = Math.hypot(x, y) / rad;
        if (d > 1) continue;
        const k = (1 - d) * (1 - d) * gain;
        const i = (sy * VIEW_W + sx) * 4;
        frame.data[i] = Math.min(225, frame.data[i] + rgb[0] * k);
        frame.data[i + 1] = Math.min(225, frame.data[i + 1] + rgb[1] * k);
        frame.data[i + 2] = Math.min(225, frame.data[i + 2] + rgb[2] * k);
      }
    }
  }

  function headlightThrow(car) {
    const [fvx, fvz] = forward(car.heading);
    const rx = -fvz;
    const rz = fvx;
    for (let t = 1.3; t < 6.5; t += 0.35) {
      const w = 0.35 + t * 0.2;
      const fade = (1 - t / 6.5) * 0.16;
      for (let u = -w; u <= w; u += 0.35) {
        const x = car.x + fvx * t + rx * u;
        const z = car.z + fvz * t + rz * u;
        const sc = worldToScreen(x, z);
        const sx = sc[0];
        const sy = sc[1];
        if (sx < 0 || sy < 0 || sx >= VIEW_W || sy >= VIEW_H) continue;
        if (depth[sy * VIEW_W + sx] < 0) continue;
        const k = fade * (1 - Math.abs(u) / w);
        const i = (sy * VIEW_W + sx) * 4;
        frame.data[i] = Math.min(210, frame.data[i] + 90 * k);
        frame.data[i + 1] = Math.min(200, frame.data[i + 1] + 70 * k);
        frame.data[i + 2] = Math.min(170, frame.data[i + 2] + 40 * k);
      }
    }
  }

  function blitSprite(spr, gx, gy, dist) {
    const x0 = gx - spr.ax;
    const y0 = gy - spr.ay;
    for (let y = 0; y < spr.h; y++) {
      const sy = y0 + y;
      if (sy < 0 || sy >= VIEW_H) continue;
      const f = fogAmt(dist, sy);
      for (let x = 0; x < spr.w; x++) {
        const sx = x0 + x;
        if (sx < 0 || sx >= VIEW_W) continue;
        const si = (y * spr.w + x) * 4;
        if (spr.data[si + 3] < 128) continue;
        const r = spr.data[si] / 255;
        const g = spr.data[si + 1] / 255;
        const b = spr.data[si + 2] / 255;
        const i = (sy * VIEW_W + sx) * 4;
        frame.data[i] = (r + (FOG[0] - r) * f) * 255;
        frame.data[i + 1] = (g + (FOG[1] - g) * f) * 255;
        frame.data[i + 2] = (b + (FOG[2] - b) * f) * 255;
        frame.data[i + 3] = 255;
        depth[sy * VIEW_W + sx] = dist;
      }
    }
  }

  function drawStacks() {
    const drawables = [];
    for (const prop of props) {
      const sc = worldToScreen(prop.x, prop.z);
      drawables.push({
        y: sc[1],
        x: sc[0],
        dist: Math.hypot(prop.x - camX, prop.z - camZ),
        spr: objects[prop.id].baked,
        lamp: prop.lamp,
        kind: "prop",
      });
    }
    for (const car of cars) {
      const sc = worldToScreen(car.x, car.z);
      drawables.push({
        y: sc[1],
        x: sc[0],
        dist: Math.hypot(car.x - camX, car.z - camZ),
        car,
        kind: "car",
      });
    }
    drawables.sort((a, b) => a.y - b.y);
    for (const item of drawables) {
      if (item.kind === "car") {
        darkenOval(item.x, item.y + 2, 16, 7);
        headlightThrow(item.car);
        const spr = renderStack(item.car.sheet, turnFromHeading(item.car.heading));
        outlineSprite(spr);
        blitSprite(spr, item.x, item.y, item.dist);
        const [fvx, fvz] = forward(item.car.heading);
        const rx = -fvz;
        const rz = fvx;
        const nose = worldToScreen(item.car.x + fvx * 1.75, item.car.z + fvz * 1.75);
        const tail = worldToScreen(item.car.x - fvx * 1.7, item.car.z - fvz * 1.7);
        const left = worldToScreen(item.car.x + fvx * 1.7 + rx * 0.62, item.car.z + fvz * 1.7 + rz * 0.62);
        const right = worldToScreen(item.car.x + fvx * 1.7 - rx * 0.62, item.car.z + fvz * 1.7 - rz * 0.62);
        const tl = worldToScreen(item.car.x - fvx * 1.65 + rx * 0.55, item.car.z - fvz * 1.65 + rz * 0.55);
        const tr = worldToScreen(item.car.x - fvx * 1.65 - rx * 0.55, item.car.z - fvz * 1.65 - rz * 0.55);
        addLight(left[0], left[1] - 4, 5, [255, 236, 196], 0.55);
        addLight(right[0], right[1] - 4, 5, [255, 236, 196], 0.55);
        addLight(tl[0], tl[1] - 3, 3.5, [255, 40, 28], 0.7);
        addLight(tr[0], tr[1] - 3, 3.5, [255, 40, 28], 0.7);
        void nose;
        void tail;
      } else {
        blitSprite(item.spr, item.x, item.y, item.dist);
        if (item.lamp) {
          const head = item.y - iround((objects.lamp.slices - 4) * spacing);
          addLight(item.x, head, 8, [240, 200, 148], 0.42);
        }
      }
    }
    for (const car of cars) {
      const n = car.trail.length;
      for (let i = 0; i < n; i++) {
        const t = car.trail[i];
        const sc = worldToScreen(t.x, t.z);
        const k = (i / n) * 0.45;
        addLight(sc[0], sc[1], 1.6, [180, 24, 18], k);
      }
    }
  }

  function dither() {
    const d = frame.data;
    for (let y = 0; y < VIEW_H; y++) {
      for (let x = 0; x < VIEW_W; x++) {
        const i = (y * VIEW_W + x) * 4;
        let r = d[i] / 255;
        let g = d[i + 1] / 255;
        let b = d[i + 2] / 255;
        const lum = 0.299 * r + 0.587 * g + 0.114 * b;
        r = lum + (r - lum) * 1.05;
        g = lum + (g - lum) * 1.05;
        b = lum + (b - lum) * 1.05;
        const bay = BAYER[((y & 3) << 2) + (x & 3)] / 16 - 0.5;
        d[i] = quant(r, bay);
        d[i + 1] = quant(g, bay);
        d[i + 2] = quant(b, bay);
      }
    }
  }

  function quant(v, bay) {
    if (v < 0) v = 0;
    else if (v > 1) v = 1;
    let q = Math.floor(v * 31 + 0.5 + bay);
    if (q < 0) q = 0;
    else if (q > 31) q = 31;
    return Math.round((q / 31) * 255);
  }

  function drawText(text, x, y, scale, color) {
    vctx.fillStyle = color;
    let cx = x | 0;
    const cy = y | 0;
    for (let n = 0; n < text.length; n++) {
      const g = FONT[text[n]] || FONT[" "];
      for (let row = 0; row < 7; row++) {
        const bits = g[row];
        for (let col = 0; col < 5; col++) {
          if (bits & (1 << (4 - col))) {
            vctx.fillRect(cx + col * scale, cy + row * scale, scale, scale);
          }
        }
      }
      cx += 6 * scale;
    }
  }

  function textPair(text, x, y, scale, color) {
    drawText(text, x + 2, y + 2, scale, "#040810");
    drawText(text, x, y, scale, color);
  }

  function placeOf(car) {
    let place = 1;
    for (const other of cars) {
      if (other !== car && other.s > car.s) place++;
    }
    return place;
  }

  function drawUi() {
    const player = cars[0];
    const kmh = Math.round(Math.abs(player.speed) * 3.6);
    const kmhText = String(kmh).padStart(3, "0");
    textPair("MIDNIGHT APEX", 28, 22, 4, "#F3EEE4");
    textPair("TOUGE NIGHT", 28, 58, 3, "#C8C0B0");
    textPair(player.name, 28, 92, 3, "#F0C894");
    const right = "P" + placeOf(player) + " / 4";
    textPair(right, 1040, 22, 4, "#F3EEE4");
    textPair(kmhText + " KM/H", 980, 58, 3, "#F3EEE4");
    const dist = Math.max(0, Math.round(FINISH - player.s));
    textPair(dist === 0 ? "FINISH" : dist + " M", 1048, 92, 3, "#C8C0B0");
    textPair(
      "WASD DRIVE   STACK " + spacing.toFixed(1) + "   SQUASH " + squash.toFixed(2),
      28,
      900,
      2,
      "#B7C0CC"
    );
    if (finished) {
      textPair("FINISH", 520, 400, 6, "#F3EEE4");
      const order = cars.slice().sort((a, b) => b.s - a.s);
      for (let i = 0; i < order.length; i++) {
        textPair(i + 1 + "  " + order[i].name, 500, 460 + i * 28, 3, "#F3EEE4");
      }
    }
  }

  function drawFrame() {
    const player = cars[0];
    camX = player.x;
    camZ = player.z;
    clearSky();
    drawGround();
    drawBanner();
    drawStacks();
    dither();
    wctx.putImageData(frame, 0, 0);
    vctx.imageSmoothingEnabled = false;
    vctx.fillStyle = "#000";
    vctx.fillRect(0, 0, 1280, 960);
    vctx.drawImage(world, 0, 0, 1280, 960);
    drawUi();
  }

  let last = 0;
  let acc = 0;
  function loop(now) {
    if (!last) last = now;
    acc += Math.min(0.05, (now - last) / 1000);
    last = now;
    while (acc >= 1 / 60) {
      step(1 / 60, false);
      acc -= 1 / 60;
    }
    drawFrame();
    requestAnimationFrame(loop);
  }

  window.addEventListener("keydown", (e) => {
    keys[e.key.toLowerCase()] = true;
    const steerKeys = ["arrowup", "arrowdown", "arrowleft", "arrowright", " "];
    if (steerKeys.indexOf(e.key.toLowerCase()) >= 0) e.preventDefault();
    if (e.repeat) return;
    let rebake = false;
    if (e.key === "[") {
      spacing = Math.max(0, Math.round((spacing - 0.5) * 2) / 2);
      rebake = true;
    } else if (e.key === "]") {
      spacing = Math.min(3, Math.round((spacing + 0.5) * 2) / 2);
      rebake = true;
    } else if (e.key === ",") {
      squash = Math.max(0.45, Math.round((squash - 0.05) * 100) / 100);
      rebake = true;
    } else if (e.key === ".") {
      squash = Math.min(1, Math.round((squash + 0.05) * 100) / 100);
      rebake = true;
    } else if (e.key === "r" || e.key === "R") {
      reset();
    }
    if (rebake) bakeStatic();
  });
  window.addEventListener("keyup", (e) => {
    keys[e.key.toLowerCase()] = false;
  });

  window.addEventListener("error", (e) => {
    setStatus("error: " + (e.message || "unknown"));
  });

  async function main() {
    if (!window.STACK_MANIFEST) throw new Error("manifest missing");
    await loadSheets();
    bakeStatic();
    reset();
    if (params.has("t")) {
      const n = Math.max(0, Math.round(parseFloat(params.get("t")) * 60));
      for (let i = 0; i < n; i++) step(1 / 60, true);
      drawFrame();
      setStatus("ready");
      return;
    }
    setStatus("ready");
    requestAnimationFrame(loop);
  }

  main().catch((err) => setStatus("error: " + err.message));
})();
