from django.db import models

class Employee(models.Model):
    emp_id = models.CharField(max_length=10, unique=True, default="E0000") # e.g., E7876
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    
    # Added fields based on your Python class
    base_salary = models.FloatField(default=0.0) 
    hours_worked = models.IntegerField(default=40) 
    
    hire_date = models.DateField() 
    resignation_date = models.DateField(null=True, blank=True) 

    # 1. Overtime Calculation Logic integrated here
    def get_total_salary(self):
        overtime = 0
        if self.hours_worked > 50:
            overtime = self.hours_worked - 50
        
        # Overtime formula from your example
        total = self.base_salary + (overtime * (self.base_salary / 50))
        return total

    # 2. Assign Department Logic integrated here
    def assign_department(self, new_department):
        self.department = new_department
        self.save() # Saves the update to the Django database

    def __str__(self):
        return f"{self.emp_id} - {self.first_name} {self.last_name}"
