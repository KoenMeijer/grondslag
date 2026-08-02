/*
 * Grondslag embed-widget. Sluit de vraagtool in op een externe site:
 *   <script src="https://grondslag.eu/widget.js"></script>
 * Injecteert een iframe (geïsoleerd, geen CORS nodig) direct na het script en
 * schaalt de hoogte mee op basis van postMessage vanuit /embed.
 * Laad synchroon (geen async/defer) zodat document.currentScript werkt.
 */
(function () {
  var origin = 'https://grondslag.eu'
  var script = document.currentScript
  if (!script || !script.parentNode) return

  var iframe = document.createElement('iframe')
  iframe.src = origin + '/embed'
  iframe.title = 'Vraag het aan Grondslag'
  iframe.setAttribute('loading', 'lazy')
  iframe.style.cssText = 'width:100%;max-width:640px;height:280px;border:0;overflow:hidden;'
  script.parentNode.insertBefore(iframe, script.nextSibling)

  window.addEventListener('message', function (e) {
    if (e.origin !== origin || !e.data || e.data.type !== 'grondslag:height') return
    var h = parseInt(e.data.height, 10)
    if (h > 0) iframe.style.height = h + 'px'
  })
})()
