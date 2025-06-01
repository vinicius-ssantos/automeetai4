import os
import json
from src.factory import AutoMeetAIFactory

# Create a user preferences file with some test settings
preferences = {
    "default_language_code": "pt-br",
    "default_speaker_labels": True,
    "default_speakers_expected": 3,
    "output_directory": "output_test",
    "openai_model": "gpt-4o"
}

# Save the preferences to a file
with open("test_preferences.json", "w", encoding="utf-8") as f:
    json.dump(preferences, f, indent=4)

print("Created test preferences file with the following settings:")
for key, value in preferences.items():
    print(f"  {key}: {value}")

# Create an instance of AutoMeetAI with user preferences enabled
factory = AutoMeetAIFactory()
app = factory.create(
    use_user_preferences=True,
    user_preferences_file="test_preferences.json"
)

# Get the config provider from the app
config_provider = app._config_provider

# Check if the preferences are being used
print("\nVerifying user preferences:")
for key, expected_value in preferences.items():
    actual_value = config_provider.get(key)
    if actual_value == expected_value:
        print(f"  ✓ {key}: {actual_value}")
    else:
        print(f"  ✗ {key}: Expected {expected_value}, got {actual_value}")

# Clean up
os.remove("test_preferences.json")
print("\nTest completed and preferences file removed.")