---
layout: page
title: 简历
permalink: /resume/
body_class: resume
hide_title: true
show_email: true
---
{% assign r = site.data.resume %}
{% for s in r.sections %}
<h2>{{ s.title }}{% if s.note %} <span class="note">{{ s.note }}</span>{% endif %}</h2>
{% for it in s.items %}
<div class="entry"><span>{{ it.title }}{% if it.sub %} · {{ it.sub }}{% endif %}{% if it.page %} · <a href="{{ it.page | relative_url }}">项目页</a>{% endif %}{% if it.note %} <span class="note">{{ it.note }}</span>{% endif %}</span><span class="when">{{ it.date }}</span></div>
{% if it.points %}<ul>
{% for p in it.points %}<li>{% if p.label %}<strong>{{ p.label }}</strong>：{% endif %}{{ p.text }}{% if p.note %} <span class="note">{{ p.note }}</span>{% endif %}</li>
{% endfor %}</ul>{% endif %}
{% endfor %}
{% endfor %}
{% if r.footer_note %}<p class="note">{{ r.footer_note }}</p>{% endif %}
