{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}

{% block methods %}
{% if methods %}

..
   HACK -- the point here is that we don't want this to appear in the output, but the autosummary should still generate the pages.
   .. autosummary::
      :toctree:
      {% for item in methods %}
      {%- if item not in inherited_members %}
      {%- if not item.startswith('_') or item in ['__call__'] %}
      {{ name }}.{{ item }}
      {%- endif -%}
      {%- endif -%}
      {%- endfor %}

{% endif %}
{% endblock %}

{% block attributes %}
{% if attributes %}

..
   HACK -- the point here is that we don't want this to appear in the output, but the autosummary should still generate the pages.
   .. autosummary::
      :toctree:
      {% for item in attributes %}
      {%- if item not in inherited_attributes %}
      {%- if not item.startswith('_') %}
      {{ name }}.{{ item }}
      {%- endif -%}
      {%- endif -%}
      {%- endfor %}

{% endif %}
{% endblock %}
