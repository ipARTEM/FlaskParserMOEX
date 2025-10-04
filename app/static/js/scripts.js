// сюда можно вынести клиентскую логику (AJAX обновление, спиннеры и т.п.)


// app/static/js/scripts.js

function clamp(n, min, max) { return Math.min(max, Math.max(min, n)); }

function gradientForChange(pct) {
  // Абсолютную шкалу можно подправить: 5, 8, 10 (%)
  const MAX = 8;
  const c = clamp(Number(pct || 0), -MAX, MAX);
  const intensity = Math.abs(c) / MAX;   // 0..1 (чем ближе к MAX, тем темнее)
  const hue = c >= 0 ? 140 : 0;          // 140° зелёный, 0° красный
  const sat = 70;                        // насыщенность
  const lBase = 60;                      // светлота у нуля
  const lMin  = 16;                      // светлота при экстремуме

  // Чем сильнее движение — тем ниже светлота (темнее)
  const l1 = lBase - (lBase - lMin) * intensity;   // верх градиента
  const l2 = Math.max(l1 - 8, 8);                  // низ градиента чуть темнее

  const col1 = `hsl(${hue} ${sat}% ${l1}%)`;
  const col2 = `hsl(${hue} ${sat}% ${l2}%)`;
  return `linear-gradient(180deg, ${col1} 0%, ${col2} 100%)`;
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tile').forEach(el => {
    const ch = parseFloat(el.dataset.change);
    if (!Number.isFinite(ch)) return;  // пропускаем "—"
    el.style.background = gradientForChange(ch);

    // Контраст текста: при очень светлом фоне делаем текст тёмным (редкий случай около 0%)
    // Но в нашей шкале фон почти всегда тёмный -> оставляем белый.
    // Если захочешь адаптивно — можно посчитать l1 и менять color при l1>50.
  });
});
