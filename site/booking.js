/* codi studio: open Calendly links in a pop-up on the site, and tell
   Google Analytics when someone books a call (event: book_call).
   Google Ads imports book_call from GA4 as the conversion.
   If the Calendly script can't load, the link opens Calendly as normal. */
(function () {
  var loading = null;
  function loadCalendly() {
    if (window.Calendly) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var css = document.createElement('link');
      css.rel = 'stylesheet';
      css.href = 'https://assets.calendly.com/assets/external/widget.css';
      document.head.appendChild(css);
      var s = document.createElement('script');
      s.src = 'https://assets.calendly.com/assets/external/widget.js';
      s.async = true;
      s.onload = function () { window.Calendly ? resolve() : reject(); };
      s.onerror = reject;
      document.head.appendChild(s);
    });
    return loading;
  }

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[href*="calendly.com/"]');
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    var url = a.href;
    loadCalendly().then(function () {
      window.Calendly.initPopupWidget({ url: url });
    }).catch(function () { window.location.href = url; });
  });

  window.addEventListener('message', function (e) {
    if (!/(^|\.)calendly\.com$/.test(new URL(e.origin).hostname)) return;
    if (!e.data || e.data.event !== 'calendly.event_scheduled') return;
    if (typeof window.gtag === 'function') {
      window.gtag('event', 'book_call', { method: 'calendly', page_path: location.pathname });
    }
  });
})();
