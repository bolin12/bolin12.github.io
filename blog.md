---
layout: page
title: 博客
permalink: /blog/
---
{% for post in site.posts %}
  {% assign y = post.date | date: "%Y" %}
  {% if y != last_year %}<h3 class="year">{{ y }}</h3>{% assign last_year = y %}{% endif %}
  <ul class="posts"><li><time>{{ post.date | date: "%m-%d" }}</time><a href="{{ post.url | relative_url }}">{{ post.title }}</a></li></ul>
{% endfor %}
