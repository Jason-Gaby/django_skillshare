from django.contrib.auth.models import User
from django.views.generic import DetailView, View, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse_lazy

from feed.models import Post
from followers.models import Follower
from profiles.models import Profile


from django.forms import modelformset_factory
# AuthorFormSet = modelformset_factory(Author, fields=["name", "title"])


class ProfileDetailView(DetailView):
    http_method_names = ["get"]
    template_name = "profiles/detail.html"
    model = User
    context_object_name = "user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.get_object()
        context = super().get_context_data(**kwargs)
        context['total_posts'] = Post.objects.filter(author=user).count()
        context['total_followers'] = Follower.objects.filter(following=user).count()

        if self.request.user.is_authenticated:
            context['you_follow'] = Follower.objects.filter(following=user, followed_by=self.request.user,).exists()

        return context


class MultiUpdateMixin:
    # A class that creates an update view that gets multiple model sources
    # and also puts to multiple model sources.

    def get(self, request, *args, **kwargs):
        context = {}
        for i in range(len(self.models)):
            self.object = self.get_object(i)
            context[self.context_object_name] = self.get_context_data()
        return self.render_to_response(self.transform_context(context))

    def transform_context(self, context):
        # Remap the context dictionary to have key values in the following form
        #   object.model_n....
        #   model_1
        #   model_2
        #   form.model_n...
        #   view
        new_context = {}
        new_context["object"] = {}
        new_context["form"] = {}
        for context_object_name in self.context_object_names:
            new_context["object"][context_object_name] = context[context_object_name]["object"]
            new_context["form"][context_object_name] = context[context_object_name]["form"]
            new_context[context_object_name] = context[context_object_name][context_object_name]
            new_context.setdefault("view", context[context_object_name]["view"])
        return new_context

    def post(self, request, *args, **kwargs):
        valid_forms = []
        for i in range(len(self.models)):
            self.object = self.get_object(i)
            form = self.get_form()
            if form.is_valid():
                valid_forms.append(form)
            else:
                return self.get(request, *args, **kwargs)

        for i, form in enumerate(valid_forms):
            self.object = self.get_object(i)
            self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_object(self, i):
        self.slug_field = self.slug_fields[i]
        self.model = self.models[i]
        self.fields = self.fields_all[i]
        self.context_object_name = self.context_object_names[i]
        return super().get_object()


class ProfileEdit(LoginRequiredMixin, MultiUpdateMixin, UpdateView):
    http_method_names = ['get', 'post']
    models = [Profile, User]
    context_object_names = ["profile", "user"]
    slug_url_kwarg = "username"
    slug_fields = ["user__username", "username"]

    fields_all = [
        [
            "image",
            "profile_name"
        ],
        [
            "username",
            "password",
            "first_name",
            "last_name",
        ],

    ]
    template_name = "profiles/edit.html"

    def get_success_url(self):
        self.success_url = reverse_lazy("profiles:detail", args=[self.object.username])
        return super().get_success_url()


class FollowView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        if "action" not in data or "username" not in data:
            return HttpResponseBadRequest("Missing data")

        try:
            other_user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            return HttpResponseBadRequest("Missing data")

        if data['action'] == 'follow':
            follower, created = Follower.objects.get_or_create(
                followed_by=request.user,
                following=other_user,
            )
        else:
            try:
                follower = Follower.objects.get(
                    followed_by=request.user,
                    following=other_user,
                )
            except Follower.DoesNotExist:
                follower = None

            if follower:
                follower.delete()

        return JsonResponse({
            'success': True,
            'wording': "Unfollow" if data['action'] == "follow" else "Follow"
        })


