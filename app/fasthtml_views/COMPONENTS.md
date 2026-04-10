# Reusable FastHTML Components

This module provides reusable components for modal dialogs and buttons to maintain consistency across all pages.

## Components

### `confirmation_modal()`

Creates a reusable confirmation modal dialog.

#### Parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `modal_id` | str | Required | Unique ID for the modal (e.g., "sync-modal", "generate-modal") |
| `title` | str | Required | Modal title (e.g., "Sync Project?", "Generate Token?") |
| `message` | str | Required | Modal message (use `\n\n` for line breaks) |
| `cancel_text` | str | "Cancel" | Text for cancel button |
| `submit_text` | str | "Confirm" | Text for submit button |
| `cancel_class` | str | "modal-btn modal-btn-cancel" | CSS class for cancel button |
| `submit_class` | str | "modal-btn modal-btn-confirm" | CSS class for submit button |
| `cancel_onclick` | str | None | JavaScript function for cancel button |
| `submit_onclick` | str | None | JavaScript function for submit button |
| `message_style` | str | "white-space: pre-line;" | CSS style for message paragraph |

#### Usage Example:

```python
from app.fasthtml_views.components import confirmation_modal

# Create a sync confirmation modal
sync_modal = confirmation_modal(
    modal_id="sync-modal",
    title="Sync Project?",
    message="This will fetch the latest project data from the server.\n\nThis action cannot be undone.",
    submit_text="Sync",
    submit_onclick="confirmSync()",
    cancel_onclick="closeSyncModal()",
)

# Add to your page
page = Html(
    Head(Style(get_modal_styles())),
    Body(
        # ... page content
        sync_modal,
    )
)
```

### `get_modal_styles()`

Returns CSS styles for modal components. Include this in your page's `Style()` component.

#### Usage:

```python
from app.fasthtml_views.components import get_modal_styles

page = Html(
    Head(
        Style(get_modal_styles()),
        # ... other styles
    ),
    # ...
)
```

### `get_sync_button_styles()`

Returns CSS styles for sync/primary buttons. Include this in pages that use sync buttons.

#### Usage:

```python
from app.fasthtml_views.components import get_sync_button_styles

page = Html(
    Head(
        Style(get_sync_button_styles()),
        # ... other styles
    ),
    # ...
)
```

## Complete Example

Here's a complete example showing how to use the modal component in a page:

```python
from fasthtml.common import Html, Head, Body, Style, Script, to_xml
from app.fasthtml_views.components import (
    confirmation_modal,
    get_modal_styles,
    get_sync_button_styles,
)

def my_page_html():
    # Create modals
    sync_modal = confirmation_modal(
        modal_id="sync-modal",
        title="Sync Data?",
        message="This will sync data from the server.\n\nContinue?",
        submit_text="Sync",
        submit_onclick="confirmSync()",
        cancel_onclick="closeSyncModal()",
    )

    page = Html(
        Head(
            Meta(charset="UTF-8"),
            Title("My Page"),
            Style(get_modal_styles()),  # Include modal styles
            Style(get_sync_button_styles()),  # Include button styles
            Style(_page_specific_styles()),  # Your custom styles
        ),
        Body(
            # Page content
            Div(...),

            # Modals
            sync_modal,

            # Scripts
            Script("""
                function showSyncModal() {
                    document.getElementById('sync-modal').classList.add('active');
                }

                function closeSyncModal() {
                    document.getElementById('sync-modal').classList.remove('active');
                }

                async function confirmSync() {
                    closeSyncModal();
                    await syncData();
                }

                async function syncData() {
                    // Your sync logic here
                }
            """),
        )
    )

    return to_xml(page)
```

## Button Classes

### Standard Button Classes:

- `modal-btn modal-btn-cancel` - Gray cancel button
- `modal-btn modal-btn-confirm` - Blue/purple confirm button
- `btn-sync` - Sync button
- `btn-primary` - Primary action button
- `btn-create` - Create action button

### Button States:

- `.syncing` - Applied when button is in loading state
- `.spinning` - Applied to icons during loading

## Button Styling Consistency

All buttons across the application should follow these guidelines:

1. **Border Radius**: 8px
2. **Icon Size**: 18px × 18px
3. **Alignment**: `display: flex; align-items: center; gap: 8px;`
4. **Background**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
5. **Hover**: Transform and box-shadow effects

## JavaScript Requirements

Each modal requires three JavaScript functions:

```javascript
// Show modal
function show<Name>Modal() {
    document.getElementById('<name>-modal').classList.add('active');
}

// Close modal
function close<Name>Modal() {
    document.getElementById('<name>-modal').classList.remove('active');
}

// Confirm and execute
async function confirm<Name>() {
    close<Name>Modal();
    await <action>();
}
```

## Modal Behavior

1. User clicks action button (e.g., "Sync")
2. Modal appears with title and message
3. User clicks "Cancel" or "Confirm"
4. If "Confirm", modal closes and action executes
5. If "Cancel", modal closes without action

## Benefits

- ✅ **Consistency**: All modals look and behave the same
- ✅ **Maintainability**: Single source of truth for modal styles
- ✅ **Reusability**: Write once, use everywhere
- ✅ **Type Safety**: Parameters are clearly defined
- ✅ **Documentation**: Self-documenting with parameter names
- ✅ **Flexibility**: Customizable for different use cases
