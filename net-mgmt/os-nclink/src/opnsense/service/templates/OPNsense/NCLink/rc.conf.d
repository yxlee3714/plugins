{% if helpers.exists('OPNsense.nclink.general.enabled') and OPNsense.nclink.general.enabled == '1' %}
nclink_enable="YES"
{% else %}
nclink_enable="NO"
{% endif %}
