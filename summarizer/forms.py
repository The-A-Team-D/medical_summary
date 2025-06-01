

# from django import forms
# from .models import Summary, ExampleSet

# class UploadPDFForm(forms.ModelForm):
#     class Meta:
#         model = Summary
#         fields = ['pdf_file', 'pdf_password']
#         widgets = {
#             'pdf_password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if no password'}),
#         }

# class SummaryFeedbackForm(forms.ModelForm):
#     class Meta:
#         model = Summary
#         fields = ['corrected_text']
#         widgets = {
#             'corrected_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
#         }

# class ExampleSetForm(forms.ModelForm):
#     class Meta:
#         model = ExampleSet
#         fields = ['name', 'project_type', 'description']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'project_type': forms.Select(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#         }





from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Summary, ExampleSet

class UploadPDFForm(forms.ModelForm):
    class Meta:
        model = Summary
        fields = ['pdf_file', 'pdf_password']
        widgets = {
            'pdf_password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if no password'}),
        }

class SummaryFeedbackForm(forms.ModelForm):
    class Meta:
        model = Summary
        fields = ['corrected_text']
        widgets = {
            'corrected_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15,
                'placeholder': 'Please provide your corrected version of the summary...'
            }),
        }
        labels = {
            'corrected_text': 'Corrected Summary Text'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['corrected_text'].help_text = 'Edit the summary text to provide the correct version'

class ExampleSetForm(forms.ModelForm):
    class Meta:
        model = ExampleSet
        fields = ['name', 'project_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter example set name'
            }),
            'project_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter example set name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Describe this example set...'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if ExampleSet.objects.filter(name=name).exists():
            raise ValidationError("An example set with this name already exists.")
        return name

# Custom User Creation Form
class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields"""
    
    USER_TYPE_CHOICES = [
        ('', 'Select access level...'),
        ('admin', 'Administrator - Full system access'),
        ('staff', 'Staff User - Limited access'),
    ]
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter email address'
        })
    )
    
    first_name = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Last name'
        })
    )
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_user_type(self):
        user_type = self.cleaned_data.get('user_type')
        if not user_type:
            raise ValidationError("Please select a user access level.")
        return user_type

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = self.cleaned_data['is_active']
        
        # Set user permissions based on user_type
        user_type = self.cleaned_data['user_type']
        if user_type == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif user_type == 'staff':
            user.is_staff = False
            user.is_superuser = False
        
        if commit:
            user.save()
        return user