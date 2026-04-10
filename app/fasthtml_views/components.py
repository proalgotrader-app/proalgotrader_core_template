"""Reusable FastHTML components for modal dialogs and buttons."""

from fasthtml.common import H3, Button, Div, P


def confirmation_modal(
    modal_id: str,
    title: str,
    message: str,
    cancel_text: str = "Cancel",
    submit_text: str = "Confirm",
    cancel_class: str = "modal-btn modal-btn-cancel",
    submit_class: str = "modal-btn modal-btn-confirm",
    cancel_onclick: str = None,
    submit_onclick: str = None,
    message_style: str = "white-space: pre-line;",
) -> Div:
    """Create a reusable confirmation modal.

    Args:
        modal_id: Unique ID for the modal (e.g., "sync-modal", "generate-modal")
        title: Modal title (e.g., "Sync Project?", "Generate Token?")
        message: Modal message (use \\n for line breaks)
        cancel_text: Text for cancel button (default: "Cancel")
        submit_text: Text for submit button (default: "Confirm")
        cancel_class: CSS class for cancel button (default: "modal-btn modal-btn-cancel")
        submit_class: CSS class for submit button (default: "modal-btn modal-btn-confirm")
        cancel_onclick: JavaScript function for cancel button (e.g., "closeSyncModal()")
        submit_onclick: JavaScript function for submit button (e.g., "confirmSync()")
        message_style: CSS style for message paragraph (default: "white-space: pre-line;")

    Returns:
        FastHTML Div component representing the modal

    Example:
        ```python
        sync_modal = confirmation_modal(
            modal_id="sync-modal",
            title="Sync Project?",
            message="This will fetch the latest project data from the server.\\n\\nThis action cannot be undone.",
            submit_text="Sync",
            submit_onclick="confirmSync()",
            cancel_onclick="closeSyncModal()",
        )
        ```
    """
    return Div(
        Div(
            H3(title),
            P(message, style=message_style),
            Div(
                Button(cancel_text, cls=cancel_class, onclick=cancel_onclick),
                Button(submit_text, cls=submit_class, onclick=submit_onclick),
                cls="modal-buttons",
            ),
            cls="modal",
        ),
        id=modal_id,
        cls="modal-overlay",
    )


def get_modal_styles() -> str:
    """Get CSS styles for modal components.

    Returns:
        CSS string for modal styles

    This should be included in the Style() component of pages that use modals.
    """
    return """
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9999;
            justify-content: center;
            align-items: center;
        }

        .modal-overlay.active {
            display: flex;
        }

        .modal-overlay.show {
            display: flex;
        }

        .modal {
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .modal h3 {
            margin: 0 0 15px 0;
            color: #333;
            font-size: 20px;
        }

        .modal p {
            margin: 0 0 20px 0;
            color: #666;
            line-height: 1.6;
        }

        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }

        .modal-btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: all 0.2s;
        }

        .modal-btn-cancel {
            background: #e5e7eb;
            color: #374151;
        }

        .modal-btn-cancel:hover {
            background: #d1d5db;
        }

        .modal-btn-confirm {
            background: #667eea;
            color: white;
        }

        .modal-btn-confirm:hover {
            background: #5568d3;
        }
    """


def get_sync_button_styles() -> str:
    """Get CSS styles for sync/primary buttons.

    Returns:
        CSS string for button styles

    This should be included in the Style() component of pages that use sync buttons.
    """
    return """
        .btn-sync, .btn-primary, .btn-create {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-sync:hover, .btn-primary:hover, .btn-create:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-sync:disabled, .btn-primary:disabled, .btn-create:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-sync.syncing {
            background: #6c757d;
        }

        .sync-icon, .plus-icon {
            width: 18px;
            height: 18px;
            display: inline-block;
            vertical-align: middle;
        }

        .sync-icon.spinning {
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    """
