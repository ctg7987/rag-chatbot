"""
Django REST Framework views for RAG Chatbot
"""
import os
import uuid
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings

from .models import Session, Message, Document
from .serializers import SessionSerializer, MessageSerializer, DocumentSerializer
from .rag_service import get_rag_service

logger = logging.getLogger(__name__)


class SessionViewSet(viewsets.ModelViewSet):
    """Session management endpoints"""
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    lookup_field = 'session_id'
    
    def list(self, request):
        """List all sessions"""
        sessions = Session.objects.all()[:50]
        serializer = self.serializer_class(sessions, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Create a new session"""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, session_id=None):
        """Get all messages for a session"""
        try:
            session = Session.objects.get(session_id=session_id)
            messages = session.messages.all()
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        except Session.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """Message management endpoints"""
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    lookup_field = 'message_id'


class DocumentViewSet(viewsets.ModelViewSet):
    """Document management endpoints"""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    lookup_field = 'doc_id'
    
    def list(self, request):
        """List all documents"""
        status_filter = request.query_params.get('status')
        if status_filter:
            documents = Document.objects.filter(status=status_filter)
        else:
            documents = Document.objects.all()
        
        serializer = self.serializer_class(documents, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        rag_service = get_rag_service()
        rag_stats = rag_service.get_stats()
        
        return Response({
            'status': 'ok',
            'database': 'connected',
            'qdrant': rag_stats.get('status', 'unknown'),
            'stats': {
                'sessions': Session.objects.count(),
                'messages': Message.objects.count(),
                'documents': Document.objects.count(),
                'vectors': rag_stats.get('vectors_count', 0)
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            {'status': 'error', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_stats(request):
    """Get system statistics"""
    try:
        rag_service = get_rag_service()
        rag_stats = rag_service.get_stats()
        
        return Response({
            'sessions': Session.objects.count(),
            'messages': Message.objects.count(),
            'documents': Document.objects.count(),
            'vectors': rag_stats.get('vectors_count', 0),
            'rag_status': rag_stats.get('status', 'unknown')
        })
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def ingest_documents(request):
    """
    Upload and ingest documents
    
    Improved with LlamaIndex for better chunking and retrieval
    """
    if 'files' not in request.FILES:
        return Response(
            {'error': 'No files provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    files = request.FILES.getlist('files')
    if not files:
        return Response(
            {'error': 'No files provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rag_service = get_rag_service()
        
        # Save files temporarily
        tmp_paths = []
        doc_records = []
        
        for file in files:
            # Save to temp location
            ext = os.path.splitext(file.name)[1]
            tmp_path = f"/tmp/{uuid.uuid4().hex}{ext}"
            
            with open(tmp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            tmp_paths.append((tmp_path, file.name))
            
            # Create document record
            doc = Document.objects.create(
                filename=file.name,
                file_size=file.size,
                file_type=ext,
                status='processing'
            )
            doc_records.append(doc)
        
        # Ingest documents using RAG service
        result = rag_service.ingest_documents(tmp_paths)
        
        # Update document statuses
        for doc in doc_records:
            if 'error' in result:
                doc.status = 'failed'
            else:
                doc.status = 'completed'
                doc.chunks_count = result['chunks_indexed'] // len(doc_records)
            doc.save()
        
        # Cleanup temp files
        for tmp_path, _ in tmp_paths:
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {tmp_path}: {e}")
        
        logger.info(f"Ingested {len(files)} files successfully")
        
        return Response({
            'doc_ids': [str(doc.doc_id) for doc in doc_records],
            'chunks_indexed': result.get('chunks_indexed', 0),
            'files_processed': len(files),
            'status': result.get('status', 'success')
        })
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def ask_question(request):
    """
    Ask a question with improved retrieval using LlamaIndex
    
    Body:
        - question: str
        - session_id: str (optional)
        - use_history: bool (default: True)
    """
    question = request.data.get('question')
    if not question:
        return Response(
            {'error': 'Question is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session_id = request.data.get('session_id')
    use_history = request.data.get('use_history', True)
    
    try:
        # Get or create session
        if session_id:
            try:
                session = Session.objects.get(session_id=session_id)
            except Session.DoesNotExist:
                session = Session.objects.create(
                    session_id=session_id,
                    title=f"Chat {session_id[:8]}"
                )
        else:
            session = Session.objects.create(
                title="New Conversation"
            )
            session_id = str(session.session_id)
        
        # Save user message
        user_message = Message.objects.create(
            session=session,
            role='user',
            content=question
        )
        
        # Get conversation context if enabled
        context = None
        if use_history:
            recent_messages = session.messages.order_by('-created_at')[:6]
            if recent_messages:
                context_parts = []
                for msg in reversed(list(recent_messages)):
                    context_parts.append(f"{msg.role.upper()}: {msg.content}")
                context = "\n".join(context_parts)
        
        # Query RAG system
        rag_service = get_rag_service()
        result = rag_service.query(question, session_context=context)
        
        # Save assistant message
        assistant_message = Message.objects.create(
            session=session,
            role='assistant',
            content=result['answer'],
            citations=result.get('citations', [])
        )
        
        logger.info(f"Answered question in session {session_id}")
        
        return Response({
            'answer': result['answer'],
            'citations': result.get('citations', []),
            'session_id': session_id,
            'status': result.get('status', 'success')
        })
        
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

