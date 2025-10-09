"""
Django REST Framework serializers
"""
from rest_framework import serializers
from .models import Session, Message, Document


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['session_id', 'title', 'created_at', 'updated_at', 'metadata']
        read_only_fields = ['session_id', 'created_at', 'updated_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message_id', 'session', 'role', 'content', 'citations', 'created_at']
        read_only_fields = ['message_id', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'doc_id', 'filename', 'file_size', 'file_type',
            'chunks_count', 'status', 'uploaded_at', 'metadata'
        ]
        read_only_fields = ['doc_id', 'uploaded_at']

