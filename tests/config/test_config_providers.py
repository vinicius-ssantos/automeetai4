import os
import json
from src.config.env_config_provider import EnvConfigProvider
from src.config.user_preferences_provider import UserPreferencesProvider
from src.config.composite_config_provider import CompositeConfigProvider

# Create a user preferences file with some test settings
preferences = {
    "default_language_code": "pt-br",
    "default_speaker_labels": True,
    "default_speakers_expected": 3,
    "output_directory": "output_test",
    "openai_model": "gpt-4o"
}

# Save the preferences to a file
with open("../test_preferences.json", "w", encoding="utf-8") as f:
    json.dump(preferences, f, indent=4)

print("Created test preferences file with the following settings:")
for key, value in preferences.items():
    print(f"  {key}: {value}")

# Create the configuration providers
env_provider = EnvConfigProvider()
user_provider = UserPreferencesProvider("../test_preferences.json")
composite_provider = CompositeConfigProvider()

# Add providers to the composite provider (env first for higher precedence)
composite_provider.add_provider(env_provider)
composite_provider.add_provider(user_provider)

# Check if the preferences are being used
print("\nVerifying user preferences:")
for key, expected_value in preferences.items():
    actual_value = composite_provider.get(key)
    if actual_value == expected_value:
        print(f"  ✓ {key}: {actual_value}")
    else:
        print(f"  ✗ {key}: Expected {expected_value}, got {actual_value}")

# Test environment variable precedence
test_key = "test_precedence"
test_value_env = "env_value"
test_value_user = "user_value"

# Set the value in user preferences
user_provider.set(test_key, test_value_user)

# Set the value in environment variables
os.environ[f"AUTOMEETAI_{test_key.upper()}"] = test_value_env

# Check which value is used (should be env_value due to precedence)
actual_value = composite_provider.get(test_key)
if actual_value == test_value_env:
    print(f"\n✓ Environment variable precedence works: {test_key} = {actual_value}")
else:
    print(f"\n✗ Environment variable precedence failed: Expected {test_value_env}, got {actual_value}")

# Clean up
os.remove("../test_preferences.json")
print("\nTest completed and preferences file removed.")