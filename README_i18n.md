# Internationalization (i18n) Support

This project supports internationalization (i18n) to allow switching between English and Arabic languages, with support for right-to-left (RTL) text direction for Arabic.

## How to Use

### Language Switching

The language can be switched using the language toggle button in the top-right corner of the main menu. The button will say "Switch to Arabic" when in English mode and "تغيير إلى الإنجليزية" (Switch to English) when in Arabic mode.

### Adding Translations

1. Wrap all user-facing strings in the `_()` function:

```python
# Instead of:
label = ttk.Label(frame, text="Hello World")

# Use:
label = ttk.Label(frame, text=_("Hello World"))
```

2. Extract messages for translation:

```bash
python tools/extract_messages.py
```

This will create/update the `locales/messages.pot` template file.

3. Create or update language-specific translation files:

For a new language, create a directory structure:
```
locales/
  ├── [lang_code]/
  │     └── LC_MESSAGES/
  │           └── messages.po
```

For example, for Arabic:
```
locales/
  ├── ar/
  │     └── LC_MESSAGES/
  │           └── messages.po
```

4. Edit the `.po` file to add translations for each string.

5. Compile the translations:

```bash
python tools/compile_messages.py
```

This will generate `.mo` files that are used at runtime.

### RTL Support

The system automatically handles Right-to-Left (RTL) text direction for Arabic. This includes:

1. Setting the `direction` property on widgets
2. Using the Tk RTL support for older versions

## Adding a New Language

To add a new language:

1. Create the appropriate directory structure in `locales/`
2. Add the language code to the extraction script
3. Translate the strings in the `.po` file
4. Compile the messages
5. Update the language switcher in the UI to support the new language

## Implementation Details

The internationalization system uses:

1. Python's built-in `gettext` module
2. A centralized `i18n.py` module with helper functions
3. Callback registration for UI updates when language changes
4. Automatic message compilation at startup

## Best Practices

1. Always wrap user-facing strings with `_()` function
2. Use meaningful, contextual source strings
3. Include placeholders in the original string, not in the translation
4. Keep UI component creation in centralized build methods to make refreshing easier

## Troubleshooting

If translations aren't working:

1. Make sure the `.mo` files are properly compiled
2. Check that strings are properly wrapped with `_()`
3. Verify the locale directory structure is correct
4. Ensure the language code matches the directory name 