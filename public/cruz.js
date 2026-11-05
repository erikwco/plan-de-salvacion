/*
 * Cruz flotante que abre "El Plan de Salvación".
 *
 *   <script src="https://salvacion.idear.pro/cruz.js" defer></script>
 *
 * Opciones (atributos data-* del mismo <script>, todas opcionales):
 *   data-lado="izquierda" | "derecha"    esquina inferior donde flota (izquierda)
 *   data-abajo="18"                       separación del borde inferior, en px
 *   data-costado="20"                     separación del borde lateral, en px
 *   data-fondo="#0b0b0b"                  color del botón
 *   data-color="#ffffff"                  color de la cruz
 *   data-borde="#555555"                  color del borde del botón
 *   data-radio="3"                        redondeo del botón, en px
 *   data-tema="noche" | "amanecer" | "olivo"   paleta de la película
 *   data-idioma="es" | "en"               idioma del botón y del diálogo
 *   data-capa="9999"                      z-index del botón
 */
(function () {
  var script = document.currentScript;
  if (!script || window.__planDeSalvacion) return;
  window.__planDeSalvacion = true;

  var opt = script.dataset;
  var origin = new URL(script.src).origin;
  var text = {
    es: { title: 'El Plan de Salvación', close: 'Cerrar', rotate: 'Gira tu teléfono para verlo en grande.' },
    en: { title: 'The Plan of Salvation', close: 'Close', rotate: 'Turn your phone sideways to see it larger.' },
  }[opt.idioma === 'en' ? 'en' : 'es'];
  var params = new URLSearchParams({ autoplay: '1' });
  if (opt.tema) params.set('tema', opt.tema);
  var src = origin + '/?' + params;
  var side = opt.lado === 'derecha' ? 'right' : 'left';
  var px = function (value, fallback) {
    var n = parseFloat(value);
    return (isFinite(n) ? n : fallback) + 'px';
  };

  function mount() {
    var host = document.createElement('div');
    host.setAttribute('data-plan-de-salvacion', '');
    var root = host.attachShadow({ mode: 'open' });
    root.innerHTML =
      '<style>' +
      ':host{all:initial}' +
      '.cruz{position:fixed;' + side + ':' + px(opt.costado, 20) + ';bottom:' + px(opt.abajo, 18) + ';z-index:' + (parseInt(opt.capa, 10) || 9999) + ';' +
      'display:flex;align-items:center;justify-content:center;width:46px;height:46px;padding:0;cursor:pointer;' +
      'border:1px solid ' + (opt.borde || '#555') + ';border-radius:' + px(opt.radio, 3) + ';background:' + (opt.fondo || '#0b0b0b') + ';color:' + (opt.color || '#fff') + ';' +
      'box-sizing:border-box;-webkit-tap-highlight-color:transparent;animation:flotar 3.2s ease-in-out infinite}' +
      '.cruz:hover{filter:brightness(1.25)}' +
      '.cruz:focus-visible{outline:3px solid #c84b00;outline-offset:4px}' +
      '.cruz svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round}' +
      '@keyframes flotar{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}' +
      'dialog{padding:0;border:0;width:min(1180px,calc(100% - 48px));max-width:none;max-height:calc(100dvh - 48px);overflow:hidden;' +
      'background:#0b0b0b;color:#fff;box-shadow:0 24px 80px #0004;font:16px/1.3 system-ui,-apple-system,"Segoe UI",sans-serif}' +
      'dialog::backdrop{background:#0009}' +
      '.barra{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:6px 6px 6px 20px}' +
      'h2{margin:0;font-size:16px;font-weight:700}' +
      '.giro{display:none;margin:3px 0 0;color:#bdbdbd;font-size:13px}' +
      '.cerrar{display:flex;align-items:center;justify-content:center;width:44px;height:44px;padding:0;border:0;background:transparent;color:#fff;cursor:pointer}' +
      '.cerrar:hover{background:#333}' +
      '.cerrar:focus-visible{outline:3px solid #c84b00;outline-offset:-3px}' +
      '.cerrar svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round}' +
      '.pantalla{aspect-ratio:16/9;max-height:calc(100dvh - 104px);background:#f4ecd8}' +
      'iframe{display:block;width:100%;height:100%;border:0}' +
      '@media (max-width:800px),(max-height:500px){' +
      'dialog{width:100%;height:100dvh;max-height:none;margin:0}' +
      'dialog[open]{display:flex;flex-direction:column}' +
      '.pantalla{flex:1;aspect-ratio:auto;max-height:none}' +
      '.cruz{' + side + ':' + px(opt.costado, 14) + ';bottom:' + px(opt.abajo, 14) + '}}' +
      '@media (max-width:800px) and (orientation:portrait){.giro{display:block}}' +
      '@media (prefers-reduced-motion:reduce){.cruz{animation:none}}' +
      '</style>' +
      '<button class="cruz" type="button" aria-haspopup="dialog"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5v19M6 8h12"/></svg></button>' +
      '<dialog aria-labelledby="titulo">' +
      '<div class="barra"><div><h2 id="titulo"></h2><p class="giro"></p></div>' +
      '<button class="cerrar" type="button"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg></button></div>' +
      '<div class="pantalla"></div>' +
      '</dialog>';

    var button = root.querySelector('.cruz');
    var dialog = root.querySelector('dialog');
    var screen = root.querySelector('.pantalla');
    var overflow = '';
    button.setAttribute('aria-label', text.title);
    button.title = text.title;
    root.querySelector('h2').textContent = text.title;
    root.querySelector('.giro').textContent = text.rotate;
    root.querySelector('.cerrar').setAttribute('aria-label', text.close);

    button.addEventListener('click', function () {
      var frame = document.createElement('iframe');
      frame.src = src;
      frame.title = text.title;
      frame.allow = 'autoplay; fullscreen';
      screen.replaceChildren(frame);
      overflow = document.documentElement.style.overflow;
      document.documentElement.style.overflow = 'hidden';
      dialog.showModal();
    });
    root.querySelector('.cerrar').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (event) { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', function () {
      screen.replaceChildren();
      document.documentElement.style.overflow = overflow;
      button.focus();
    });
    document.body.appendChild(host);
  }

  if (document.body) mount();
  else document.addEventListener('DOMContentLoaded', mount);
})();
