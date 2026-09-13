from django import forms
from .models import Employee, LeaveRequest

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'emp_id', 'first_name', 'last_name', 'email', 
            'department', 'position', 'base_salary', 'hours_worked', 
            'hire_date', 'resignation_date'
        ]
