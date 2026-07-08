// Mobile nav toggle
(function(){
  var btn = document.querySelector('.nav__toggle');
  var links = document.querySelector('.nav__links');
  if(btn && links){
    btn.addEventListener('click', function(){
      links.classList.toggle('open');
      btn.setAttribute('aria-expanded', links.classList.contains('open'));
    });
  }
})();
