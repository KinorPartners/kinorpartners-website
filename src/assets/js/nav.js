// Mobile nav toggle
(function(){
  var btn = document.querySelector('.nav__toggle');
  var links = document.querySelector('.nav__links');
  if(!btn || !links) return;
  function setOpen(open){
    links.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
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
