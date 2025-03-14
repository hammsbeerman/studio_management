from django import forms
from .models import Customer, Contact, ShipTo, MailingCustomer
from localflavor.us.forms import USStateSelect

class CustomerForm(forms.ModelForm):
    required_css_class = 'required-field'
    state = forms.CharField(widget=USStateSelect(), initial='WI')
    #company_name = forms.CharField(required=True)
    class Meta:
        model = Customer
        fields = ['company_name', 'first_name', 'last_name', 'address1', 'address2', 'city', 'state', 'zipcode', 'tax_exempt', 'tax_exempt_number', 'phone1', 'phone2', 'email', 'website', 'po_number', 'tax_exempt_paperwork', 'active', 'mail_bounced_back']
        # widgets = {
        #     'tax_exempt': forms.RadioSelect(attrs={'class':'form-control'})
        # }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     #Loop through all fields and set attrs for all
    #     for field in self.fields:
    #         #print(field)
    #         new_data = {
    #             "placeholder": f'Customer {str(field)}',
    #             "class": 'form-control',
    #             #"hx-post": ".",
    #             #"hx-trigger": "keyup changed delay:500ms",
    #             #"hx-target": "#recipe-container",
    #             #"hx-swap": "innerHTML"
    #         }
    #         self.fields[str(field)].widget.attrs.update(new_data)
    #     #self.fields[''].label = ''
    #     #self.fields['name'].widget.attrs.update({'class': 'form-control-2'})
    #     #self.fields['description'].widget.attrs.update({'rows': '2'})
    #     #self.fields['directions'].widget.attrs.update({'rows': '3'})
            
class ContactForm(forms.ModelForm):
    required_css_class = 'required-field'
    state = forms.CharField(widget=USStateSelect(), initial='WI')
    class Meta:
        model = Contact
        fields = ['fname', 'lname', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            #print(field)
            new_data = {
                "placeholder": f'Contact {str(field)}',
                "class": 'form-control',
            }
            self.fields[str(field)].widget.attrs.update(
                new_data
            )

class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['notes']

class ShipToForm(forms.ModelForm):
    required_css_class = 'required-field'
    state = forms.CharField(widget=USStateSelect(), initial='WI')
    class Meta:
        model = ShipTo
        fields = ['company_name', 'first_name', 'last_name', 'address1', 'address2', 'city', 'state', 'zipcode', 'phone1', 'phone2', 'email', 'website', 'logo', 'notes']

class MailingCustomerForm(forms.ModelForm):
    required_css_class = 'required-field'
    state = forms.CharField(widget=USStateSelect(), initial='WI')
    class Meta:
        model = MailingCustomer
        fields = ['company_name', 'first_name', 'last_name', 'address1', 'address2', 'city', 'state', 'zipcode', 'tax_exempt', 'tax_exempt_number', 'phone1', 'phone2', 'email', 'website', 'active']