/* Compose campaign posters at runtime: selected face + product + names. */
(function (global) {
  function asset(path) {
    return global.Match99Base && global.Match99Base.withBase ? global.Match99Base.withBase(path) : path;
  }
  const MOCKUPS = {
    lobby: { src: '/assets/campaign/mockups/lobby.png', x: 0.388, y: 0.072, w: 0.226, h: 0.856 },
    metro: { src: '/assets/campaign/mockups/metro.png', x: 0.186, y: 0.208, w: 0.236, h: 0.588 },
    phone: { src: '/assets/campaign/mockups/phone.png', x: 0.318, y: 0.332, w: 0.364, h: 0.392 }
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

  function cover(ctx, img, x, y, w, h, biasY) {
    const ir = img.width / img.height;
    const r = w / h;
    let sx = 0;
    let sy = 0;
    let sw = img.width;
    let sh = img.height;
    if (ir > r) {
      sw = img.height * r;
      sx = (img.width - sw) / 2;
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
    ctx.fillStyle = '#1b1d16';
    ctx.fillRect(0, 0, w, h);

    const pad = 48;
    ctx.fillStyle = '#f4f1ea';
    ctx.textBaseline = 'top';
    ctx.font = '700 15px "Helvetica Neue","PingFang SC",sans-serif';
    ctx.letterSpacing = '0.16em';
    ctx.fillText(String(spec.product || 'AEROSTRIDE').toUpperCase(), pad, 44);
    ctx.letterSpacing = '0';
    ctx.font = '600 22px "Helvetica Neue","PingFang SC",sans-serif';
    ctx.fillStyle = '#c8e86a';
    ctx.fillText('×  ' + (spec.name || ''), pad, 72);

    const slogan = String(spec.slogan || 'MOVE BETWEEN.').toUpperCase();
    ctx.fillStyle = '#ffffff';
    const sSize = fitText(ctx, slogan, w - pad * 2, 58, 28);
    ctx.font = '700 ' + sSize + 'px "Helvetica Neue","PingFang SC",sans-serif';
    ctx.fillText(slogan, pad, 112);

    const hasProduct = !!spec.productImg;
    const bandH = hasProduct ? 250 : 120;
    const faceY = 200;
    const faceH = h - faceY - bandH - 28;
    const faceW = w - pad * 2;
    ctx.save();
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(pad, faceY, faceW, faceH, 22);
    else ctx.rect(pad, faceY, faceW, faceH);
    ctx.clip();
    ctx.fillStyle = '#2a2e22';
    ctx.fillRect(pad, faceY, faceW, faceH);
    if (spec.portraitImg) cover(ctx, spec.portraitImg, pad, faceY, faceW, faceH, 0.12);
    ctx.restore();

    const bandY = h - bandH;
    ctx.fillStyle = '#f4f1ea';
    ctx.fillRect(0, bandY, w, bandH);
    ctx.fillStyle = '#1b1d16';
    ctx.font = '700 13px "Helvetica Neue","PingFang SC",sans-serif';
    ctx.fillText(String(spec.productLine || spec.product || '').toUpperCase(), pad, bandY + 22);
    if (spec.productImg) {
      contain(ctx, spec.productImg, pad, bandY + 48, w - pad * 2, bandH - 70);
    } else {
      ctx.font = '600 20px "Helvetica Neue","PingFang SC",sans-serif';
      ctx.fillText(spec.product || '', pad, bandY + 56);
    }
    return c;
  }

  async function placeOnMockup(kind, poster) {
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
    ctx.fillStyle = '#111';
    ctx.fillRect(x, y, w, h);
    ctx.drawImage(poster, x, y, w, h);
    return c;
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
    const [lobby, metro, phone] = await Promise.all([
      placeOnMockup('lobby', poster),
      placeOnMockup('metro', poster),
      placeOnMockup('phone', poster)
    ]);
    return {
      hero: poster.toDataURL('image/jpeg', 0.92),
      lobby: lobby.toDataURL('image/jpeg', 0.9),
      metro: metro.toDataURL('image/jpeg', 0.9),
      phone: phone.toDataURL('image/jpeg', 0.9)
    };
  }

  function apply(urls) {
    if (!urls) return;
    document.querySelectorAll('[data-cs-scene]').forEach((btn) => {
      const key = btn.getAttribute('data-cs-scene');
      const img = btn.querySelector('img');
      if (img && urls[key]) img.src = urls[key];
    });
    const main = document.querySelector('.cs-visual img');
    const active = document.querySelector('[data-cs-scene].on');
    const key = (active && active.getAttribute('data-cs-scene')) || 'hero';
    if (main && urls[key]) main.src = urls[key];
  }

  function probe(src) {
    return loadImage(src).then(() => src).catch(() => '');
  }

  async function resolveFusion(productId, slug) {
    const keys = ['hero', 'hold', 'feature'];
    const urls = {};
    for (const key of keys) {
      const src = asset('/assets/campaign/fusion/' + productId + '/' + slug + '/' + key + '.png');
      urls[key] = await probe(src);
    }
    if (!urls.hero) return null;
    urls.hold = urls.hold || urls.hero;
    urls.feature = urls.feature || urls.hold || urls.hero;
    return urls;
  }

  global.Match99Poster = { compose, apply, resolveFusion };
})(window);
