"""
Monkey patch for pydantic to make BaseSettings available from pydantic-settings.

This patch is needed because AssemblyAI is trying to import BaseSettings from pydantic,
but in Pydantic v2, BaseSettings has been moved to the pydantic-settings package.

This patch also provides a default API key for the AssemblyAI Settings class during testing.

Additionally, this patch fixes issues with RawTranscriptionConfig in assemblyai 0.22.0,
which requires all fields to be present in the constructor.
"""

import sys
import importlib.util
import types
import os
import functools
from importlib.abc import MetaPathFinder, Loader
from typing import Optional, Dict, Any

# Direct monkey patch for RawTranscriptionConfig.__init__
# This needs to be done before any other imports
def patch_raw_transcription_config():
    try:
        # Try to import the module
        import assemblyai.types

        # Default values for all required fields
        defaults = {
            "language_code": "en_us",
            "punctuate": True,
            "format_text": True,
            "dual_channel": False,
            "webhook_url": None,
            "webhook_auth_header_name": None,
            "webhook_auth_header_value": None,
            "audio_start_from": None,
            "audio_end_at": None,
            "word_boost": [],
            "boost_param": None,
            "filter_profanity": False,
            "redact_pii": False,
            "redact_pii_audio": False,
            "redact_pii_policies": None,
            "redact_pii_sub": None,
            "speaker_labels": False,
            "speakers_expected": None,
            "content_safety": False,
            "content_safety_confidence": None,
            "iab_categories": False,
            "custom_spelling": None,
            "disfluencies": False,
            "sentiment_analysis": False,
            "auto_chapters": False,
            "entity_detection": False,
            "summarization": False,
            "summary_model": None,
            "summary_type": None,
            "auto_highlights": False,
            "language_detection": True,
            "speech_threshold": None,
            "speech_model": None,
        }

        # Get the original __init__ method
        original_init = assemblyai.types.RawTranscriptionConfig.__init__

        # Create a new __init__ method that provides default values
        @functools.wraps(original_init)
        def patched_init(self, **kwargs):
            # Start with defaults and update with provided kwargs
            all_kwargs = defaults.copy()
            all_kwargs.update(kwargs)

            # Call the original __init__ with all required fields
            original_init(self, **all_kwargs)

        # Replace the original __init__ with our patched version
        assemblyai.types.RawTranscriptionConfig.__init__ = patched_init

        # Also patch the Config class to address Pydantic deprecation warnings
        if hasattr(assemblyai.types.RawTranscriptionConfig, 'Config'):
            # Replace class-based Config with ConfigDict
            from pydantic import ConfigDict
            assemblyai.types.RawTranscriptionConfig.model_config = ConfigDict(extra='allow')

        print("Successfully patched RawTranscriptionConfig.__init__")
    except (ImportError, AttributeError) as e:
        print(f"Failed to patch RawTranscriptionConfig.__init__: {e}")
        # Module not available yet, will be patched later
        pass

# Try to patch immediately
patch_raw_transcription_config()

# Import BaseSettings from pydantic_settings
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # If pydantic_settings is not available, log a warning
    import logging
    logging.warning("Could not import BaseSettings from pydantic_settings. "
                   "Please install pydantic-settings package.")
    BaseSettings = None

# Set a default API key for testing
os.environ["ASSEMBLYAI_API_KEY"] = "test_api_key_12345678901234567890"

# Default values for RawTranscriptionConfig fields
RAW_TRANSCRIPTION_CONFIG_DEFAULTS: Dict[str, Any] = {
    "language_code": "pt",
    "punctuate": True,
    "format_text": True,
    "dual_channel": False,
    "webhook_url": None,
    "webhook_auth_header_name": None,
    "webhook_auth_header_value": None,
    "audio_start_from": None,
    "audio_end_at": None,
    "word_boost": [],
    "boost_param": None,
    "filter_profanity": False,
    "redact_pii": False,
    "redact_pii_audio": False,
    "redact_pii_policies": None,
    "redact_pii_sub": None,
    "speaker_labels": True,
    "speakers_expected": 2,
    "content_safety": False,
    "content_safety_confidence": None,
    "iab_categories": False,
    "custom_spelling": None,
    "disfluencies": False,
    "sentiment_analysis": False,
    "auto_chapters": False,
    "entity_detection": False,
    "summarization": False,
    "summary_model": None,
    "summary_type": None,
    "auto_highlights": False,
    "language_detection": True,
    "speech_threshold": None,
    "speech_model": None,
}

# Check if pydantic is already imported
if 'pydantic' in sys.modules:
    # If pydantic is already imported, we need to patch it
    import pydantic

    # Directly add BaseSettings to pydantic module's __dict__ to avoid triggering __getattr__
    if BaseSettings is not None:
        pydantic.__dict__['BaseSettings'] = BaseSettings

        # Also patch the __getattr__ function to handle BaseSettings
        if hasattr(pydantic, '__getattr__'):
            original_getattr = pydantic.__getattr__

            def patched_getattr(name):
                if name == 'BaseSettings':
                    return BaseSettings
                return original_getattr(name)

            pydantic.__getattr__ = patched_getattr

    # Patch RawTranscriptionConfig in assemblyai.types if it's imported
    if 'assemblyai' in sys.modules and 'assemblyai.types' in sys.modules:
        import assemblyai.types

        # Store the original __init__ method
        original_init = assemblyai.types.RawTranscriptionConfig.__init__

        # Create a patched __init__ method that uses default values
        def patched_init(self, **kwargs):
            # Merge defaults with provided kwargs
            merged_kwargs = RAW_TRANSCRIPTION_CONFIG_DEFAULTS.copy()
            merged_kwargs.update(kwargs)

            # Call the original __init__ with all required fields
            original_init(self, **merged_kwargs)

        # Replace the original __init__ with our patched version
        assemblyai.types.RawTranscriptionConfig.__init__ = patched_init
else:
    # If pydantic is not imported yet, we need to create a module finder
    # that will patch pydantic when it's imported
    class PydanticFinder(MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname == 'pydantic':
                # Temporarily remove ourselves from sys.meta_path to avoid recursion
                finder = self
                sys.meta_path.remove(finder)
                try:
                    # Get the original spec
                    spec = importlib.util.find_spec(fullname, path)
                finally:
                    # Add ourselves back to sys.meta_path
                    sys.meta_path.insert(0, finder)

                if spec:
                    # Create a loader that will patch the module
                    original_loader = spec.loader

                    class PydanticLoader(Loader):
                        def create_module(self, spec):
                            return original_loader.create_module(spec)

                        def exec_module(self, module):
                            # Execute the original module
                            original_loader.exec_module(module)

                            # Patch the module
                            if BaseSettings is not None:
                                # Directly add BaseSettings to module's __dict__ to avoid triggering __getattr__
                                module.__dict__['BaseSettings'] = BaseSettings

                                # Also patch the __getattr__ function to handle BaseSettings
                                if hasattr(module, '__getattr__'):
                                    original_getattr = module.__getattr__

                                    def patched_getattr(name):
                                        if name == 'BaseSettings':
                                            return BaseSettings
                                        return original_getattr(name)

                                    module.__getattr__ = patched_getattr

                                # Also add a hook to patch assemblyai.types.RawTranscriptionConfig when it's imported
                                def patch_assemblyai_types():
                                    if 'assemblyai' in sys.modules and 'assemblyai.types' in sys.modules:
                                        import assemblyai.types

                                        # Store the original __init__ method
                                        original_init = assemblyai.types.RawTranscriptionConfig.__init__

                                        # Create a patched __init__ method that uses default values
                                        def patched_init(self, **kwargs):
                                            # Merge defaults with provided kwargs
                                            merged_kwargs = RAW_TRANSCRIPTION_CONFIG_DEFAULTS.copy()
                                            merged_kwargs.update(kwargs)

                                            # Call the original __init__ with all required fields
                                            original_init(self, **merged_kwargs)

                                        # Replace the original __init__ with our patched version
                                        assemblyai.types.RawTranscriptionConfig.__init__ = patched_init

                                # Schedule the patch to run after this module is loaded
                                import threading
                                threading.Timer(0.1, patch_assemblyai_types).start()

                    spec.loader = PydanticLoader()
                    return spec
            return None

    # Register the finder
    sys.meta_path.insert(0, PydanticFinder())

    # Direct patch for assemblyai.types module
    def patch_assemblyai_types_module():
        try:
            import assemblyai.types

            # Check if RawTranscriptionConfig exists
            if hasattr(assemblyai.types, 'RawTranscriptionConfig'):
                # Store the original __init__ method
                original_init = assemblyai.types.RawTranscriptionConfig.__init__

                # Create a patched __init__ method that uses default values
                def patched_init(self, **kwargs):
                    # Merge defaults with provided kwargs
                    merged_kwargs = RAW_TRANSCRIPTION_CONFIG_DEFAULTS.copy()
                    merged_kwargs.update(kwargs)

                    # Call the original __init__ with all required fields
                    original_init(self, **merged_kwargs)

                # Replace the original __init__ with our patched version
                assemblyai.types.RawTranscriptionConfig.__init__ = patched_init

                # Also patch the Config class to address Pydantic deprecation warnings
                if hasattr(assemblyai.types.RawTranscriptionConfig, 'Config'):
                    # Replace class-based Config with ConfigDict
                    from pydantic import ConfigDict
                    assemblyai.types.RawTranscriptionConfig.model_config = ConfigDict(extra='allow')

        except (ImportError, AttributeError):
            # Module not available yet, will be patched later
            pass

    # Try to patch immediately
    patch_assemblyai_types_module()

    # Also schedule a delayed patch to ensure it runs after all imports
    import threading
    threading.Timer(1.0, patch_assemblyai_types_module).start()
