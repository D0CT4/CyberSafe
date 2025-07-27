import pytest
from pathlib import Path
import tempfile
import json
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chat_engine import ChatEngine, ChatMessage
from core.summarizer import LogSummarizer
from core.watcher import FileWatcher

@pytest.fixture
def temp_log_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def sample_log_file(temp_log_dir):
    log_content = {
        "timestamp": datetime.now().isoformat(),
        "level": "ERROR",
        "message": "Test error message",
        "details": {"source": "test_integration"}
    }
    
    log_file = Path(temp_log_dir) / "test.log.json"
    with open(log_file, 'w') as f:
        json.dump(log_content, f)
    
    return log_file

@pytest.fixture
def chat_engine():
    config = {
        "mode": "gpt4all",
        "model_path": "./models/test_model.gguf"
    }
    return ChatEngine(config)

@pytest.fixture
def summarizer(chat_engine):
    return LogSummarizer(chat_engine)

@pytest.mark.asyncio
async def test_full_processing_pipeline(temp_log_dir, sample_log_file, chat_engine, summarizer):
    """Test the complete flow from file detection to summary generation"""
    
    # Setup file watcher
    processed_files = []
    def callback(data):
        processed_files.append(data)
    
    watcher = FileWatcher(temp_log_dir, callback)
    
    try:
        # Start watching
        watcher.start()
        
        # Write new log entry
        new_log = {
            "timestamp": datetime.now().isoformat(),
            "level": "WARNING",
            "message": "Test warning message",
            "details": {"source": "test_integration"}
        }
        
        new_log_file = Path(temp_log_dir) / "new_test.log.json"
        with open(new_log_file, 'w') as f:
            json.dump(new_log, f)
        
        # Give some time for processing
        await asyncio.sleep(2)
        
        # Verify file was processed
        assert len(processed_files) > 0
        
        # Process with summarizer
        summary = await summarizer.process_log_data(processed_files[0])
        
        # Verify summary
        assert summary.error_count == 0
        assert summary.warning_count == 1
        assert len(summary.key_events) > 0
        
    finally:
        watcher.stop()

@pytest.mark.asyncio
async def test_ai_provider_switching(chat_engine):
    """Test switching between AI providers"""
    
    # Test initial GPT4All provider
    assert chat_engine.config.mode == "gpt4all"
    
    # Test chat functionality
    response = await chat_engine.chat("Test prompt")
    assert response is not None
    
    # Switch to OpenAI
    chat_engine.switch_provider("openai", openai_api_key="test_key")
    assert chat_engine.config.mode == "openai"
    
    # Test chat after switching
    response = await chat_engine.chat("Test prompt")
    assert response is not None

def test_file_monitoring(temp_log_dir):
    """Test file monitoring system"""
    
    # Setup
    events_detected = []
    def callback(data):
        events_detected.append(data)
    
    watcher = FileWatcher(temp_log_dir, callback)
    
    try:
        # Start monitoring
        watcher.start()
        assert watcher.is_running()
        
        # Create test files
        files_to_create = [
            ("test1.log", "Test log content 1"),
            ("test2.json", '{"message": "Test log 2"}'),
            ("test3.txt", "Test log content 3"),
            ("ignored.exe", "Should be ignored")
        ]
        
        for filename, content in files_to_create:
            file_path = Path(temp_log_dir) / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Wait for processing
        time.sleep(2)
        
        # Verify only valid files were processed
        valid_extensions = ['.log', '.json', '.txt']
        processed_count = len([e for e in events_detected 
                             if Path(e['file_path']).suffix in valid_extensions])
        assert processed_count == 3
        
    finally:
        watcher.stop()
        assert not watcher.is_running()

@pytest.mark.asyncio
async def test_error_handling(temp_log_dir, chat_engine):
    """Test error handling in various components"""
    
    # Test invalid file handling
    invalid_log = Path(temp_log_dir) / "invalid.json"
    with open(invalid_log, 'w') as f:
        f.write("Invalid JSON content")
    
    summarizer = LogSummarizer(chat_engine)
    
    # Should handle invalid JSON gracefully
    summary = await summarizer.process_log_data({"file_path": str(invalid_log)})
    assert summary is not None
    
    # Test AI provider errors
    chat_engine.config.mode = "invalid_mode"
    with pytest.raises(ValueError):
        chat_engine._create_provider()

def test_performance(temp_log_dir):
    """Test system performance with larger datasets"""
    
    # Generate multiple log files
    for i in range(100):
        log_content = {
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "level": "INFO",
            "message": f"Test message {i}",
            "details": {"iteration": i}
        }
        
        log_file = Path(temp_log_dir) / f"test_{i}.log.json"
        with open(log_file, 'w') as f:
            json.dump(log_content, f)
    
    # Test file watcher performance
    processed_count = 0
    def callback(data):
        nonlocal processed_count
        processed_count += 1
    
    watcher = FileWatcher(temp_log_dir, callback)
    
    try:
        start_time = datetime.now()
        watcher.start()
        
        # Wait for processing
        while processed_count < 100 and (datetime.now() - start_time).seconds < 10:
            time.sleep(0.1)
        
        # Verify processing speed
        assert processed_count == 100
        
    finally:
        watcher.stop()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
