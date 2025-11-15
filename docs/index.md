---
layout: default
title: "Welcome"
---

Welcome to my build logs, notes, and experiments.

You can read my latest posts below

<ul>
  {% for post in site.posts %}
  <li>
    <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    <small>— {{ post.date | date: "%Y-%m-%d" }}</small>
  </li>
  {% endfor %}
</ul>

## Other Resources

<ul>
  <li>
    <a href="{{ './cool_tools.md' | relative_url }}">Cool Tools</a>
  </li>
</ul>
