"""Thin viewset for operation documents (фото документов)."""
from rest_framework import mixins, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.permissions import IsAuthenticatedRole

from .models import OperationDocument
from .serializers import (
    OperationDocumentCreateSerializer,
    OperationDocumentSerializer,
)


class OperationDocumentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Documents attached to money operations. Filter the list by
    ``?target=transaction&object_id=42`` to fetch one operation's documents."""

    queryset = OperationDocument.objects.select_related("content_type", "uploaded_by")
    serializer_class = OperationDocumentSerializer
    permission_classes = [IsAuthenticatedRole]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = None  # few docs per operation → return a plain list

    def get_queryset(self):
        qs = super().get_queryset()
        target = self.request.query_params.get("target")
        object_id = self.request.query_params.get("object_id")
        if target:
            qs = qs.filter(content_type__model=target)
        if object_id:
            qs = qs.filter(object_id=object_id)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        payload = OperationDocumentCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        upload = data["file"]
        doc = OperationDocument.objects.create(
            doc_type=data["doc_type"],
            file=upload,
            original_name=getattr(upload, "name", "")[:255],
            note=data["note"],
            content_type=data["content_type"],
            object_id=data["object_id"],
            uploaded_by=request.user if request.user.is_authenticated else None,
        )
        out = OperationDocumentSerializer(doc, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)
