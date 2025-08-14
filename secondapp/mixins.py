# mixins.py
from django.views.generic import ListView, DeleteView
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect, get_object_or_404
from .models import Tag
from .forms import TagForm


class TagListAndCreateMixin(FormMixin, ListView):
    model = Tag
    form_class = TagForm
    template_name = "secondapp/tag_list_create.html"
    context_object_name = "tags"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        if "delete_tag" in request.POST:
            tag_id = request.POST.get("tag_id")
            print("Tag ID:", tag_id)
            tag = get_object_or_404(Tag, id=tag_id)
            tag.delete()
            return redirect(self.get_success_url())
        else:
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
