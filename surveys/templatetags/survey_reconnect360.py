from django import template

register = template.Library()

@register.inclusion_tag('surveys/reconnect360/submit_button.html')
def thcs_survey_button(text="Tham gia khảo sát"):
    return {
        'button_text': text,
    }