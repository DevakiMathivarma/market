from django import forms
import re

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Name", "oninput": "validateName(this)"}),
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Email"}))
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={"placeholder": "Phone number", "oninput": "validatePhone(this)"}),
    )
    how_find = forms.ChoiceField(
        choices=[
            ("", "How did you find us?"),
            ("google", "Google"),
            ("social", "Social Media"),
            ("friend", "Friend"),
            ("other", "Other"),
        ],
        initial="",
    )
    message = forms.CharField(widget=forms.Textarea(attrs={"placeholder": "Message"}))

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not re.fullmatch(r"[A-Za-z ]+", name):
            raise forms.ValidationError("Name should only contain letters and spaces.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not re.fullmatch(r"[0-9]+", phone):
            raise forms.ValidationError("Phone should contain only numbers.")
        return phone
