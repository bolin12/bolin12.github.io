---
layout: page
title: 项目
permalink: /projects/
---
<div class="cards">
  {% for p in site.data.projects %}
  <a class="card" href="{{ p.url }}">
    <h3>{{ p.name }}</h3>
    <p>{{ p.desc }}</p>
    <span class="chips">{% for t in p.tags %}<span class="tag">{{ t }}</span>{% endfor %}</span>
  </a>
  {% endfor %}
</div>
