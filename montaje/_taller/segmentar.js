// Corta la voz en escenas según sus pausas (copia de la lógica de Apps Script).
function segmentarVoz(rms, frameS, palabras) {
  var n = palabras.length, max = Math.max.apply(null, rms.concat([1e-9])), thr = max * 0.06, minRun = Math.round(0.3 / frameS);
  var first = rms.findIndex(function (v) { return v > thr; }), last = rms.length - 1;
  while (last > 0 && rms[last] <= thr) last--;
  var a = Math.max(0, first) * frameS, z = (last + 1) * frameS, cands = [], run = 0;
  for (var i = Math.max(0, first); i <= last; i++) {
    if (rms[i] <= thr) run++;
    else { if (run >= minRun) cands.push({ t: (i - run / 2) * frameS, w: run * frameS }); run = 0; }
  }
  var tot = palabras.reduce(function (s, x) { return s + x; }, 0), acc = 0, esperado = [];
  for (var j = 0; j < n - 1; j++) { acc += palabras[j]; esperado.push(a + (acc / tot) * (z - a)); }
  // asignación monótona: cada corte esperado toma una pausa, minimizando la distancia (las pausas largas pesan más)
  var m = cands.length, INF = 1e9, dp = [], prev = [];
  for (j = 0; j < n - 1; j++) { dp.push([]); prev.push([]);
    for (i = 0; i < m; i++) {
      var costo = Math.abs(cands[i].t - esperado[j]) - 0.5 * Math.min(cands[i].w, 1), mejor = INF, pi = -1;
      if (j === 0) mejor = 0; else for (var k = 0; k < i; k++) if (dp[j - 1][k] < mejor) { mejor = dp[j - 1][k]; pi = k; }
      dp[j][i] = mejor + costo; prev[j][i] = pi;
    } }
  var cortes = [];
  if (m >= n - 1 && n > 1) {
    var bi = -1, bv = INF; for (i = 0; i < m; i++) if (dp[n - 2][i] < bv) { bv = dp[n - 2][i]; bi = i; }
    for (j = n - 2; j >= 0; j--) { cortes.unshift(cands[bi].t); bi = prev[j][bi]; }
  } else cortes = esperado;                                  // sin pausas suficientes: reparto por palabras
  var b = [a].concat(cortes).concat([z]), out = [];
  for (j = 0; j < n; j++) out.push([Math.round(b[j] * 100) / 100, Math.round(b[j + 1] * 100) / 100]);
  return out;
}

