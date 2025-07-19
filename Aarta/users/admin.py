from users.utils.email_utils import send_approval_email, send_rejection_email

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages

from .models import ArtisanProfile

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):
    list_display = ('username', 'email', 'is_artisan', 'is_approved_artisan', 'is_staff', 'is_superuser')
    list_filter = ('is_artisan', 'is_approved_artisan', 'is_staff')
    search_fields = ('username', 'email')
    readonly_fields = ('last_login', 'date_joined')


@admin.register(ArtisanProfile)
class ArtisanAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'is_approved', 'phone_number', 'city',
        'address', 'postal_code', 'state', 'action_buttons'
    ]
    search_fields = ['user__username', 'city', 'state']
    actions = ['approve_selected_artisans', 'reject_selected_artisans']

    def is_approved(self, obj):
        return obj.user.is_approved_artisan
    is_approved.boolean = True
    is_approved.short_description = 'Approved'

    def approve_selected_artisans(self, request, queryset):
        count = 0
        for profile in queryset:
            user = profile.user
            if not user.is_approved_artisan:
                user.is_approved_artisan = True
                user.save()
                send_approval_email(user.email, user.username)
                count += 1
        self.message_user(request, f"{count} artisan(s) successfully approved and notified.")
    approve_selected_artisans.short_description = "✅ Approve selected artisans"

    def reject_selected_artisans(self, request, queryset):
        count = queryset.count()
        for profile in queryset:
            user = profile.user
            send_rejection_email(user)
            user.is_active = False
            user.save()
        self.message_user(request, f"{count} artisan(s) rejected, deleted, and notified.")
    reject_selected_artisans.short_description = "❌ Reject selected artisans"

    def action_buttons(self, obj):
        if obj.user.is_approved_artisan:
            return "✔️ Already Approved"
        return format_html(
            '<a class="button" href="approve/{}/">✅ Approve</a> &nbsp; '
            '<a class="button" style="color:red" href="reject/{}/">❌ Reject</a>',
            obj.pk, obj.pk
        )
    action_buttons.short_description = 'Actions'
    action_buttons.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:pk>/', self.admin_site.admin_view(self.approve_artisan), name='approve_artisan'),
            path('reject/<int:pk>/', self.admin_site.admin_view(self.reject_artisan), name='reject_artisan'),
        ]
        return custom_urls + urls

    def approve_artisan(self, request, pk):
        profile = ArtisanProfile.objects.get(pk=pk)
        user = profile.user
        if not user.is_approved_artisan:
            user.is_approved_artisan = True
            user.save()
            send_approval_email(profile.user)
            self.message_user(request, f"{user.username} has been approved and notified.")
        else:
            self.message_user(request, f"{user.username} is already approved.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    def reject_artisan(self, request, pk):
        profile = ArtisanProfile.objects.get(pk=pk)
        user = profile.user
        send_rejection_email(profile.user)
        username = user.username
        user.is_active = False
        user.save()
        self.message_user(request, f"{username} has been rejected, deleted, and notified.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))
