"""
Django admin configuration
"""
from django.contrib import admin
from .models import Session, Message, Document


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'title', 'created_at', 'updated_at']
    search_fields = ['title', 'session_id']
    readonly_fields = ['session_id', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'session', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']
    readonly_fields = ['message_id', 'created_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['doc_id', 'filename', 'status', 'chunks_count', 'uploaded_at']
    list_filter = ['status', 'file_type', 'uploaded_at']
    search_fields = ['filename']
    readonly_fields = ['doc_id', 'uploaded_at']

