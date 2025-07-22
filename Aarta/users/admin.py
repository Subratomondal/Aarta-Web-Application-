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
    list_display = ('username', 'email', 'is_artisan', 'is_approved_artisan', 'is_staff')
    list_filter = ('is_artisan', 'is_approved_artisan', 'is_staff')
    search_fields = ('username', 'email')
    readonly_fields = ('last_login', 'date_joined')


@admin.register(ArtisanProfile)
class ArtisanAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'is_approved', 'phone_number', 'city', 'action_buttons'
    ]
    search_fields = ['user__username', 'city', 'state']
    actions = ['approve_selected_artisans', 'reject_selected_artisans']

    def is_approved(self, obj):
        return obj.user.is_approved_artisan

    is_approved.boolean = True
    is_approved.short_description = 'Approved'

    def approve_selected_artisans(self, request, queryset):
        # ✅ Send emails first
        for profile in queryset:
            if not profile.user.is_approved_artisan:
                send_approval_email(profile.user)

        # ✅ Then, perform a single, efficient database update
        users_to_approve = User.objects.filter(artisanprofile__in=queryset, is_approved_artisan=False)
        updated_count = users_to_approve.update(is_approved_artisan=True)

        self.message_user(request, f"{updated_count} artisan(s) successfully approved and notified.")

    approve_selected_artisans.short_description = "✅ Approve selected artisans"

    def reject_selected_artisans(self, request, queryset):
        # ✅ Send emails first
        for profile in queryset:
            send_rejection_email(profile.user)

        # ✅ Then, perform a single, efficient database update
        users_to_reject = User.objects.filter(artisanprofile__in=queryset)
        updated_count = users_to_reject.update(is_active=False)

        # ✅ Updated message for accuracy
        self.message_user(request, f"{updated_count} artisan(s) rejected, deactivated, and notified.")

    reject_selected_artisans.short_description = "❌ Reject selected artisans"

    # In your ArtisanAdmin class in users/admin.py

    def action_buttons(self, obj):
        if obj.user.is_approved_artisan:
            return "✔️ Already Approved"

        # ✅ ADD THIS CHECK for rejected/inactive users
        elif not obj.user.is_active:
            return "❌ Rejected (Deactivated)"

        # If not approved and still active, show the buttons
        return format_html(
            '<a class="button" href="approve/{}/">✅ Approve</a> &nbsp; '
            '<a class="button" style="color:red" href="reject/{}/">❌ Reject</a>',
            obj.pk, obj.pk
        )

    action_buttons.short_description = 'Actions'

    # allow_tags is deprecated and not needed when using format_html

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
            send_approval_email(user)  # ✅ Consistent call
            self.message_user(request, f"{user.username} has been approved and notified.")
        else:
            self.message_user(request, f"{user.username} is already approved.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    def reject_artisan(self, request, pk):
        profile = ArtisanProfile.objects.get(pk=pk)
        user = profile.user
        send_rejection_email(user)  # ✅ Consistent call
        username = user.username
        user.is_active = False
        user.save()
        # ✅ Updated message for accuracy
        self.message_user(request, f"{username} has been rejected, deactivated, and notified.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))