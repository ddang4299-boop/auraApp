/* AURA – khung quét tranh trực tiếp cho bản web (giống quét mã QR ở app ngân hàng).
 *
 * Cách hoạt động
 * - Bấm nút Scan (hay "Quét bức khác"), Flet mở hộp chọn ảnh bằng một <input type="file" accept="image/*">
 *   (thư viện file_picker, chạy NGAY trong cú chạm nhờ ft.PickFiles). Tệp này "đón" lệnh mở đó và hiện khung
 *   quét: camera sau chạy trực tiếp, khung ngắm ở giữa, nút chụp, nút Thư viện ảnh ở góc.
 * - Chụp (hoặc chọn ảnh trong Thư viện) xong, ảnh được thu nhỏ ngay trên máy (cạnh dài 1280px, vài trăm KB
 *   thay vì 3-12 MB) rồi trao lại cho chính <input> đó như thể người dùng vừa chọn tệp. Phần Python
 *   (FilePicker.on_result -> gửi ảnh lên -> nhận diện) không phải đổi gì.
 * - Khung quét giữ ảnh vừa chụp cho tới khi thấy ảnh bắt đầu được gửi lên máy chủ (lúc đó màn chờ của app
 *   đã hiện bên dưới), rồi mới mờ đi: người dùng không thấy màn cũ chớp lên giữa chừng.
 * - Bấm X / Esc / nút Back của điện thoại: đóng khung, báo "người dùng huỷ" cho Flet, ở nguyên màn đang xem.
 * - Trình duyệt không cho dùng camera (trang không chạy HTTPS, trình duyệt quá cũ...) thì để hộp chọn ảnh
 *   gốc mở như bình thường. Bị từ chối quyền camera / máy không có camera: khung báo rõ và mời chọn ảnh có sẵn.
 * Camera chỉ bật khi khung đang mở và tắt ngay khi chụp xong hoặc đóng khung.
 */
(function () {
  'use strict';
  if (window.__auraScan) return;
  window.__auraScan = true;

  var SHOT_MAX = 1280;      // cạnh dài ảnh chụp từ camera (máy chủ chỉ dùng tới 800px)
  var PICK_MAX = 1600;      // cạnh dài ảnh chọn từ Thư viện
  var SEND_WAIT = 6000;     // chờ ngần này mà không thấy ảnh được gửi lên máy chủ thì vẫn đóng khung
  var TIPS = [
    'Đưa bức tranh vào trong khung',
    'Chụp một phần thật rõ cũng được',
    'Giữ máy thật chắc khi bấm chụp',
    'Tắt đèn flash để mặt kính không bị lóa'
  ];

  var ICON_X = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';
  var ICON_IMG = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21"/></svg>';
  var ICON_CAM_OFF = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 2l20 20"/><path d="M7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16"/><path d="M9.5 4h5L17 7h3a2 2 0 0 1 2 2v7.3"/><path d="M14.1 14.1a3 3 0 1 1-4.2-4.2"/></svg>';

  var CSS = [
    '#aura-cam{position:fixed;inset:0;z-index:2147483000;display:none;opacity:0;transition:opacity .22s ease;',
    ' background:#0E0B0A;color:#fff;overflow:hidden;touch-action:none;-webkit-user-select:none;user-select:none;',
    ' -webkit-tap-highlight-color:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;',
    ' --fw:min(74vw,340px,42vh)}',
    '#aura-cam.on{display:block}#aura-cam.in{opacity:1}',
    '#aura-cam video,#aura-cam canvas{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}',
    '#aura-cam .mirror{transform:scaleX(-1)}',
    '#aura-cam canvas{display:none}#aura-cam.frozen canvas{display:block}',
    /* khung ngắm: vùng ngoài khung tối đi, 4 góc vàng thở nhẹ, một vệt sáng quét lên xuống */
    '#aura-cam .frame{position:absolute;left:50%;top:44%;width:var(--fw);height:calc(var(--fw)*1.25);',
    ' transform:translate(-50%,-50%);border-radius:22px;box-shadow:0 0 0 200vmax rgba(14,10,9,.52);transition:opacity .25s}',
    '#aura-cam .c{position:absolute;width:40px;height:40px;border:0 solid #E8A84B;animation:aura-breathe 2.6s ease-in-out infinite}',
    '#aura-cam .tl{left:-3px;top:-3px;border-left-width:4px;border-top-width:4px;border-top-left-radius:24px;--dx:-3px;--dy:-3px}',
    '#aura-cam .tr{right:-3px;top:-3px;border-right-width:4px;border-top-width:4px;border-top-right-radius:24px;--dx:3px;--dy:-3px}',
    '#aura-cam .bl{left:-3px;bottom:-3px;border-left-width:4px;border-bottom-width:4px;border-bottom-left-radius:24px;--dx:-3px;--dy:3px}',
    '#aura-cam .br{right:-3px;bottom:-3px;border-right-width:4px;border-bottom-width:4px;border-bottom-right-radius:24px;--dx:3px;--dy:3px}',
    '@keyframes aura-breathe{0%,100%{transform:translate(0,0)}50%{transform:translate(var(--dx),var(--dy))}}',
    '#aura-cam .sweep{position:absolute;inset:0;animation:aura-sweep 2.8s ease-in-out infinite alternate;pointer-events:none}',
    '#aura-cam .sweep b{position:absolute;left:9%;right:9%;top:50%;height:2px;border-radius:2px;',
    ' background:linear-gradient(90deg,rgba(232,168,75,0),#F3C77A 50%,rgba(232,168,75,0));box-shadow:0 0 14px 3px rgba(232,168,75,.45)}',
    '@keyframes aura-sweep{from{transform:translateY(-42%)}to{transform:translateY(42%)}}',
    '#aura-cam:not(.live) .sweep{display:none}',
    /* thanh trên */
    '#aura-cam .top{position:absolute;left:0;right:0;top:0;padding:14px 16px 0;display:flex;align-items:center;justify-content:space-between}',
    '#aura-cam .rbtn{width:44px;height:44px;border-radius:22px;border:0;padding:0;margin:0;background:rgba(20,15,13,.5);color:#fff;',
    ' display:flex;align-items:center;justify-content:center;cursor:pointer;-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}',
    '#aura-cam .rbtn:focus-visible,#aura-cam .shutter:focus-visible,#aura-cam label:focus-visible{outline:3px solid #F3C77A;outline-offset:3px}',
    '#aura-cam .title{font-size:16px;font-weight:600;letter-spacing:.01em;text-shadow:0 1px 8px rgba(0,0,0,.5)}',
    '#aura-cam .rsp{width:44px}',
    /* lời nhắc dưới khung (tự đổi) */
    '#aura-cam .hint{position:absolute;left:24px;right:24px;top:calc(44% + var(--fw)*.625 + 20px);text-align:center;',
    ' font-size:15px;line-height:1.4;font-weight:500;text-shadow:0 1px 10px rgba(0,0,0,.6);transition:opacity .28s}',
    /* hàng nút dưới: Thư viện · Chụp · (trống) */
    '#aura-cam .bottom{position:absolute;left:0;right:0;bottom:0;padding:0 28px 30px;display:grid;',
    ' grid-template-columns:1fr auto 1fr;align-items:center;transition:opacity .25s}',
    '@media (min-width:700px){#aura-cam .bottom{left:50%;right:auto;width:520px;transform:translateX(-50%);box-sizing:border-box}}',
    '#aura-cam .gal{justify-self:start;display:flex;flex-direction:column;align-items:center;gap:6px;cursor:pointer;',
    ' color:#fff;font-size:12.5px;font-weight:500;text-shadow:0 1px 6px rgba(0,0,0,.5)}',
    '#aura-cam .gal .ic{width:54px;height:54px;border-radius:17px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.3);',
    ' display:flex;align-items:center;justify-content:center;-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}',
    '#aura-cam .gal:active .ic{background:rgba(255,255,255,.28)}',
    '#aura-cam .shutter{width:80px;height:80px;border-radius:50%;border:4px solid #fff;background:rgba(255,255,255,.08);padding:0;margin:0;',
    ' display:flex;align-items:center;justify-content:center;cursor:pointer;transition:opacity .2s}',
    '#aura-cam .shutter i{display:block;width:62px;height:62px;border-radius:50%;background:#fff;transition:transform .12s}',
    '#aura-cam .shutter:active i{transform:scale(.88)}',
    '#aura-cam:not(.live) .shutter{opacity:.35;pointer-events:none}',
    /* chip trạng thái (đang mở camera / đang gửi ảnh) */
    '#aura-cam .status{position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);display:none;align-items:center;gap:10px;',
    ' white-space:nowrap;padding:12px 18px;border-radius:999px;background:rgba(20,15,13,.66);font-size:14px;font-weight:600;',
    ' -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}',
    '#aura-cam.starting .status,#aura-cam.sending .status{display:flex}',
    '#aura-cam .spin{width:18px;height:18px;border-radius:50%;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;animation:aura-spin .8s linear infinite}',
    '@keyframes aura-spin{to{transform:rotate(360deg)}}',
    '#aura-cam.sending .frame,#aura-cam.sending .hint,#aura-cam.sending .bottom{opacity:0;pointer-events:none}',
    '#aura-cam.starting .hint{opacity:0}',
    /* không mở được camera */
    '#aura-cam .err{position:absolute;left:50%;top:46%;transform:translate(-50%,-50%);width:min(84vw,360px);display:none;box-sizing:border-box;',
    ' background:#FFFBF2;color:#2F2A26;border-radius:22px;padding:24px 20px 16px;text-align:center;box-shadow:0 18px 50px rgba(0,0,0,.35)}',
    '#aura-cam.error .err{display:block}',
    '#aura-cam.error .frame,#aura-cam.error .hint,#aura-cam.error .bottom{display:none}',
    '#aura-cam .eic{width:52px;height:52px;margin:0 auto;border-radius:26px;background:#EFE2DF;color:#772F3D;display:flex;align-items:center;justify-content:center}',
    '#aura-cam .err h3{margin:12px 0 6px;font:500 20px/1.3 Lora,Georgia,"Times New Roman",serif;color:#2F2A26}',
    '#aura-cam .err p{margin:0 0 18px;font-size:14.5px;line-height:1.45;color:#6B6056}',
    '#aura-cam .pick{display:flex;align-items:center;justify-content:center;gap:10px;height:52px;border-radius:26px;background:#772F3D;',
    ' color:#fff;font-weight:600;font-size:15.5px;cursor:pointer}',
    '#aura-cam .close2{margin-top:8px;padding:10px 16px;border:0;background:none;color:#6B6056;font-size:14px;text-decoration:underline;cursor:pointer}',
    '#aura-cam .vh{position:absolute;left:-9999px;width:1px;height:1px;opacity:0;pointer-events:none}',
    '#aura-cam .flash{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none}',
    '#aura-cam .flash.go{animation:aura-flash .34s ease-out}',
    '@keyframes aura-flash{0%{opacity:.8}100%{opacity:0}}',
    '@media (prefers-reduced-motion:reduce){#aura-cam .c,#aura-cam .sweep{animation:none}#aura-cam .sweep b{top:50%}}'
  ].join('\n');

  var HTML = [
    '<video playsinline muted autoplay></video>',
    '<canvas></canvas>',
    '<div class="frame" aria-hidden="true"><i class="c tl"></i><i class="c tr"></i><i class="c bl"></i><i class="c br"></i>',
    '<div class="sweep"><b></b></div></div>',
    '<div class="top"><button type="button" class="rbtn x" aria-label="Đóng khung quét">' + ICON_X + '</button>',
    '<div class="title">Quét tranh</div><div class="rsp"></div></div>',
    '<div class="hint" aria-live="polite"></div>',
    '<div class="status" role="status"><span class="spin"></span><span class="stext">Đang mở camera…</span></div>',
    '<div class="err" role="alert"><div class="eic">' + ICON_CAM_OFF + '</div><h3></h3><p></p>',
    '<label class="pick" for="aura-cam-file">' + ICON_IMG + '<span>Chọn ảnh có sẵn</span></label>',
    '<button type="button" class="close2">Đóng</button></div>',
    '<div class="bottom"><label class="gal" for="aura-cam-file" aria-label="Chọn ảnh trong Thư viện"><span class="ic">' + ICON_IMG,
    '</span>Thư viện</label><button type="button" class="shutter" aria-label="Chụp ảnh"><i></i></button><span></span></div>',
    '<input id="aura-cam-file" class="vh" type="file" accept="image/*" tabindex="-1" aria-hidden="true">',
    '<div class="flash"></div>'
  ].join('');

  var nativeClick = HTMLInputElement.prototype.click;
  var root = null, video, still, hintEl, statusText, errTitle, errText, fileInput, flashEl;
  var target = null;        // <input> của file_picker đang chờ ảnh
  var stream = null, state = 'idle', seq = 0, sendTimer = 0, tipTimer = 0, tipIdx = 0;

  function cameraOK() {
    if (window.AURA_NO_CAMERA || !window.isSecureContext) return false;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return false;
    try { new DataTransfer(); } catch (e) { return false; }      // cần để trao ảnh lại cho <input>
    return true;
  }

  // Đón lệnh mở hộp chọn ảnh của Scan (chỉ <input> ảnh đơn; các <input> khác chạy như cũ)
  HTMLInputElement.prototype.click = function () {
    if (this.type === 'file' && this.accept === 'image/*' && !this.multiple && this !== fileInput && cameraOK()) {
      try { open(this); return; } catch (e) { console.warn('[aura-scan] dùng hộp chọn ảnh gốc:', e); hide(); }
    }
    return nativeClick.apply(this, arguments);
  };

  function build() {
    if (root) return;
    var css = document.createElement('style');
    css.textContent = CSS;
    document.head.appendChild(css);
    root = document.createElement('div');
    root.id = 'aura-cam';
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.setAttribute('aria-label', 'Quét tranh');
    root.innerHTML = HTML;
    document.body.appendChild(root);
    video = root.querySelector('video');
    still = root.querySelector('canvas');
    hintEl = root.querySelector('.hint');
    statusText = root.querySelector('.stext');
    errTitle = root.querySelector('.err h3');
    errText = root.querySelector('.err p');
    fileInput = root.querySelector('#aura-cam-file');
    flashEl = root.querySelector('.flash');
    root.querySelector('.x').addEventListener('click', cancel);
    root.querySelector('.close2').addEventListener('click', cancel);
    root.querySelector('.shutter').addEventListener('click', shoot);
    fileInput.addEventListener('change', picked);
    video.addEventListener('playing', live);
    video.addEventListener('loadeddata', live);
  }

  function setState(s) {
    state = s;
    ['starting', 'live', 'sending', 'error'].forEach(function (k) { root.classList.toggle(k, k === s); });
  }

  function open(input) {
    build();
    if (target && target !== input) fireCancel(target);      // lần mở trước chưa xong (hiếm)
    target = input;
    clearTimeout(sendTimer);
    root.className = 'on';
    void root.offsetWidth;                                   // để hiệu ứng hiện dần chạy
    root.classList.add('in');
    var a = document.activeElement;
    if (a && a !== document.body && a.blur) a.blur();        // cất bàn phím nếu đang mở
    pushEntry();
    startTips();
    startCamera();
  }

  // ---- nút Back của điện thoại: chỉ đóng khung quét ----
  // Khung đang mở thì thêm một mục lịch sử (cùng địa chỉ, cùng trạng thái của Flutter): bấm Back / vuốt lùi
  // chỉ gỡ mục đó và đóng khung, không lùi trang của app (hay rời app nếu đang ở trang đầu tiên).
  var pushed = false, popWait = null;

  function pushEntry() {
    if (pushed) return;
    try {
      var s = history.state, mine = {};
      if (s && typeof s === 'object') for (var k in s) mine[k] = s[k];
      mine.auraScan = true;
      history.pushState(mine, '', location.href);
      pushed = true;
    } catch (e) {}
  }

  // Đóng khung bằng X / chụp xong: tự gỡ mục lịch sử của khung, gỡ XONG mới chạy then() (vd trao ảnh cho
  // Flet), để lệnh mở màn /scan của app đến sau, không bị lệnh lùi này cuốn mất.
  function popEntry(then) {
    if (!pushed) { if (then) then(); return; }
    pushed = false;
    var done = false;
    popWait = function () {
      if (done) return;
      done = true;
      popWait = null;
      if (then) then();
    };
    history.back();
    setTimeout(function () { if (popWait) popWait(); }, 400);
  }

  window.addEventListener('popstate', function () {
    if (popWait) { popWait(); return; }          // chính khung vừa gỡ mục của mình
    if (pushed) { pushed = false; cancel(); }    // người dùng bấm Back khi khung đang mở
  });

  function startCamera() {
    stopCamera();
    setState('starting');
    statusText.textContent = 'Đang mở camera…';
    var my = ++seq;
    var md = navigator.mediaDevices;
    md.getUserMedia({ audio: false, video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } } })
      .catch(function (err) {
        if (err && /Overconstrained|ConstraintNotSatisfied/.test(err.name)) return md.getUserMedia({ audio: false, video: true });
        throw err;
      })
      .then(function (s) {
        if (my !== seq || !target) { stopTracks(s); return; }
        stream = s;
        var tr = s.getVideoTracks()[0];
        var face = tr && tr.getSettings ? tr.getSettings().facingMode : '';
        video.classList.toggle('mirror', face === 'user');   // camera trước: hiện như soi gương
        still.classList.toggle('mirror', face === 'user');
        if (tr) tr.addEventListener('ended', function () { if (stream === s && state === 'live') startCamera(); });
        video.srcObject = s;
        var p = video.play();
        if (p && p.catch) p.catch(function () {});
      })
      .catch(function (err) {
        if (my !== seq || !target) return;
        showError(err && err.name);
      });
  }

  function live() {
    if (state === 'starting' && stream && video.videoWidth) setState('live');
  }

  function stopTracks(s) {
    try { s.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
  }

  function stopCamera() {
    seq++;
    if (stream) { stopTracks(stream); stream = null; }
    if (video) {
      try { video.pause(); } catch (e) {}
      video.srcObject = null;
    }
  }

  function showError(name) {
    stopCamera();
    var denied = /NotAllowed|Security|PermissionDenied/.test(name || '');
    var busy = /NotReadable|TrackStart|Abort/.test(name || '');
    errTitle.textContent = denied ? 'AURA chưa được dùng camera' : busy ? 'Camera đang bận' : 'Chưa mở được camera';
    errText.textContent = denied
      ? 'Bạn cho phép trang này dùng camera trong cài đặt của trình duyệt rồi mở lại, hoặc chọn một ảnh bức tranh có sẵn trong máy.'
      : busy
        ? 'Có thể một ứng dụng khác đang dùng camera. Bạn tắt ứng dụng đó rồi mở lại, hoặc chọn ảnh có sẵn.'
        : 'Máy này chưa mở được camera. Bạn có thể chọn một ảnh bức tranh có sẵn trong máy.';
    setState('error');
  }

  function shoot() {
    if (state !== 'live' || !target) return;
    var w = video.videoWidth, h = video.videoHeight;
    if (!w || !h) return;
    var k = Math.min(1, SHOT_MAX / Math.max(w, h));
    still.width = Math.round(w * k);
    still.height = Math.round(h * k);
    try { still.getContext('2d').drawImage(video, 0, 0, still.width, still.height); } catch (e) { return; }
    root.classList.add('frozen');                            // giữ khung hình vừa chụp
    flashEl.classList.remove('go');
    void flashEl.offsetWidth;
    flashEl.classList.add('go');
    sending('Đang gửi ảnh…');
    still.toBlob(function (blob) {
      if (!blob) { root.classList.remove('frozen'); startCamera(); return; }
      deliver(new File([blob], 'aura-scan-' + Date.now() + '.jpg', { type: 'image/jpeg', lastModified: Date.now() }));
    }, 'image/jpeg', 0.88);
  }

  function picked() {
    var f = fileInput.files && fileInput.files[0];
    fileInput.value = '';
    if (!f || !target) return;
    sending('Đang chuẩn bị ảnh…');
    shrink(f).then(function (g) {
      statusText.textContent = 'Đang gửi ảnh…';
      deliver(g);
    });
  }

  function sending(text) {
    stopCamera();
    stopTips();
    setState('sending');
    statusText.textContent = text;
  }

  // Thu nhỏ ảnh chọn từ Thư viện (ảnh điện thoại 3-12 MB) để gửi nhanh; không đọc được thì gửi nguyên ảnh.
  function shrink(file) {
    return new Promise(function (resolve) {
      if (!/^image\/(jpeg|png|webp|bmp|gif)$/.test(file.type) || file.size < 700 * 1024) { resolve(file); return; }
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        try {
          var w = img.naturalWidth, h = img.naturalHeight, k = Math.min(1, PICK_MAX / Math.max(w, h));
          if (!w || !h || k >= 1) { resolve(file); return; }
          var c = document.createElement('canvas');
          c.width = Math.round(w * k);
          c.height = Math.round(h * k);
          c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
          c.toBlob(function (b) {
            resolve(b ? new File([b], 'aura-scan-' + Date.now() + '.jpg', { type: 'image/jpeg', lastModified: Date.now() }) : file);
          }, 'image/jpeg', 0.9);
        } catch (e) {
          resolve(file);
        } finally {
          URL.revokeObjectURL(url);
        }
      };
      img.onerror = function () { URL.revokeObjectURL(url); resolve(file); };
      img.src = url;
    });
  }

  // Trao ảnh cho <input> của file_picker như thể người dùng vừa chọn tệp
  function deliver(file) {
    var input = target;
    target = null;
    if (!input) { hide(); return; }
    try {
      var dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
    } catch (e) {
      console.warn('[aura-scan] không trao được ảnh:', e);
      hide();
      popEntry(function () { fireCancel(input); });
      return;
    }
    clearTimeout(sendTimer);
    sendTimer = setTimeout(hide, SEND_WAIT);
    popEntry(function () { input.dispatchEvent(new Event('change')); });
  }

  function fireCancel(input) {
    try { input.dispatchEvent(new Event('cancel')); } catch (e) {}
  }

  function cancel() {
    if (state === 'idle') return;
    var input = target;
    target = null;
    hide();
    popEntry(function () { if (input) fireCancel(input); });
  }

  function hide() {
    clearTimeout(sendTimer);
    stopTips();
    stopCamera();
    if (!root) return;
    state = 'idle';
    root.classList.remove('in');
    setTimeout(function () { if (state === 'idle') root.className = ''; }, 240);
  }

  function startTips() {
    stopTips();
    tipIdx = 0;
    hintEl.textContent = TIPS[0];
    hintEl.style.opacity = '';
    tipTimer = setInterval(function () {
      tipIdx = (tipIdx + 1) % TIPS.length;
      hintEl.style.opacity = '0';
      setTimeout(function () { hintEl.textContent = TIPS[tipIdx]; hintEl.style.opacity = ''; }, 280);
    }, 3600);
  }

  function stopTips() {
    clearInterval(tipTimer);
    tipTimer = 0;
  }

  // Ảnh bắt đầu được gửi lên máy chủ (Flet gọi /upload?f=...): màn chờ của app đã hiện, đóng khung quét.
  function watch(url) {
    if (state === 'sending' && !target && /(^|\/)upload\?/.test(String(url || ''))) {
      clearTimeout(sendTimer);
      sendTimer = setTimeout(hide, 180);
    }
  }
  var xhrOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    try { watch(url); } catch (e) {}
    return xhrOpen.apply(this, arguments);
  };
  if (window.fetch) {
    var nativeFetch = window.fetch;
    window.fetch = function (input) {
      try { watch(typeof input === 'string' ? input : input && input.url); } catch (e) {}
      return nativeFetch.apply(this, arguments);
    };
  }

  window.addEventListener('keydown', function (e) {
    if (state === 'idle') return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cancel(); }
    else if ((e.key === ' ' || e.key === 'Enter') && state === 'live' && !(e.target && e.target.closest && e.target.closest('button,label'))) {
      e.preventDefault(); e.stopPropagation(); shoot();
    }
  }, true);
  // Chuyển sang ứng dụng khác: tắt camera; quay lại thì bật lại
  document.addEventListener('visibilitychange', function () {
    if (state !== 'starting' && state !== 'live') return;
    if (document.hidden) stopCamera(); else startCamera();
  });
})();
