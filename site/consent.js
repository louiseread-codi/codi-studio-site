/* codi studio: Google Analytics 4 with a cookie banner.
   Analytics only loads after the visitor clicks Accept (UK GDPR / PECR).
   The choice is remembered in this browser. */
(function () {
  var GA_ID = 'G-5296ZG77LR';
  if (!/^G-[A-Z0-9]{6,}$/.test(GA_ID) || GA_ID === 'G-XXXXXXXXXX') return;
  var KEY = 'codi-cookie-choice';
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag('consent', 'default', { analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });

  function loadGA() {
    gtag('consent', 'update', { analytics_storage: 'granted' });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', GA_ID);
  }
  function choice() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  if (choice() === 'accepted') { loadGA(); return; }
  if (choice() === 'declined') return;

  function showBanner() {
    var b = document.createElement('div');
    b.setAttribute('role', 'region');
    b.setAttribute('aria-label', 'Cookie choice');
    b.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;max-width:560px;margin:0 auto;background:#1E1034;color:#fff;border:1px solid #8B4BFF;border-radius:14px;padding:18px 20px;font-family:Poppins,system-ui,sans-serif;font-size:14px;line-height:1.5;box-shadow:0 10px 30px rgba(0,0,0,.35)';
    b.innerHTML = '<p style="margin:0 0 12px">We use analytics cookies to see how people find and use this site. Nothing loads unless you accept. <a href="/privacy-policy" style="color:#35FF9A">Privacy policy</a></p>'
      + '<div style="display:flex;gap:10px;flex-wrap:wrap">'
      + '<button type="button" data-c="accepted" style="background:#35FF9A;color:#12032E;border:0;border-radius:999px;padding:9px 20px;font:600 14px Poppins,system-ui,sans-serif;cursor:pointer">Accept</button>'
      + '<button type="button" data-c="declined" style="background:transparent;color:#fff;border:1px solid #CFC4E8;border-radius:999px;padding:9px 20px;font:600 14px Poppins,system-ui,sans-serif;cursor:pointer">Decline</button>'
      + '</div>';
    b.addEventListener('click', function (e) {
      var v = e.target && e.target.getAttribute('data-c');
      if (!v) return;
      save(v);
      if (v === 'accepted') loadGA();
      b.remove();
    });
    document.body.appendChild(b);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', showBanner); else showBanner();
})();
