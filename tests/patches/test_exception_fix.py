from src.exceptions import TranscriptionError

def test_get_user_friendly_message():
    # Test with default message
    error = TranscriptionError("Test error message")
    assert error.get_user_friendly_message() == "Test error message"
    
    # Test with custom user-friendly message
    error = TranscriptionError("Technical error", user_friendly_message="User-friendly error message")
    assert error.get_user_friendly_message() == "User-friendly error message"
    
    print("All tests passed!")

if __name__ == "__main__":
    test_get_user_friendly_message()