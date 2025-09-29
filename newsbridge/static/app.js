function renderNews(items){
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    items.forEach(it => {
        const card = document.createElement('div');
        card.className = 'card';
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = it.source + (it.published ? (' • ' + it.published) : '');
        const title = document.createElement('div');
        title.className = 'title';
        const a = document.createElement('a');
        a.href = it.url;
        a.target = '_blank';
        a.textContent = it.title;
        title.appendChild(a);
        const summary = document.createElement('div');
        summary.className = 'summary';
        summary.innerHTML = it.summary || '';
        card.appendChild(meta);
        card.appendChild(title);
        card.appendChild(summary);
        grid.appendChild(card);
    })
}

function applyFilters(){
    const active = document.querySelectorAll('.filter-btn.active');
    const sources = Array.from(active).map(b => b.dataset.source);
    const q = document.getElementById('q').value.toLowerCase();
    let filtered = window.__news || [];
    if(sources.length) filtered = filtered.filter(i => sources.includes(i.source));
    if(q) filtered = filtered.filter(i => (i.title + ' ' + (i.summary||'')).toLowerCase().includes(q));
    renderNews(filtered);
}

async function loadAndRender(){
    const resp = await fetch('/api/news');
    const data = await resp.json();
    window.__news = data;
    renderNews(data);
    const container = document.getElementById('source-filters');
    const sources = [...new Set(data.map(d => d.source))].sort();
    sources.forEach(s => {
        const b = document.createElement('button');
        b.className = 'filter-btn';
        b.textContent = s;
        b.dataset.source = s;
        b.onclick = function(){ this.classList.toggle('active'); applyFilters(); }
        container.appendChild(b);
    })
}

window.addEventListener('DOMContentLoaded', loadAndRender);
