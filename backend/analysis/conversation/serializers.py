from analysis.models import Message, ShoppingBrief, StreamOperation, UploadedImage


def serialize_brief(brief: ShoppingBrief):
    return {
        "revision": brief.revision,
        "recipient_context": brief.recipient_context,
        "category": brief.category,
        "selected_product_label": brief.selected_product_label,
        "budget_toman": brief.budget_toman,
        "use_cases": brief.use_cases,
        "hard_constraints": brief.hard_constraints,
        "unknowns": brief.unknowns,
        "contradictions": brief.contradictions,
        "provenance": brief.provenance,
        "confirmed": brief.confirmed,
        "updated_at": brief.updated_at.isoformat(),
    }


def serialize_message(message: Message):
    return {
        "id": str(message.id),
        "role": message.role,
        "state": message.state,
        "text": message.text,
        "upload_ids": [str(item.id) for item in message.uploads.all()],
        "created_at": message.created_at.isoformat(),
    }


def serialize_operation(operation: StreamOperation):
    return {
        "id": str(operation.id),
        "conversation_id": str(operation.conversation_id),
        "status": operation.status,
        "expected_brief_revision": operation.expected_brief_revision,
        "final_message_id": str(operation.final_message_id) if operation.final_message_id else None,
        "terminal_code": operation.terminal_code,
        "created_at": operation.created_at.isoformat(),
        "updated_at": operation.updated_at.isoformat(),
        "started_at": operation.started_at.isoformat() if operation.started_at else None,
        "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
    }


def serialize_conversation(conversation, *, detail=False):
    data = {
        "id": str(conversation.id),
        "status": conversation.status,
        "title": conversation.title,
        "brief_revision": conversation.brief_revision,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "expires_at": conversation.expires_at.isoformat(),
    }
    if detail:
        messages = conversation.messages.prefetch_related("uploads").order_by("created_at")[:200]
        operations = conversation.operations.order_by("-created_at")[:20]
        data.update({
            "brief": serialize_brief(conversation.brief),
            "messages": [serialize_message(item) for item in messages],
            "operations": [serialize_operation(item) for item in reversed(list(operations))],
        })
    return data


def serialize_upload(upload: UploadedImage):
    return {
        "id": str(upload.id),
        "conversation_id": str(upload.conversation_id),
        "media_type": upload.media_type,
        "size_bytes": upload.size_bytes,
        "width": upload.width,
        "height": upload.height,
        "sha256": upload.sha256,
        "created_at": upload.created_at.isoformat(),
        "expires_at": upload.expires_at.isoformat(),
    }
