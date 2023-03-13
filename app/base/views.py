# from django.shortcuts import render
from django.views import generic
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin

import checker

from .forms import UploadFileForm


class HomeView(generic.RedirectView):
    url = '/checker'


class CheckerView(TemplateResponseMixin, FormMixin, generic.View):
    template_name = 'checker.html'
    form_class = UploadFileForm

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            table = form.cleaned_data['table']
            checks = checker.check(table.name, table.file)
            context = self.get_context_data(form=form, checks=checks)
            return self.render_to_response(context)
        return self.form_invalid(form)
