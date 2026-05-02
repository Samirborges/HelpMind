from django.db import models
from apps.documents.models import Document


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks"
    )

    chunk_index = models.PositiveIntegerField()
    content = models.TextField()

    page_number = models.PositiveIntegerField(null=True, blank=True)

    token_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
        unique_together = ("document", "chunk_index")

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"