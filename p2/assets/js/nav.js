// Mobile nav toggle
(function(){
  var btn = document.querySelector('.nav__toggle');
  var links = document.querySelector('.nav__links');
  if(!btn || !links) return;
  function setOpen(open){
    links.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    // the menu fills the screen, so the page behind it should not scroll
    document.documentElement.classList.toggle('nav-open', open);
  }
  // close it if the window grows past the phone layout while it is open
  var wide = window.matchMedia('(min-width: 861px)');
  (wide.addEventListener ? wide.addEventListener.bind(wide, 'change') : wide.addListener.bind(wide))(function(e){
    if(e.matches) setOpen(false);
  });
  btn.addEventListener('click', function(){
    setOpen(!links.classList.contains('open'));
  });
  // Close the menu after a link is chosen, on Escape, and on a tap outside it.
  links.addEventListener('click', function(e){
    if(e.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && links.classList.contains('open')){ setOpen(false); btn.focus(); }
  });
  document.addEventListener('click', function(e){
    if(links.classList.contains('open') && !links.contains(e.target) && !btn.contains(e.target)) setOpen(false);
  });
})();
