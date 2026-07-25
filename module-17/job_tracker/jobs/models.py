from django.db import models


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    job_location = models.CharField(max_length=200)
    # salary is optional
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    application_date = models.DateField()
    deadline = models.DateField()
    notes = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.position} at {self.company_name}"
