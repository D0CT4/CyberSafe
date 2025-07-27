import unittest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chat_engine import ChatEngine, ChatMessage, OpenAIProvider, GPT4AllProvider
from core.summarizer import LogSummarizer
from core.watcher import FileWatcher, SmartLogHandler

class TestChatEngine(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.mode = "gpt4all"
        self.config.gpt4all_model_path = "./models/test_model.gguf"
        self.chat_engine = ChatEngine(self.config)

    @patch('core.chat_engine.GPT4All')
    async def test_chat_generation(self, mock_gpt4all):
        # Setup mock response
        mock_gpt4all.return_value.generate.return_value = "Test response"
        
        # Test chat generation
        response = await self.chat_engine.chat("Test prompt")
        self.assertEqual(response, "Test response")

    def test_provider_switching(self):
        # Test switching from GPT4All to OpenAI
        self.chat_engine.switch_provider("openai", openai_api_key="test_key")
        self.assertIsInstance(self.chat_engine.provider, OpenAIProvider)
        
        # Test switching back to GPT4All
        self.chat_engine.switch_provider("gpt4all")
        self.assertIsInstance(self.chat_engine.provider, GPT4AllProvider)

class TestSummarizer(unittest.TestCase):
    def setUp(self):
        self.chat_engine = MagicMock()
        self.summarizer = LogSummarizer(self.chat_engine)

    def test_extract_key_events(self):
        # Test JSON log processing
        json_log = {
            "content": {
                "events": ["event1", "event2"],
                "messages": [{"text": "message1"}, {"text": "message2"}]
            }
        }
        events = self.summarizer._extract_key_events(json_log)
        self.assertEqual(len(events), 4)

        # Test text log processing
        text_log = {
            "content": "error: test error\nwarning: test warning"
        }
        events = self.summarizer._extract_key_events(text_log)
        self.assertEqual(len(events), 2)

    def test_count_errors(self):
        log_data = {"content": "error: test\nexception occurred\nerror found"}
        error_count = self.summarizer._count_errors(log_data)
        self.assertEqual(error_count, 3)

class TestFileWatcher(unittest.TestCase):
    def setUp(self):
        self.callback = MagicMock()
        self.watcher = FileWatcher("./test_logs", self.callback)
        self.handler = SmartLogHandler(self.callback)

    @patch('core.watcher.Path')
    def test_file_processing(self, mock_path):
        # Mock file event
        event = MagicMock()
        event.is_directory = False
        event.src_path = "./test_logs/test.json"
        
        # Mock Path operations
        mock_path.return_value.suffix = ".json"
        mock_path.return_value.stat.return_value.st_size = 1000
        
        # Test handler
        self.handler.on_modified(event)
        self.callback.assert_called_once()

    def test_file_filtering(self):
        # Test file extension filtering
        valid_file = MagicMock()
        valid_file.suffix = ".json"
        valid_file.stat.return_value.st_size = 1000
        
        invalid_file = MagicMock()
        invalid_file.suffix = ".exe"
        
        self.assertTrue(self.handler._should_process(valid_file))
        self.assertFalse(self.handler._should_process(invalid_file))

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        from api.server import create_app
        self.app = create_app({"testing": True})
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_dashboard_data(self):
        response = self.client.get('/api/dashboard-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        required_fields = ['dates', 'events', 'errors', 'totalEvents']
        for field in required_fields:
            self.assertIn(field, data)

    @patch('api.routes.ChatEngine')
    def test_chat_endpoint(self, mock_chat_engine):
        # Mock chat response
        mock_chat_engine.chat.return_value = "Test response"
        
        # Test chat endpoint
        response = self.client.post('/chat', 
                                  json={"prompt": "test"},
                                  headers={"X-API-Key": "test_key"})
        self.assertEqual(response.status_code, 200)

class TestSecurity(unittest.TestCase):
    def setUp(self):
        from api.server import create_app
        self.app = create_app({"api_key_hash": "test_hash"})
        self.client = self.app.test_client()

    def test_api_key_validation(self):
        # Test missing API key
        response = self.client.get('/status')
        self.assertEqual(response.status_code, 401)

        # Test invalid API key
        response = self.client.get('/status', 
                                 headers={"X-API-Key": "invalid_key"})
        self.assertEqual(response.status_code, 401)

    def test_rate_limiting(self):
        # Test rate limiting
        for _ in range(11):  # Exceed rate limit (10 per minute)
            self.client.post('/chat',
                           json={"prompt": "test"},
                           headers={"X-API-Key": "test_key"})
        
        response = self.client.post('/chat',
                                  json={"prompt": "test"},
                                  headers={"X-API-Key": "test_key"})
        self.assertEqual(response.status_code, 429)  # Too Many Requests

def run_tests():
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests()
