FROM odoo:18

USER root

RUN mkdir -p /opt/odoo/custom-addons

COPY . /opt/odoo/custom-addons/odoo_hms

RUN chown -R odoo:odoo /opt/odoo/custom-addons

USER odoo
