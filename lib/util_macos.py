# Electrum - lightweight Bitcoin client
# Copyright © 2018 Alexander Schlarb
# Copyright © 2018 Calin Culianu
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

class _Void: pass

import codecs
import pathlib
from ctypes import cdll, c_bool, c_uint, c_uint16, c_void_p, POINTER, util, cast, create_string_buffer, sizeof, Structure


# macOS framework libraries used
corefoundation_path = util.find_library('CoreFoundation')
foundation_path = util.find_library('Foundation')
if corefoundation_path is None or foundation_path is None:
    raise ImportError("This module requires the macOS foundation libraries")

corefoundation = cdll.LoadLibrary(corefoundation_path)
foundation = cdll.LoadLibrary(foundation_path)

# macOS Framework constants used
NSApplicationSupportDirectory = 14
NSCachesDirectory = 13
NSUserDomainMask = 1

# macOS CoreFoundation types used
CFIndex = c_ssize_t

UniChar = c_uint16
UniChar_p = POINTER(UniChar)

class CFArray(Structure):
    _fields_ = []
CFArray_p = POINTER(CFArray)

class CFBundle(Structure):
    _fields_ = []
CFBundle_p = POINTER(CFBundle)

class CFString(Structure):
    _fields_ = []
CFString_p = POINTER(CFString)

class CFRange(Structure):
    _fields_ = [('location', CFIndex), ('length', CFIndex)]



# const UniChar* CFStringGetCharactersPtr(CFStringRef theString);
corefoundation.CFStringGetCharactersPtr.restype = UniChar_p
corefoundation.CFStringGetCharactersPtr.argtypes = [CFString_p]

# void CFStringGetCharacters(CFStringRef theString, CFRange range, UniChar* buffer);
corefoundation.CFStringGetCharacters.restype = None
corefoundation.CFStringGetCharacters.argtypes = [CFString_p, CFRange, UniChar_p]

# CFIndex CFStringGetLength(CFStringRef theString);
corefoundation.CFStringGetLength.restype = CFIndex
corefoundation.CFStringGetLength.argtypes = [CFString_p]

def CFString2Str(cf: CFString_p) -> str:
    b = corefoundation.CFStringGetCharactersPtr(cf)
    if b is None:
        # Both `CFStringGetLength` and `CFStringGetCharacters` are guranteed
        # to succeed so we'll always be able to return something
        range = CFRange()
        range.location = 0
        range.length = corefundation.CFStringGetLength(cf)
        b = create_string_buffer(range.length * sizeof(UniChar))
        corefoundation.CFStringGetCharacters(cf, range, buf)
    b = bytes(b)
    # UTF-16BE is default encoding unless the strings starts with an LE BOM
    # – Pythons's 'utf-16' decoder defaults to LE if there is no BOM
    if b.startswith(codecs.BOM_UTF16_LE):
        return b.decode('utf-16LE')
    else:
        return b.decode('utf-16BE')


# CFIndex CFArrayGetCount(CFArrayRef theArray);
corefoundation.CFArrayGetCount.restype = CFIndex
corefoundation.CFArrayGetCount.argtypes = [CFArray_p]

# const void* CFArrayGetValueAtIndex(CFArrayRef theArray, CFIndex idx);
corefoundation.CFArrayGetValueAtIndex.restype = c_void_p
corefoundation.CFArrayGetValueAtIndex.argtypes = [CFArray_p, CFIndex]

def CFArrayGetIndex(array: CFArray_p, idx: int, default=_Void) -> c_void_p:
    length = corefoundation.CFArrayGetCount(array)
    if length > idx:
        return corefoundation.CFArrayGetValueAtIndex(array, idx)
    elif default is not _Void:
        return default
    else:
        raise IndexError("CoreFramework array index is out range: {0} <= {1}".format(length, idx))


# NSArray<NSString*>* NSSearchPathForDirectoriesInDomains(NSSearchPathDirectory directory, NSSearchPathDomainMask domainMask, BOOL expandTilde);
foundation.NSSearchPathForDirectoriesInDomains.restype = CFArray_p
foundation.NSSearchPathForDirectoriesInDomains.argtypes = [c_uint, c_uint, c_bool]

def get_user_directory(type: str) -> pathlib.Path:
    """
    Retrieve the macOS directory path for the given type

    The `type` parameter must be one of: "application-support", "cache".

    Example results:

     - '/Users/calin/Library/Application Support' (for "application-support")
     - '/Users/calin/Library/Caches' (for "cache")

    Returns the discovered path on success, `None` otherwise.
    """
    if type == 'application-support':
        ns_type = NSApplicationSupportDirectory
    elif type == 'cache':
        ns_type = NSCachesDirectory
    else:
        raise AssertionError('Unexpected directory type name')
    array = foundation.NSSearchPathForDirectoriesInDomains(ns_type, NSUserDomainMask, c_bool(True))
    result = CFArrayGetIndex(array, 0, None)
    if result is not None:
        return pathlib.Path(CFString2Str(cast(result, CFString_p)))



# CFBundleRef CFBundleGetMainBundle(void);
corefoundation.CFBundleGetMainBundle.restype = CFBundle_p
corefoundation.CFBundleGetMainBundle.argtypes = []

# CFStringRef CFBundleGetIdentifier(CFBundleRef bundle);
corefoundation.CFBundleGetIdentifier.restype = CFString_p
corefoundation.CFBundleGetIdentifier.argtypes = [CFBundle_p]

def get_bundle_identifier():
    """
    Retrieve this app's bundle identifier

    Example result: 'org.python.python'

    Returns the bundle identifier on success, `None` otherwise.
    """
    bundle = corefoundation.CFBundleGetMainBundle()
    if bundle:
        return CFString2Str(corefoundation.CFBundleGetIdentifier(bundle))
