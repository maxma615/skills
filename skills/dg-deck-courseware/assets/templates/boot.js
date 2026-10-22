(function(){var q=new URLSearchParams(location.search),r=document.documentElement;
if(q.get('static')==='1'||q.get('print')||matchMedia('(prefers-reduced-motion: reduce)').matches)r.classList.add('static');
if(q.get('export')==='1')r.classList.add('export');})();