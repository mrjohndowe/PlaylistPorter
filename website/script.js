document.querySelectorAll('.reveal').forEach((item) => {
  if (!('IntersectionObserver' in window)) return item.classList.add('visible');
  const observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      item.classList.add('visible');
      observer.disconnect();
    }
  }, { threshold: 0.12 });
  observer.observe(item);
});

const themeToggle = document.querySelector('.theme-toggle');
const syncThemeToggle = () => {
  const dark = document.documentElement.dataset.theme === 'dark';
  themeToggle.setAttribute('aria-pressed', String(dark));
  themeToggle.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
  themeToggle.querySelector('span').textContent = dark ? '☀' : '☾';
  themeToggle.querySelector('b').textContent = dark ? 'Light' : 'Dark';
};
syncThemeToggle();
themeToggle.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('playlist-porter-theme', next);
  syncThemeToggle();
});
