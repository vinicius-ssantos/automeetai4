"""
Monkey patch for pydantic to make BaseSettings available from pydantic-settings.

This patch is needed because AssemblyAI is trying to import BaseSettings from pydantic,
but in Pydantic v2, BaseSettings has been moved to the pydantic-settings package.

This patch also provides a default API key for the AssemblyAI Settings class during testing.
"""

import sys
import importlib.util
import types
import os
from importlib.abc import MetaPathFinder, Loader
from typing import Optional

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

                    spec.loader = PydanticLoader()
                    return spec
            return None

    # Register the finder
    sys.meta_path.insert(0, PydanticFinder())
