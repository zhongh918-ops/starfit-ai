/* Compose campaign posters at runtime: selected face + product + names. */
(function (global) {
  function asset(path) {
    return global.Match99Base && global.Match99Base.withBase ? global.Match99Base.withBase(path) : path;
  }
  const MOCKUPS = {
    lobby: { src: '/assets/campaign/mockups/lobby.png', x: 0.367, y: 0.090, w: 0.275, h: 0.820 },
    metro: { src: '/assets/campaign/mockups/metro.png', x: 0.119, y: 0.285, w: 0.400, h: 0.530, radius: 0.016 },
    phone: { src: '/assets/campaign/mockups/phone.png', x: 0.358, y: 0.434, w: 0.298, h: 0.348, radius: 0.055 }
  };

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      if (!src) {
        reject(new Error('empty src'));
        return;
      }
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error(src));
      img.src = src;
    });
  }

  function cover(ctx, img, x, y, w, h, biasY, biasX) {
    const ir = img.width / img.height;
    const r = w / h;
    let sx = 0;
    let sy = 0;
    let sw = img.width;
    let sh = img.height;
    if (ir > r) {
      sw = img.height * r;
      const bx = biasX == null ? 0.5 : biasX;
      sx = Math.max(0, Math.min(img.width - sw, (img.width - sw) * bx));
    } else {
      sh = img.width / r;
      sy = Math.max(0, (img.height - sh) * (biasY == null ? 0.18 : biasY));
    }
    ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
  }

  function contain(ctx, img, x, y, w, h) {
    const ir = img.width / img.height;
    const r = w / h;
    let dw = w;
    let dh = h;
    let dx = x;
    let dy = y;
    if (ir > r) {
      dh = w / ir;
      dy = y + (h - dh) / 2;
    } else {
      dw = h * ir;
      dx = x + (w - dw) / 2;
    }
    ctx.drawImage(img, dx, dy, dw, dh);
  }

  function fitText(ctx, text, maxWidth, maxSize, minSize) {
    let size = maxSize;
    ctx.font = '700 ' + size + 'px "Helvetica Neue","PingFang SC",sans-serif';
    while (size > minSize && ctx.measureText(text).width > maxWidth) {
      size -= 1;
      ctx.font = '700 ' + size + 'px "Helvetica Neue","PingFang SC",sans-serif';
    }
    return size;
  }

  async function drawPoster(spec) {
    const w = 720;
    const h = 1200;
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#f6f3ee';
    ctx.fillRect(0, 0, w, h);

    if (spec.portraitImg) cover(ctx, spec.portraitImg, 0, 0, w, h, 0.12);
    else {
      ctx.fillStyle = '#1b1d16';
      ctx.fillRect(0, 0, w, h);
    }

    const g = ctx.createLinearGradient(0, h * 0.55, 0, h);
    g.addColorStop(0, 'rgba(18, 16, 14, 0)');
    g.addColorStop(1, 'rgba(18, 16, 14, 0.55)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    if (spec.productImg) {
      const pw = 250;
      const ph = 320;
      const px = w - pw - 36;
      const py = h - ph - 150;
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,0.28)';
      ctx.shadowBlur = 28;
      ctx.shadowOffsetY = 10;
      contain(ctx, spec.productImg, px, py, pw, ph);
      ctx.restore();
    }

    ctx.fillStyle = '#ffffff';
    ctx.textBaseline = 'top';
    ctx.font = '600 14px "Helvetica Neue","PingFang SC",sans-serif';
    const brand = String(spec.product || '').toUpperCase();
    ctx.fillText(brand, 36, 40);
    if (spec.name) {
      ctx.font = '500 13px "Helvetica Neue","PingFang SC",sans-serif';
      ctx.fillText('×  ' + spec.name, 36, 62);
    }
    const slogan = String(spec.slogan || '').toUpperCase();
    if (slogan) {
      const sSize = fitText(ctx, slogan, w - 72, 42, 22);
      ctx.font = '700 ' + sSize + 'px "Helvetica Neue","PingFang SC",sans-serif';
      ctx.textBaseline = 'bottom';
      ctx.fillText(slogan, 36, h - 48);
    }
    return c;
  }

  async function placeOnMockup(kind, poster, opts) {
    const slot = MOCKUPS[kind];
    const plate = await loadImage(asset(slot.src));
    const c = document.createElement('canvas');
    c.width = plate.width;
    c.height = plate.height;
    const ctx = c.getContext('2d');
    ctx.drawImage(plate, 0, 0);
    const x = Math.round(slot.x * plate.width);
    const y = Math.round(slot.y * plate.height);
    const w = Math.round(slot.w * plate.width);
    const h = Math.round(slot.h * plate.height);
    const radius = slot.radius ? Math.round(Math.min(w, h) * slot.radius) : 0;
    const biasY = opts && opts.biasY != null ? opts.biasY : 0.18;
    const biasX = opts && opts.biasX != null ? opts.biasX : 0.5;
    ctx.save();
    ctx.beginPath();
    if (radius && ctx.roundRect) ctx.roundRect(x, y, w, h, radius);
    else ctx.rect(x, y, w, h);
    ctx.clip();
    ctx.fillStyle = '#111';
    ctx.fillRect(x, y, w, h);
    cover(ctx, poster, x, y, w, h, biasY, biasX);
    ctx.restore();
    return c;
  }

  async function composeScenes(art, opts) {
    const [lobby, metro, phone] = await Promise.all([
      placeOnMockup('lobby', art, opts),
      placeOnMockup('metro', art, opts),
      placeOnMockup('phone', art, opts)
    ]);
    return {
      lobby: lobby.toDataURL('image/jpeg', 0.92),
      metro: metro.toDataURL('image/jpeg', 0.92),
      phone: phone.toDataURL('image/jpeg', 0.92)
    };
  }

  async function compose(spec) {
    const [portraitImg, productImg] = await Promise.all([
      spec.portrait ? loadImage(spec.portrait).catch(() => null) : Promise.resolve(null),
      spec.productImg ? loadImage(spec.productImg).catch(() => null) : Promise.resolve(null)
    ]);
    const poster = await drawPoster({
      product: spec.product,
      name: spec.name,
      slogan: spec.slogan,
      productLine: spec.productLine,
      portraitImg,
      productImg
    });
    const scenes = await composeScenes(poster);
    scenes.hero = poster.toDataURL('image/jpeg', 0.92);
    return scenes;
  }

  function apply(urls) {
    if (!urls) return;
    document.querySelectorAll('[data-cs-scene]').forEach((btn) => {
      const key = btn.getAttribute('data-cs-scene');
      const img = btn.querySelector('img');
      if (img && urls[key]) img.src = urls[key];
    });
    const main = document.querySelector('.cs-preview img');
    const active = document.querySelector('[data-cs-scene].on');
    const key = (active && active.getAttribute('data-cs-scene')) || 'lobby';
    if (main && urls[key]) main.src = urls[key];
  }

  function probe(src) {
    return loadImage(src).then(() => src).catch(() => '');
  }

  async function resolveFusionArt(productId, slug, family) {
    const keys = [];
    const push = (k) => { if (k && keys.indexOf(k) < 0) keys.push(k); };
    push(family);
    push(productId);
    if (family === 'beauty') push('beauty');
    for (let i = 0; i < keys.length; i++) {
      const src = asset('/assets/campaign/fusion/' + keys[i] + '/' + slug + '/hero.png');
      const ok = await probe(src);
      if (ok) return ok;
    }
    return '';
  }

  async function composeFromArt(src) {
    const art = await loadImage(src);
    const beauty = /\/beauty\//.test(String(src || ''));
    return composeScenes(art, beauty ? { biasX: 0.72, biasY: 0.12 } : undefined);
  }

  global.Match99Poster = { compose, composeScenes, composeFromArt, apply, resolveFusionArt, loadImage };
})(window);
