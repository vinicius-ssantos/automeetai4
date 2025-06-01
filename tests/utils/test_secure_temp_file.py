import os
import unittest
from src.utils.file_utils import secure_temp_file

class TestSecureTempFile(unittest.TestCase):
    """Test cases for the secure_temp_file function."""
    
    def test_secure_temp_file_creates_and_deletes(self):
        """Test that secure_temp_file creates a file and deletes it after the context is exited."""
        # Use the secure_temp_file context manager
        with secure_temp_file(suffix='.txt') as temp_path:
            # Verify the file exists
            self.assertTrue(os.path.exists(temp_path))
            self.assertTrue(os.path.isfile(temp_path))
            
            # Verify the file has the correct suffix
            self.assertTrue(temp_path.endswith('.txt'))
            
            # Write some data to the file
            with open(temp_path, 'w') as f:
                f.write('test data')
            
            # Verify the data was written
            with open(temp_path, 'r') as f:
                self.assertEqual(f.read(), 'test data')
        
        # Verify the file is deleted after the context is exited
        self.assertFalse(os.path.exists(temp_path))
    
    def test_secure_temp_file_with_prefix(self):
        """Test that secure_temp_file creates a file with the specified prefix."""
        prefix = 'test_prefix_'
        with secure_temp_file(prefix=prefix) as temp_path:
            # Verify the file exists
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify the file has the correct prefix
            self.assertTrue(os.path.basename(temp_path).startswith(prefix))
        
        # Verify the file is deleted after the context is exited
        self.assertFalse(os.path.exists(temp_path))
    
    def test_secure_temp_file_with_dir(self):
        """Test that secure_temp_file creates a file in the specified directory."""
        # Create a temporary directory for the test
        test_dir = os.path.join(os.path.dirname(__file__), 'temp_test_dir')
        os.makedirs(test_dir, exist_ok=True)
        
        try:
            with secure_temp_file(dir=test_dir) as temp_path:
                # Verify the file exists
                self.assertTrue(os.path.exists(temp_path))
                
                # Verify the file is in the specified directory
                self.assertEqual(os.path.dirname(temp_path), test_dir)
            
            # Verify the file is deleted after the context is exited
            self.assertFalse(os.path.exists(temp_path))
        finally:
            # Clean up the temporary directory
            if os.path.exists(test_dir):
                import shutil
                shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main()