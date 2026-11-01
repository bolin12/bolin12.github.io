---
layout: page
title: 项目
permalink: /projects/
nav: projects
---
<div class="cards">
  {% for p in site.data.projects %}{% unless p.status == 'planned' %}
  <a class="card" href="{{ p.url | relative_url }}">
    <h3>{{ p.name }}</h3>
    <p>{{ p.desc }}</p>
    <span class="chips">{% for t in p.tags %}<span class="tag">{{ t }}</span>{% endfor %}</span>
  </a>
  {% endunless %}{% endfor %}
</div>

{% assign planned = site.data.projects | where: "status", "planned" %}
{% if planned.size > 0 %}
<h2 class="section">规划中</h2>
<div class="cards">
  {% for p in planned %}
  <a class="card planned" href="{{ p.url | relative_url }}">
    <h3>{{ p.name }} <span class="badge">规划中</span></h3>
    <p>{{ p.desc }}</p>
    <span class="chips">{% for t in p.tags %}<span class="tag">{{ t }}</span>{% endfor %}</span>
  </a>
  {% endfor %}
</div>
{% endif %}
