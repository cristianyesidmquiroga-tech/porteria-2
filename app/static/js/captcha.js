/* Widget del desafío anti-bot (prueba de trabajo), servido desde este mismo
 * servidor. No habla con ningún tercero.
 *
 * SHA-256 va implementado a mano en vez de usar crypto.subtle a propósito:
 * crypto.subtle no existe en contextos inseguros (http:// sobre una IP de la
 * red del centro), y ahí el registro quedaría bloqueado sin explicación. Esta
 * versión funciona igual en http y en https, y además es síncrona, así que
 * resolver decenas de miles de intentos toma milisegundos en vez de encadenar
 * decenas de miles de promesas.
 */
(function () {
  'use strict';

  var K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }

  function bytesDeTexto(texto) {
    if (typeof TextEncoder !== 'undefined') {
      return new TextEncoder().encode(texto);
    }
    var salida = [];
    for (var i = 0; i < texto.length; i++) {
      var c = texto.charCodeAt(i);
      if (c < 0x80) { salida.push(c); }
      else if (c < 0x800) { salida.push(0xc0 | (c >> 6), 0x80 | (c & 63)); }
      else { salida.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63)); }
    }
    return new Uint8Array(salida);
  }

  function sha256Hex(texto) {
    var datos = bytesDeTexto(texto);
    var largo = datos.length;
    var total = ((largo + 9 + 63) >> 6) << 6;
    var buffer = new ArrayBuffer(total);
    var bytes = new Uint8Array(buffer);
    bytes.set(datos);
    bytes[largo] = 0x80;
    var vista = new DataView(buffer);
    var bits = largo * 8;
    vista.setUint32(total - 8, Math.floor(bits / 4294967296));
    vista.setUint32(total - 4, bits >>> 0);

    var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
             0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var w = new Uint32Array(64);

    for (var bloque = 0; bloque < total; bloque += 64) {
      for (var j = 0; j < 16; j++) { w[j] = vista.getUint32(bloque + j * 4); }
      for (j = 16; j < 64; j++) {
        var x = w[j - 15], y = w[j - 2];
        var s0 = rotr(x, 7) ^ rotr(x, 18) ^ (x >>> 3);
        var s1 = rotr(y, 17) ^ rotr(y, 19) ^ (y >>> 10);
        w[j] = (w[j - 16] + s0 + w[j - 7] + s1) >>> 0;
      }
      var a = H[0], b = H[1], c = H[2], d = H[3];
      var e = H[4], f = H[5], g = H[6], h = H[7];
      for (j = 0; j < 64; j++) {
        var S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        var ch = (e & f) ^ (~e & g);
        var t1 = (h + S1 + ch + K[j] + w[j]) >>> 0;
        var S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + maj) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0;
        d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      H[0] = (H[0] + a) >>> 0; H[1] = (H[1] + b) >>> 0;
      H[2] = (H[2] + c) >>> 0; H[3] = (H[3] + d) >>> 0;
      H[4] = (H[4] + e) >>> 0; H[5] = (H[5] + f) >>> 0;
      H[6] = (H[6] + g) >>> 0; H[7] = (H[7] + h) >>> 0;
    }

    var hex = '';
    for (var i = 0; i < 8; i++) {
      hex += ('00000000' + H[i].toString(16)).slice(-8);
    }
    return hex;
  }

  function resolver(desafio) {
    for (var n = 0; n <= desafio.maxNumber; n++) {
      if (sha256Hex(desafio.salt + n) === desafio.challenge) { return n; }
    }
    return null;
  }

  function iniciar(caja) {
    var formulario = caja.closest('form');
    if (!formulario) { return; }

    var campo = formulario.querySelector('input[name="captcha_payload"]');
    var estado = caja.querySelector('[data-captcha-estado]');
    var boton = formulario.querySelector('button[type="submit"]');

    function decir(texto) { if (estado) { estado.textContent = texto; } }
    function liberar() { if (boton) { boton.disabled = false; } }

    // Red de seguridad: pase lo que pase, el botón no puede quedarse
    // bloqueado para siempre. Si el desafío no se resolvió, el servidor lo
    // dirá con un mensaje claro, que es mejor que un formulario muerto.
    var rescate = setTimeout(function () {
      decir('No se pudo completar la verificación. Puedes intentar enviar igualmente.');
      liberar();
    }, 15000);

    if (boton) { boton.disabled = true; }
    decir('Verificando que eres una persona...');

    fetch(caja.dataset.captchaUrl, { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (desafio) {
        if (desafio && desafio.activo === false) {
          clearTimeout(rescate);
          decir('');
          caja.style.display = 'none';
          liberar();
          return;
        }
        // setTimeout para no bloquear el primer pintado de la página.
        setTimeout(function () {
          var numero = resolver(desafio);
          clearTimeout(rescate);
          if (numero === null) {
            decir('No se pudo completar la verificación. Recarga la página.');
            liberar();
            return;
          }
          var solucion = {
            algorithm: desafio.algorithm,
            challenge: desafio.challenge,
            number: numero,
            salt: desafio.salt,
            signature: desafio.signature
          };
          if (campo) { campo.value = btoa(JSON.stringify(solucion)); }
          decir('Verificado. Ya puedes enviar el formulario.');
          caja.classList.add('captcha-listo');
          liberar();
        }, 30);
      })
      .catch(function () {
        clearTimeout(rescate);
        decir('No se pudo cargar la verificación. Puedes intentar enviar igualmente.');
        liberar();
      });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var cajas = document.querySelectorAll('[data-captcha-url]');
    for (var i = 0; i < cajas.length; i++) { iniciar(cajas[i]); }
  });
})();
