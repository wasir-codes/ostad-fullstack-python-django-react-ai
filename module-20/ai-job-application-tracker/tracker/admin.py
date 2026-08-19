from django.contrib import admin
from .models import Category, Tag, JobApplication, Interview, JobAnalysis

# registering these so I can poke at the data directly in /admin/ while
# building/debugging, without writing throwaway views just to look at rows
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(JobApplication)
admin.site.register(Interview)
admin.site.register(JobAnalysis)
