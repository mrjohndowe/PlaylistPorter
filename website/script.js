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
