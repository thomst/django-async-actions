from django import forms


class SomeRuntimeData(forms.Form):
    one = forms.CharField(required=True)
    two = forms.CharField(required=False)


class MoreRuntimeData(forms.Form):
    three = forms.CharField(required=False)
    four = forms.CharField(required=False)
