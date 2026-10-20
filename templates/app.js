// The header shows the group's name as it was at the point being read.
// build.py drops a .mark[data-group=N] wherever the group is renamed.
(function () {
  var names = JSON.parse(document.getElementById('groups').textContent);
  var marks = [].slice.call(document.querySelectorAll('[data-group]'));
  var title = document.getElementById('gname');
  var current = 0;
  function check() {
    var n = 0, y = window.innerHeight / 2;
    for (var i = 0; i < marks.length; i++) {
      if (marks[i].getBoundingClientRect().top > y) break;
      n = +marks[i].getAttribute('data-group');
    }
    if (n !== current) { current = n; title.innerHTML = names[n]; }
  }
  check();
  window.addEventListener('scroll', check, { passive: true });
  window.addEventListener('resize', check);
})();
