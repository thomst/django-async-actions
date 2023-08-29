from django import forms
from item_messages.constants import DEFAULT_TAGS


class MessageFrom(forms.Form):
    message = forms.CharField(widget=forms.Textarea())
    level = forms.ChoiceField(choices=[(k, v) for k, v in DEFAULT_TAGS.items()])