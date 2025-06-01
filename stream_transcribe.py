#!/usr/bin/env python
"""
AutoMeetAI - Real-time Streaming Transcription

This script demonstrates how to use the AutoMeetAI application for real-time
transcription of audio from a microphone.

Usage:
    python stream_transcribe.py [options]

Examples:
    python stream_transcribe.py --duration 60
    python stream_transcribe.py --language en
    python stream_transcribe.py --assemblyai-key YOUR_API_KEY
"""

import argparse
import os
import sys
import time
import signal
from typing import Dict, Any

from src.services.assemblyai_streaming_transcription_service import AssemblyAIStreamingTranscriptionService
from src.config.env_config_provider import EnvConfigProvider
from src.utils.logging import get_logger, configure_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Configure the root logger
configure_logger()

# Global variables
streaming_service = None
is_running = True


def signal_handler(sig, frame):
    """
    Handle Ctrl+C to gracefully stop streaming.
    """
    global is_running
    logger.info("Stopping streaming...")
    is_running = False


def process_transcription_result(result: Dict[str, Any]) -> None:
    """
    Process and display a transcription result.
    
    Args:
        result: The transcription result to process
    """
    # Clear the line and print the result
    if result.get("text"):
        # Print in different colors based on whether it's final or not
        if result.get("is_final"):
            # Green for final results
            print(f"\033[92m{result.get('text')}\033[0m")
        else:
            # Yellow for interim results, overwrite the line
            print(f"\033[93m{result.get('text')}\033[0m", end="\r")


def main():
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AutoMeetAI - Real-time Streaming Transcription")
    
    # API key
    parser.add_argument("--assemblyai-key", help="AssemblyAI API key (overrides environment variable)")
    
    # Streaming options
    parser.add_argument("--duration", type=int, help="Duration in seconds to record (default: unlimited)")
    parser.add_argument("--language", default="pt", help="Language code (default: pt)")
    parser.add_argument("--speaker-labels", action="store_true", help="Enable speaker diarization")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create configuration provider
    config_provider = EnvConfigProvider()
    
    # Set API key if provided
    if args.assemblyai_key:
        config_provider.set("assemblyai_api_key", args.assemblyai_key)
    
    try:
        # Create streaming service
        global streaming_service
        streaming_service = AssemblyAIStreamingTranscriptionService(config_provider=config_provider)
        
        # Prepare configuration
        config = {
            "language_code": args.language,
            "speaker_labels": args.speaker_labels
        }
        
        # Print instructions
        print("\n=== AutoMeetAI Real-time Streaming Transcription ===")
        print("Speak into your microphone to see real-time transcription.")
        print("Press Ctrl+C to stop recording.\n")
        
        # Start streaming from microphone
        if args.duration:
            print(f"Recording for {args.duration} seconds...")
            result = streaming_service.stream_microphone(
                callback=process_transcription_result,
                duration=args.duration,
                config=config
            )
            
            if result:
                print("\n=== Final Transcription ===")
                print(result.to_formatted_text())
        else:
            print("Recording until stopped (Ctrl+C to stop)...")
            streaming_service.stream_microphone(
                callback=process_transcription_result,
                config=config
            )
            
            # Keep the main thread running until Ctrl+C
            while is_running:
                time.sleep(0.1)
            
            # Stop streaming and get final result
            result = streaming_service.stop_streaming()
            
            if result:
                print("\n=== Final Transcription ===")
                print(result.to_formatted_text())
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
    
    finally:
        # Ensure streaming is stopped
        if streaming_service and streaming_service.is_streaming():
            streaming_service.stop_streaming()


if __name__ == "__main__":
    main()