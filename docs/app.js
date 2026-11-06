'use strict';
const samples = { fa: { before: 'sghl', after: 'سلام', direction: 'rtl' }, en: { before: 'اثممخ', after: 'hello', direction: 'ltr' } };
let selected = 'fa';
let corrected = false;
const text = document.querySelector('#demo-text');
const status = document.querySelector('#demo-status');
const label = document.querySelector('#convert-label');
function render() {
  const sample = samples[selected];
  text.firstElementChild.textContent = corrected ? sample.after : sample.before;
  text.dir = corrected ? sample.direction : (selected === 'fa' ? 'ltr' : 'rtl');
  text.classList.toggle('fixed', corrected);
  status.textContent = corrected ? 'همان متن، با چیدمان درست.' : 'زبان صفحه‌کلید اشتباه بود.';
  label.textContent = corrected ? 'دوباره امتحان کن' : 'اصلاح نمونه';
}
document.querySelectorAll('[data-sample]').forEach(button => {
  button.addEventListener('click', () => {
    selected = button.dataset.sample;
    corrected = false;
    document.querySelectorAll('[data-sample]').forEach(tab => {
      const active = tab === button;
      tab.classList.toggle('selected', active);
      tab.setAttribute('aria-pressed', String(active));
    });
    render();
  });
});
document.querySelector('#convert').addEventListener('click', () => { corrected = !corrected; render(); });
