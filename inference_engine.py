"""
Inference engine for the trained CTF AI model.
Handles question answering and response generation.
"""

import torch
import logging
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
from typing import List, Dict, Optional, Tuple
import re
import json

from config import Config

logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.qa_pipeline = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.max_length = 512
        self.context_window = 1000  # Characters for context window
        
        # CTF-specific response templates
        self.response_templates = {
            'tool_usage': "To use {tool}, you typically need to {action}. Here's how: {explanation}",
            'vulnerability': "This vulnerability involves {type}. The exploitation process: {steps}",
            'technique': "The {technique} technique works by {mechanism}. Implementation: {details}",
            'flag_finding': "To find the flag, you should {approach}. Look for: {indicators}",
            'general': "{answer}"
        }
    
    def load_model(self, model, tokenizer):
        """Load model and tokenizer instances."""
        self.model = model
        self.tokenizer = tokenizer
        self.model.to(self.device)
        
        # Initialize QA pipeline
        self.qa_pipeline = pipeline(
            "question-answering",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device.type == 'cuda' else -1
        )
        
        logger.info("Model loaded into inference engine")
        return True
    
    def load_saved_model(self, model_path: str) -> bool:
        """Load a saved model from disk."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForQuestionAnswering.from_pretrained(model_path)
            self.model.to(self.device)
            
            # Initialize QA pipeline
            self.qa_pipeline = pipeline(
                "question-answering",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device.type == 'cuda' else -1
            )
            
            logger.info(f"Model loaded from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {str(e)}")
            return False
    
    def preprocess_question(self, question: str) -> str:
        """Preprocess user question for better understanding."""
        # Normalize common CTF terminology
        replacements = {
            'pwning': 'pwn',
            'exploitation': 'exploit',
            'vulnerability': 'vuln',
            'reverse engineering': 'reverse',
            'cryptography': 'crypto'
        }
        
        processed_question = question.lower()
        for old, new in replacements.items():
            processed_question = processed_question.replace(old, new)
        
        # Add context cues for better categorization
        if any(word in processed_question for word in ['web', 'http', 'xss', 'sql']):
            processed_question = f"[web] {processed_question}"
        elif any(word in processed_question for word in ['crypto', 'cipher', 'encrypt']):
            processed_question = f"[crypto] {processed_question}"
        elif any(word in processed_question for word in ['pwn', 'buffer', 'overflow']):
            processed_question = f"[pwn] {processed_question}"
        elif any(word in processed_question for word in ['reverse', 'assembly', 'binary']):
            processed_question = f"[reverse] {processed_question}"
        elif any(word in processed_question for word in ['forensics', 'steganography']):
            processed_question = f"[forensics] {processed_question}"
        
        return processed_question
    
    def generate_context(self, question: str) -> str:
        """Generate relevant context for the question."""
        # This is a simplified context generation
        # In a more advanced system, this could use vector similarity search
        # across the knowledge base
        
        question_lower = question.lower()
        context_parts = []
        
        # Add general CTF knowledge based on question type
        if 'flag' in question_lower:
            context_parts.append(
                "CTF flags are typically in the format team{flag_content} or CTF{flag_content}. "
                "They are often hidden in files, databases, or can be obtained through exploitation."
            )
        
        if any(word in question_lower for word in ['exploit', 'vulnerability']):
            context_parts.append(
                "Exploitation involves identifying vulnerabilities and leveraging them to gain "
                "unauthorized access or extract information. Common techniques include buffer overflows, "
                "injection attacks, and privilege escalation."
            )
        
        if any(word in question_lower for word in ['tool', 'use']):
            context_parts.append(
                "CTF tools help automate various tasks including reconnaissance, exploitation, "
                "forensics, and reverse engineering. Popular tools include Burp Suite, Metasploit, "
                "Wireshark, IDA Pro, and custom scripts."
            )
        
        # Add technique-specific context
        if 'buffer overflow' in question_lower:
            context_parts.append(
                "Buffer overflow occurs when data exceeds buffer boundaries, potentially overwriting "
                "adjacent memory. This can be exploited to execute arbitrary code or crash programs."
            )
        
        if 'sql injection' in question_lower:
            context_parts.append(
                "SQL injection exploits vulnerabilities in database queries by inserting malicious SQL code. "
                "This can lead to data extraction, authentication bypass, or database manipulation."
            )
        
        if 'xss' in question_lower:
            context_parts.append(
                "Cross-Site Scripting (XSS) allows attackers to inject malicious scripts into web pages "
                "viewed by other users. This can steal cookies, session tokens, or perform actions on behalf of users."
            )
        
        return ' '.join(context_parts) if context_parts else self.get_default_context()
    
    def get_default_context(self) -> str:
        """Get default CTF context when no specific context is available."""
        return (
            "Capture The Flag (CTF) competitions test cybersecurity skills across various domains "
            "including web security, cryptography, binary exploitation, reverse engineering, and forensics. "
            "Participants solve challenges to find hidden flags, typically formatted as team{flag_content}. "
            "Common tools include Burp Suite, Metasploit, Wireshark, IDA Pro, and scripting languages. "
            "Techniques involve vulnerability identification, exploitation, code analysis, and problem-solving."
        )
    
    def answer_question(self, question: str, context: str = None) -> Dict:
        """Answer a question using the trained model."""
        if not self.qa_pipeline:
            raise ValueError("No model loaded for inference")
        
        # Preprocess question
        processed_question = self.preprocess_question(question)
        
        # Generate or use provided context
        if context is None:
            context = self.generate_context(question)
        
        # Truncate context if too long
        if len(context) > self.context_window:
            context = context[:self.context_window] + "..."
        
        try:
            # Get answer from model
            result = self.qa_pipeline(
                question=processed_question,
                context=context,
                max_answer_len=200,
                handle_impossible_answer=True
            )
            
            # Post-process the answer
            processed_answer = self.postprocess_answer(result['answer'], question)
            
            return {
                'answer': processed_answer,
                'confidence': result['score'],
                'original_answer': result['answer'],
                'context_used': context[:200] + "..." if len(context) > 200 else context,
                'question_processed': processed_question
            }
            
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            return {
                'answer': "I'm sorry, I couldn't process your question. Please try rephrasing it.",
                'confidence': 0.0,
                'error': str(e)
            }
    
    def postprocess_answer(self, raw_answer: str, original_question: str) -> str:
        """Post-process the raw model answer for better presentation."""
        if not raw_answer or len(raw_answer.strip()) < 3:
            return "I don't have enough information to answer that question accurately."
        
        # Clean up the answer
        answer = raw_answer.strip()
        
        # Remove redundant phrases
        redundant_phrases = [
            "The answer is",
            "Based on the context",
            "According to the information",
            "As mentioned"
        ]
        
        for phrase in redundant_phrases:
            if answer.lower().startswith(phrase.lower()):
                answer = answer[len(phrase):].strip()
                if answer.startswith(':'):
                    answer = answer[1:].strip()
        
        # Ensure proper capitalization
        if answer and not answer[0].isupper():
            answer = answer[0].upper() + answer[1:]
        
        # Add period if missing
        if answer and not answer.endswith(('.', '!', '?')):
            answer += '.'
        
        # Add context-specific formatting
        question_lower = original_question.lower()
        
        if 'how to' in question_lower and not answer.lower().startswith(('first', 'start', 'begin', 'step', '1.')):
            answer = f"To accomplish this: {answer}"
        
        if 'what is' in question_lower and not answer.lower().startswith(('it is', 'this is', 'that is')):
            answer = f"This is {answer.lower()}"
        
        return answer
    
    def generate_response(self, user_message: str) -> str:
        """Generate a complete response to user message."""
        # Handle greetings and general conversation
        if self.is_greeting(user_message):
            return self.get_greeting_response()
        
        if self.is_farewell(user_message):
            return "Goodbye! Feel free to ask if you have more CTF questions."
        
        # Process as a question
        result = self.answer_question(user_message)
        
        # Format response based on confidence
        if result['confidence'] > 0.7:
            response = result['answer']
        elif result['confidence'] > 0.3:
            response = f"{result['answer']}\n\nNote: I'm not entirely certain about this answer. Please verify with additional sources."
        else:
            response = (
                "I'm not confident about answering this question accurately. "
                "Could you provide more context or rephrase your question? "
                "You might also want to check specific CTF resources or documentation."
            )
        
        return response
    
    def is_greeting(self, message: str) -> bool:
        """Check if message is a greeting."""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in message.lower() for greeting in greetings)
    
    def is_farewell(self, message: str) -> bool:
        """Check if message is a farewell."""
        farewells = ['bye', 'goodbye', 'see you', 'farewell', 'exit', 'quit']
        return any(farewell in message.lower() for farewell in farewells)
    
    def get_greeting_response(self) -> str:
        """Get a greeting response."""
        return (
            "Hello! I'm a CTF AI assistant trained on cybersecurity writeups. "
            "I can help you with questions about CTF challenges, security techniques, "
            "tools, and exploitation methods. What would you like to know?"
        )
    
    def batch_answer(self, questions: List[str], context: str = None) -> List[Dict]:
        """Answer multiple questions in batch."""
        results = []
        
        for question in questions:
            try:
                result = self.answer_question(question, context)
                results.append(result)
            except Exception as e:
                results.append({
                    'answer': f"Error processing question: {str(e)}",
                    'confidence': 0.0,
                    'error': str(e)
                })
        
        return results
    
    def get_similar_questions(self, question: str, num_suggestions: int = 3) -> List[str]:
        """Generate similar questions that the model might answer better."""
        question_lower = question.lower()
        suggestions = []
        
        # Generate variations based on question type
        if 'how' in question_lower:
            base = question_lower.replace('how to', '').replace('how', '').strip()
            suggestions.extend([
                f"What is the process for {base}?",
                f"Can you explain {base}?",
                f"What are the steps to {base}?"
            ])
        
        elif 'what' in question_lower:
            base = question_lower.replace('what is', '').replace('what', '').strip()
            suggestions.extend([
                f"How does {base} work?",
                f"Explain {base}",
                f"How to use {base}?"
            ])
        
        # Add generic CTF suggestions
        if 'flag' in question_lower:
            suggestions.extend([
                "How to find flags in CTF challenges?",
                "Where are flags typically hidden?",
                "What tools help find flags?"
            ])
        
        return suggestions[:num_suggestions]
    
    def is_model_ready(self) -> bool:
        """Check if model is ready for inference."""
        return self.model is not None and self.tokenizer is not None and self.qa_pipeline is not None
    
    def get_model_status(self) -> Dict:
        """Get current model status."""
        return {
            'model_loaded': self.is_model_ready(),
            'device': str(self.device),
            'model_name': getattr(self.model, 'name_or_path', 'Unknown') if self.model else None,
            'vocab_size': len(self.tokenizer) if self.tokenizer else 0
        }
