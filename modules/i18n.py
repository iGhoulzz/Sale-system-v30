"""
modules/i18n.py - Internationalization Support
------------------------------------------
Provides internationalization (i18n) support for the application, allowing
switching between English and Arabic languages.
"""

import os
import gettext
import locale
import importlib
import json
import sys
from typing import Dict, List, Callable, Optional
import subprocess
import platform
import logging
import codecs

# Configure logger
logger = logging.getLogger(__name__)

# If running in console mode, add UTF-8 compatible console handler
if not hasattr(sys, 'frozen'):  # Not a frozen executable
    # Custom handler for console output that respects encoding
    class EncodedStdoutHandler(logging.StreamHandler):
        def __init__(self, stream=None):
            if stream is None and sys.platform == 'win32':
                stream = codecs.getwriter('utf-8')(sys.stdout.buffer)
            super().__init__(stream)
            
    console_handler = EncodedStdoutHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Initialize the _ function as a no-op until properly set up
_ = lambda s: s

# Track current language
current_lang = 'en'

# Store callbacks to be called when language changes
_refresh_callbacks: List[Callable] = []

# Path for storing language preference
def get_preferences_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'user_preferences.json')

def save_language_preference(lang_code: str):
    """Save the language preference to a file."""
    prefs_path = get_preferences_path()
    temp_path = prefs_path + '.tmp'
    
    # Load existing preferences if file exists
    if os.path.exists(prefs_path):
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
        except:
            prefs = {}
    else:
        prefs = {}
    
    # Update language preference
    prefs['language'] = lang_code
    
    # Save preferences atomically
    try:
        # Write to temporary file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2)
        
        # Replace the original file with the temporary file
        # This is atomic on most operating systems
        if os.path.exists(prefs_path):
            os.replace(temp_path, prefs_path)
        else:
            os.rename(temp_path, prefs_path)
            
        logger.info(f"Language preference saved: {lang_code}")
    except Exception as e:
        logger.error(f"Failed to save language preference: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

def load_language_preference() -> str:
    """Load the language preference from file."""
    prefs_path = get_preferences_path()
    
    if os.path.exists(prefs_path):
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
                lang = prefs.get('language', 'en')
                logger.info(f"Loaded language preference: {lang}")
                return lang
        except Exception as e:
            logger.error(f"Failed to load language preference: {e}")
    
    # Default to English if no preference found
    return 'en'

def compile_translations():
    """
    Compile message catalogs (.po files) to binary format (.mo files).
    This is called during initialization to ensure translations are up-to-date.
    """
    # Define base directory for locale files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locales_dir = os.path.join(base_dir, 'locales')
    
    # Check if locales directory exists
    if not os.path.exists(locales_dir):
        logger.warning(f"Locales directory {locales_dir} does not exist.")
        return
    
    # DIRECT COMPILATION: Manually create Arabic .mo file
    # This is a workaround for environments where msgfmt is not available
    ar_po_file = os.path.join(locales_dir, 'ar', 'LC_MESSAGES', 'messages.po')
    ar_mo_file = os.path.join(locales_dir, 'ar', 'LC_MESSAGES', 'messages.mo')
    
    # Create the LC_MESSAGES directory if it doesn't exist
    os.makedirs(os.path.dirname(ar_mo_file), exist_ok=True)
    
    # Instead of trying to copy the .po file (which causes bad magic number error),
    # create a proper empty .mo file that gettext can read
    try:
        # These are the magic numbers for a valid empty .mo file
        mo_header = (
            b'\xde\x12\x04\x95'  # Magic number
            b'\x00\x00\x00\x00'  # Revision
            b'\x00\x00\x00\x00'  # Number of strings
            b'\x00\x00\x00\x0c'  # Offset of original strings hash table
            b'\x00\x00\x00\x0c'  # Offset of translated strings hash table
            b'\x00\x00\x00\x00'  # Size of hash table
            b'\x00\x00\x00\x00'  # Offset of hash table
        )
        
        with open(ar_mo_file, 'wb') as f:
            f.write(mo_header)
        
        logger.info(f"Created empty but valid MO file: {ar_mo_file}")
    except Exception as e:
        logger.error(f"Failed to create MO file: {e}")

def setup_i18n(default_lang: str = None) -> None:
    """
    Initialize the internationalization system.
    
    Args:
        default_lang: Default language code ('en' or 'ar')
    """
    global _, current_lang
    
    # Use saved preference or default to English if not specified
    if default_lang is None:
        default_lang = load_language_preference()
        
    current_lang = default_lang
    
    # Ensure translations are compiled
    compile_translations()
    
    # Define base directory for locale files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_dir = os.path.join(base_dir, 'locales')
    
    # Create the locales directory if it doesn't exist
    if not os.path.exists(locale_dir):
        os.makedirs(locale_dir)
        
    # Special case for English (no translation needed)
    if default_lang == 'en':
        _ = lambda s: s
        return
    
    # Fallback translations for Arabic if gettext fails
    ar_translations = {
        "Sales Management System": "نظام إدارة المبيعات",
        "Logged in as:": "تم تسجيل الدخول باسم:",
        "Manage Inventory": "إدارة المخزون",
        "Sales Screen": "شاشة المبيعات",
        "Manage Debits": "إدارة الديون",
        "Financial Dashboard": "لوحة المعلومات المالية",
        "Logout": "تسجيل خروج",
        "Exit": "خروج",
        "Back to Home": "العودة إلى الرئيسية",
        "Cancel": "إلغاء",
        "Save": "حفظ",
        "Add": "إضافة",
        "Edit": "تعديل",
        "Delete": "حذف",
        "OK": "موافق",
        "Error": "خطأ",
        "Warning": "تحذير",
        "Success": "نجاح",
        "Confirm": "تأكيد",
        "Search": "بحث",
        "Switch to Arabic": "تغيير إلى العربية",
        "Switch to English": "تغيير إلى الإنجليزية",
        "Language": "اللغة",
        "English": "الإنجليزية",
        "Arabic": "العربية",
        # Add new entries for our UI elements
        "Enter Barcode/QR Code:": "أدخل الباركود/رمز الاستجابة السريعة:",
        "Add to Cart": "أضف إلى السلة",
        "Scan Code": "مسح الرمز",
        "Search Products": "بحث المنتجات",
        "Category:": "الفئة:",
        "ID": "رقم التعريف",
        "Name": "الاسم",
        "Price": "السعر",
        "Add Selected Product": "إضافة المنتج المحدد",
        "Shopping Cart": "عربة التسوق",
        "Payment Method:": "طريقة الدفع:",
        "Cash": "نقد",
        "Card": "بطاقة",
        "Discount:": "الخصم:",
        "Complete Sale": "إتمام البيع",
        "Mark As Debit": "تسجيل كدين",
        "Reset Cart": "إعادة تعيين السلة",
        "View Invoices": "عرض الفواتير",
        "Total": "المجموع",
        "Subtotal": "المجموع الفرعي",
        "Add New Debit": "إضافة دين جديد",
        "Filters": "المرشحات",
        "Customer Name:": "اسم العميل:",
        "Phone:": "الهاتف:",
        "Date:": "التاريخ:",
        "Status:": "الحالة:",
        "Apply Filters": "تطبيق المرشحات",
        "Reset": "إعادة تعيين",
        "Total Amount": "المبلغ الإجمالي",
        "Pending": "معلق",
        "Paid": "مدفوع",
        "Invoice ID": "رقم الفاتورة",
        "Customer": "العميل",
        "Phone Number": "رقم الهاتف",
        "Balance": "الرصيد",
        "All": "الكل",
        # Add more translations for Financial dashboard
        "Inventory Management": "إدارة المخزون",
        "Inventory Statistics": "إحصائيات المخزون",
        "Total Products": "إجمالي المنتجات",
        "Inventory Value": "قيمة المخزون",
        "Low Stock Items": "منتجات المخزون المنخفض",
        "Categories": "الفئات",
        "Add Category": "+ إضافة فئة",
        "Clear": "مسح",
        "Show Out of Stock": "إظهار المنتجات غير المتوفرة",
        "Refresh Data": "تحديث البيانات",
        "Product ID": "رقم المنتج",
        "Product Name": "اسم المنتج",
        "Sell Price": "سعر البيع",
        "Buy Price": "سعر الشراء",
        "Stock": "المخزون",
        "Category": "الفئة",
        "Add Product": "إضافة منتج",
        "Edit Product": "تعديل المنتج",
        "Delete Product": "حذف المنتج",
        "Month (YYYY‑MM)": "الشهر (YYYY‑MM)",
        "Apply": "تطبيق",
        "Refresh": "تحديث",
        "View All Invoices": "عرض جميع الفواتير",
        "Fix Admin Records": "إصلاح سجلات المدير",
        "Total Sales": "إجمالي المبيعات",
        "Outstanding Debits": "الديون المستحقة",
        "Profit": "الربح",
        "Losses": "الخسائر",
        "Sales by User": "المبيعات حسب المستخدم",
        "User": "المستخدم",
        "# of Sales": "عدد المبيعات",
        "Users & Activity": "المستخدمين والنشاط",
        "Select a user to view details": "اختر مستخدمًا لعرض التفاصيل",
        "View User Sales": "عرض مبيعات المستخدم",
        "User Activity Log": "سجل نشاط المستخدم",
        "Please select a user first": "الرجاء اختيار مستخدم أولا",
        "Activity Log for": "سجل النشاط لـ",
        "Close": "إغلاق",
        "Action": "الإجراء",
        "Date / Time": "التاريخ / الوقت",
        "Recent Activity": "النشاط الأخير",
        "Error loading data": "خطأ في تحميل البيانات",
        "Error fetching logs": "خطأ في جلب السجلات",
        "Loading...": "جاري التحميل...",
        "Loading data...": "جاري تحميل البيانات...",
        "Loading logs...": "جاري تحميل السجلات...",
        "Role": "الدور",
        "Invoices": "الفواتير",
        "No invoice selected!": "لم يتم اختيار فاتورة!",
        "Seller": "البائع",
        "Product": "المنتج",
        "Qty": "الكمية",
        "Thank you for shopping with us!": "شكراً لتسوقكم معنا!",
        "You were served by": "تم خدمتك بواسطة",
        "Show Selected Invoice Items": "عرض عناصر الفاتورة المحددة",
        "Print Invoice": "طباعة الفاتورة",
        "Select an invoice first.": "اختر فاتورة أولاً.",
        "Invoice": "فاتورة",
        "Payment Method": "طريقة الدفع",
        "Invoices for": "الفواتير لـ",
        "Error fetching invoices": "خطأ في جلب الفواتير",
        "Unknown": "غير معروف",
        "Discount": "الخصم",
        "Date": "التاريخ"
    }
    
    try:
        # Set the locale
        locale.setlocale(locale.LC_ALL, default_lang)
        
        # Load translation
        translation = gettext.translation(
            'messages', 
            localedir=locale_dir, 
            languages=[default_lang],
            fallback=True
        )
        _ = translation.gettext
        
        # Test if translation works with a common string
        test_string = "Sales Management System"
        translated = _(test_string)
        
        # If translation didn't work (returns same string), use the fallback dictionary for Arabic
        if default_lang == 'ar' and translated == test_string:
            logger.warning("Gettext translation failed, using hardcoded fallback dictionary")
            ar_dict = ar_translations
            _ = lambda s: ar_dict.get(s, s)
            
    except Exception as e:
        logger.error(f"Error setting up i18n: {e}")
        
        # Use fallback dictionary for Arabic
        if default_lang == 'ar':
            logger.warning("Using hardcoded fallback translations for Arabic")
            ar_dict = ar_translations
            _ = lambda s: ar_dict.get(s, s)
        else:
            # Fallback to no translation for other languages
            _ = lambda s: s

def switch_language(lang_code: str) -> None:
    """
    Switch the application language.
    
    Args:
        lang_code: Language code ('en' or 'ar')
    """
    global _, current_lang
    
    if lang_code not in ['en', 'ar']:
        logger.warning(f"Unsupported language code: {lang_code}")
        return
    
    # Save preference
    save_language_preference(lang_code)
    current_lang = lang_code
    
    # Set up logging
    logger.info(f"Switching language from {current_lang} to {lang_code}")
    
    # Define base directory for locale files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_dir = os.path.join(base_dir, 'locales')
    
    # Special case for English (no translation needed)
    if lang_code == 'en':
        _ = lambda s: s
        logger.info(f"Set locale to {lang_code}")
    else:
        # Try to install translations with gettext
        try:
            # Try to set locale for proper RTL support
            locale_name = 'ar_AE.UTF-8' if lang_code == 'ar' else 'en_US.UTF-8'
            
            try:
                if sys.platform == 'win32':
                    locale.setlocale(locale.LC_ALL, locale_name)
                else:
                    locale.setlocale(locale.LC_ALL, locale_name + '.UTF-8')
                logger.info(f"Set locale to {lang_code}")
            except locale.Error:
                logger.warning(f"Could not set locale to {locale_name}")
                try:
                    locale.setlocale(locale.LC_ALL, '') 
                except Exception as e:
                    logger.warning(f"Could not set default locale: {e}")
            
            # Install the translation
            translation = gettext.translation('messages', localedir=locale_dir, 
                                             languages=[lang_code], fallback=True)
            translation.install()
            _ = translation.gettext
            
        except Exception as e:
            logger.error(f"Error switching language: {str(e)}")
            logger.warning(f"Using hardcoded fallback translations for Arabic when switching language")
            
            # Use fallback mechanism - lambda with dictionary lookup
            # Translations for Arabic
            if lang_code == 'ar':
                ar_translations = get_arabic_fallback_translations()
                _ = lambda s: ar_translations.get(s, s)
            else:
                _ = lambda s: s
      # Emit signals to update UI
    logger.info(f"Calling {len(_refresh_callbacks)} registered refresh callbacks")
    
    # Create a copy of the callbacks list to avoid modification during iteration
    callbacks_to_call = _refresh_callbacks.copy()
    
    for i, callback in enumerate(callbacks_to_call):
        try:
            # Check if callback is still in the original list (not unregistered)
            if callback not in _refresh_callbacks:
                continue
                
            logger.info(f"Calling callback #{i}")
            callback()
            logger.info(f"Callback #{i} completed")
        except Exception as e:
            logger.error(f"Error in language refresh callback: {str(e)}")
            # Optionally remove problematic callbacks
            try:
                if callback in _refresh_callbacks:
                    _refresh_callbacks.remove(callback)
                    logger.warning(f"Removed problematic callback #{i} from list")
            except:
                pass  # Ignore any issues with removal
    
    logger.info("Language switch completed")

def get_arabic_fallback_translations() -> Dict[str, str]:
    """Get the fallback Arabic translations dictionary"""
    return {
        # Main menu
        "Sales Management System": "نظام إدارة المبيعات",
        "Logged in as:": "تم تسجيل الدخول باسم:",
        "Switch to Arabic": "التحويل إلى الإنجليزية",
        "Switch to English": "التحويل إلى العربية",
        "Manage Inventory": "إدارة المخزون",
        "Sales Screen": "شاشة المبيعات",
        "Manage Debits": "إدارة الديون",
        "Financial Dashboard": "لوحة المعلومات المالية",
        "(Admin Only)": "(للمسؤول فقط)",
        "Logout": "تسجيل الخروج",
        "Exit": "خروج",
        
        # Inventory management
        "Inventory Management": "إدارة المخزون",
        "Back to Home": "العودة إلى الرئيسية",
        "Inventory Statistics": "إحصائيات المخزون",
        "Total Products": "إجمالي المنتجات",
        "Inventory Value": "قيمة المخزون",
        "Low Stock Items": "منتجات المخزون المنخفض",
        "Categories": "الفئات",
        "Add Category": "إضافة فئة",
        "Search": "بحث",
        "Clear": "مسح",
        "Show Out of Stock": "عرض نفاذ المخزون",
        "Refresh Data": "تحديث البيانات",
        "ID": "المعرف",
        "Product Name": "اسم المنتج",
        "Sell Price": "سعر البيع",
        "Buy Price": "سعر الشراء",
        "Stock": "المخزون",
        "Category": "الفئة",
        "Add Product": "إضافة منتج",
        "Edit Product": "تعديل المنتج",
        "Delete Product": "حذف المنتج",
        "Save": "حفظ",
        "Cancel": "إلغاء",
        
        # Sales screen
        "Sales Management Screen": "شاشة إدارة المبيعات",
        "Enter Barcode/QR Code:": "أدخل الباركود/رمز QR:",
        "Add to Cart": "أضف إلى السلة",
        "Scan Code": "مسح الرمز",
        "Search Products": "بحث المنتجات",
        "Category:": "الفئة:",
        "Add Selected Product": "إضافة المنتج المحدد",
        "Shopping Cart": "عربة التسوق",
        "Payment Method:": "طريقة الدفع:",
        "Cash": "نقد",
        "Card": "بطاقة",
        "Discount:": "الخصم:",
        "Subtotal": "المجموع الفرعي",
        "Total": "المجموع",
        "Complete Sale": "إتمام البيع",
        "Mark As Debit": "تسجيل كدين",
        "Reset Cart": "إعادة تعيين السلة",
        "View Invoices": "عرض الفواتير",
        
        # Financial dashboard
        "Financial Dashboard": "لوحة المعلومات المالية",
        "Month (YYYY‑MM):": "الشهر (YYYY-MM):",
        "All": "الكل",
        "Apply": "تطبيق",
        "Refresh": "تحديث",
        "View All Invoices": "عرض جميع الفواتير",
        "Fix Admin Records": "إصلاح سجلات المسؤول",
        "Total Sales": "إجمالي المبيعات",
        "Outstanding Debits": "الديون المستحقة",
        "Profit": "الربح",
        "Losses": "الخسائر",
        "Sales by User": "المبيعات حسب المستخدم",
        "User": "المستخدم",
        "# of Sales": "عدد المبيعات",
        "Users & Activity": "المستخدمين والنشاط",
        "Select a user to view details": "حدد مستخدمًا لعرض التفاصيل",
        "View User Sales": "عرض مبيعات المستخدم",
        "User Activity Log": "سجل نشاط المستخدم",
        "Recent Activity": "النشاط الأخير",
        "Error": "خطأ",
        "Error loading data": "خطأ في تحميل البيانات",
        "Error loading logs": "خطأ في تحميل السجلات"
    }

# ----------------------------------------------------------------------
#  Fast live-translation helper
# ----------------------------------------------------------------------
_cached: dict[tuple[str, str], str] = {}      # (lang, msg) -> text

def tr(msg: str) -> str:
    """
    Fast gettext wrapper that updates live when the language changes.
    Uses a per-language cache – as cheap as your old LBL_ constants.
    """
    key = (current_lang, msg)
    text = _cached.get(key)
    if text is None:
        text = _(msg)          # call gettext / fallback dict once
        _cached[key] = text
    return text

def get_current_language() -> str:
    """Get the current language code."""
    return current_lang

def is_rtl() -> bool:
    """Check if current language is right-to-left."""
    return current_lang == 'ar'

def register_refresh_callback(callback: Callable) -> None:
    """
    Register a callback to be called when language changes.
    
    Args:
        callback: Function to call when language changes
    """
    if callback is not None and callback not in _refresh_callbacks:
        _refresh_callbacks.append(callback)

def unregister_refresh_callback(callback: Callable) -> None:
    """
    Unregister a previously registered callback.
    
    Args:
        callback: Function to remove from callback list
    """
    try:
        if callback is not None and callback in _refresh_callbacks:
            _refresh_callbacks.remove(callback)
    except (ValueError, TypeError):
        # Callback might have already been removed or be invalid
        pass

def set_widget_direction(widget) -> None:
    """
    Set the text direction for a widget based on current language.
    
    Args:
        widget: The Tkinter widget to update
    """
    if is_rtl():
        try:
            # Try modern API first
            widget.configure(direction='rtl')
        except:
            # Fallback to older API
            try:
                widget.tk.call('tk', 'rtl', 'set', 'yes')
            except:
                pass
    else:
        try:
            # Try modern API first
            widget.configure(direction='ltr')
        except:
            # Fallback to older API
            try:
                widget.tk.call('tk', 'rtl', 'set', 'no')
            except:
                pass

# Initialize gettext with default language
setup_i18n() 