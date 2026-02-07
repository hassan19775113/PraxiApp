from django import template

register = template.Library()


@register.simple_tag
def get_admin_app(app_list, label):
    """Return the admin app dict with the given label, if available."""
    if not app_list:
        return None
    for app in app_list:
        if app.get("app_label") == label:
            return app
    return None
