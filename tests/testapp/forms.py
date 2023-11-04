from django import forms


class SomeRuntimeData(forms.Form):
    value_one = forms.CharField()
    value_two = forms.CharField()
    extra_value = forms.CharField()


class MoreRuntimeData(forms.Form):
    value_three = forms.CharField()
    value_four = forms.CharField()
