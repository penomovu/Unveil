"""
Model evaluation module for cybersecurity-specific metrics.
Evaluates model performance on CTF question-answering tasks.
"""

import json
import logging
import numpy as np
from typing import List, Dict, Tuple
import torch
from transformers import pipeline
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import re
from collections import Counter, defaultdict

from config import Config

logger = logging.getLogger(__name__)

class ModelEvaluator:
    def __init__(self):
        self.evaluation_questions = self.load_evaluation_questions()
        self.ctf_categories = ['web', 'crypto', 'pwn', 'reverse', 'forensics', 'misc']
        
    def load_evaluation_questions(self) -> List[Dict]:
        """Load predefined evaluation questions for cybersecurity tasks."""
        # These are curated questions covering different CTF domains
        questions = [
            # Web Security
            {
                'question': 'How do you exploit SQL injection vulnerabilities?',
                'category': 'web',
                'expected_keywords': ['injection', 'query', 'database', 'payload', 'union'],
                'context': 'SQL injection is a web security vulnerability that allows attackers to interfere with queries.'
            },
            {
                'question': 'What is Cross-Site Scripting (XSS)?',
                'category': 'web',
                'expected_keywords': ['script', 'javascript', 'browser', 'payload', 'cookie'],
                'context': 'XSS vulnerabilities occur when web applications include untrusted data in web pages.'
            },
            {
                'question': 'How to find hidden directories in web applications?',
                'category': 'web',
                'expected_keywords': ['directory', 'enumeration', 'brute', 'force', 'wordlist'],
                'context': 'Directory enumeration helps discover hidden paths and files in web applications.'
            },
            
            # Cryptography
            {
                'question': 'How do you decrypt RSA encrypted messages?',
                'category': 'crypto',
                'expected_keywords': ['rsa', 'private', 'key', 'factorization', 'decrypt'],
                'context': 'RSA is an asymmetric cryptographic algorithm used for secure communication.'
            },
            {
                'question': 'What are common techniques to break weak ciphers?',
                'category': 'crypto',
                'expected_keywords': ['frequency', 'analysis', 'substitution', 'brute', 'force'],
                'context': 'Weak ciphers can be broken using various cryptanalysis techniques.'
            },
            
            # Binary Exploitation
            {
                'question': 'How does buffer overflow exploitation work?',
                'category': 'pwn',
                'expected_keywords': ['buffer', 'overflow', 'stack', 'return', 'address'],
                'context': 'Buffer overflow vulnerabilities occur when programs write data beyond buffer boundaries.'
            },
            {
                'question': 'What is Return-Oriented Programming (ROP)?',
                'category': 'pwn',
                'expected_keywords': ['rop', 'gadgets', 'return', 'chain', 'exploit'],
                'context': 'ROP is an exploitation technique that chains together code gadgets.'
            },
            
            # Reverse Engineering
            {
                'question': 'How to analyze binary files for vulnerabilities?',
                'category': 'reverse',
                'expected_keywords': ['disassembly', 'static', 'analysis', 'ida', 'ghidra'],
                'context': 'Binary analysis involves examining compiled programs to understand their behavior.'
            },
            {
                'question': 'What tools are used for dynamic analysis?',
                'category': 'reverse',
                'expected_keywords': ['debugger', 'gdb', 'dynamic', 'runtime', 'analysis'],
                'context': 'Dynamic analysis examines program behavior during execution.'
            },
            
            # Forensics
            {
                'question': 'How to extract data from memory dumps?',
                'category': 'forensics',
                'expected_keywords': ['memory', 'dump', 'volatility', 'process', 'extract'],
                'context': 'Memory forensics involves analyzing RAM dumps to extract information.'
            },
            {
                'question': 'What is steganography and how to detect it?',
                'category': 'forensics',
                'expected_keywords': ['steganography', 'hidden', 'data', 'image', 'detect'],
                'context': 'Steganography hides information within other non-secret data or media.'
            },
            
            # General/Misc
            {
                'question': 'How to find flags in CTF challenges?',
                'category': 'misc',
                'expected_keywords': ['flag', 'format', 'search', 'strings', 'grep'],
                'context': 'CTF flags are typically formatted strings that need to be discovered and submitted.'
            }
        ]
        
        return questions
    
    def evaluate_model(self, model, tokenizer) -> Dict:
        """Comprehensive evaluation of the model."""
        logger.info("Starting model evaluation...")
        
        # Initialize QA pipeline
        qa_pipeline = pipeline(
            "question-answering",
            model=model,
            tokenizer=tokenizer,
            device=-1  # Use CPU for evaluation
        )
        
        results = {
            'overall_performance': {},
            'category_performance': {},
            'detailed_results': [],
            'keyword_coverage': {},
            'response_quality': {}
        }
        
        # Evaluate on predefined questions
        category_scores = defaultdict(list)
        all_scores = []
        keyword_matches = defaultdict(list)
        
        for i, question_data in enumerate(self.evaluation_questions):
            try:
                # Get model answer
                answer_result = qa_pipeline(
                    question=question_data['question'],
                    context=question_data['context'],
                    max_answer_len=200
                )
                
                # Evaluate the answer
                score = self.evaluate_answer(
                    answer_result['answer'],
                    question_data['expected_keywords'],
                    question_data['category']
                )
                
                # Store results
                category_scores[question_data['category']].append(score)
                all_scores.append(score)
                
                # Check keyword coverage
                keyword_coverage = self.check_keyword_coverage(
                    answer_result['answer'],
                    question_data['expected_keywords']
                )
                keyword_matches[question_data['category']].append(keyword_coverage)
                
                # Store detailed result
                results['detailed_results'].append({
                    'question': question_data['question'],
                    'category': question_data['category'],
                    'answer': answer_result['answer'],
                    'confidence': answer_result['score'],
                    'evaluation_score': score,
                    'keyword_coverage': keyword_coverage,
                    'expected_keywords': question_data['expected_keywords']
                })
                
                logger.info(f"Evaluated question {i+1}/{len(self.evaluation_questions)}")
                
            except Exception as e:
                logger.error(f"Error evaluating question {i}: {str(e)}")
                all_scores.append(0.0)
                category_scores[question_data['category']].append(0.0)
        
        # Calculate overall performance
        results['overall_performance'] = {
            'average_score': np.mean(all_scores) if all_scores else 0.0,
            'median_score': np.median(all_scores) if all_scores else 0.0,
            'std_score': np.std(all_scores) if all_scores else 0.0,
            'min_score': np.min(all_scores) if all_scores else 0.0,
            'max_score': np.max(all_scores) if all_scores else 0.0,
            'total_questions': len(self.evaluation_questions)
        }
        
        # Calculate category performance
        for category in self.ctf_categories:
            if category in category_scores:
                scores = category_scores[category]
                keyword_coverage = keyword_matches[category]
                
                results['category_performance'][category] = {
                    'average_score': np.mean(scores),
                    'question_count': len(scores),
                    'keyword_coverage': np.mean(keyword_coverage) if keyword_coverage else 0.0,
                    'strength_level': self.categorize_performance(np.mean(scores))
                }
        
        # Evaluate response quality metrics
        results['response_quality'] = self.evaluate_response_quality(results['detailed_results'])
        
        # Overall keyword coverage
        all_keyword_coverage = [item for sublist in keyword_matches.values() for item in sublist]
        results['keyword_coverage'] = {
            'overall_coverage': np.mean(all_keyword_coverage) if all_keyword_coverage else 0.0,
            'category_breakdown': {
                cat: np.mean(matches) if matches else 0.0 
                for cat, matches in keyword_matches.items()
            }
        }
        
        logger.info("Model evaluation completed")
        return results
    
    def evaluate_answer(self, answer: str, expected_keywords: List[str], category: str) -> float:
        """Evaluate a single answer based on expected keywords and relevance."""
        if not answer or len(answer.strip()) < 3:
            return 0.0
        
        answer_lower = answer.lower()
        score = 0.0
        
        # Keyword matching (40% of score)
        keyword_score = self.check_keyword_coverage(answer, expected_keywords)
        score += keyword_score * 0.4
        
        # Length appropriateness (20% of score)
        length_score = self.evaluate_answer_length(answer)
        score += length_score * 0.2
        
        # Category relevance (20% of score)
        relevance_score = self.evaluate_category_relevance(answer, category)
        score += relevance_score * 0.2
        
        # Technical accuracy indicators (20% of score)
        technical_score = self.evaluate_technical_accuracy(answer, category)
        score += technical_score * 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def check_keyword_coverage(self, answer: str, expected_keywords: List[str]) -> float:
        """Check how many expected keywords are covered in the answer."""
        if not expected_keywords:
            return 1.0
        
        answer_lower = answer.lower()
        matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
        return matches / len(expected_keywords)
    
    def evaluate_answer_length(self, answer: str) -> float:
        """Evaluate if answer length is appropriate."""
        word_count = len(answer.split())
        
        if word_count < 5:
            return 0.2  # Too short
        elif word_count < 15:
            return 0.6  # Short but acceptable
        elif word_count < 50:
            return 1.0  # Good length
        elif word_count < 100:
            return 0.8  # Bit long but ok
        else:
            return 0.4  # Too long
    
    def evaluate_category_relevance(self, answer: str, category: str) -> float:
        """Evaluate if answer is relevant to the CTF category."""
        answer_lower = answer.lower()
        
        category_keywords = {
            'web': ['web', 'http', 'browser', 'server', 'application', 'request', 'response'],
            'crypto': ['crypto', 'encryption', 'cipher', 'key', 'algorithm', 'hash'],
            'pwn': ['binary', 'exploit', 'buffer', 'memory', 'stack', 'heap', 'shellcode'],
            'reverse': ['reverse', 'disassemble', 'analysis', 'binary', 'code', 'assembly'],
            'forensics': ['forensics', 'analysis', 'file', 'data', 'evidence', 'extract'],
            'misc': ['programming', 'script', 'tool', 'technique', 'method']
        }
        
        relevant_keywords = category_keywords.get(category, [])
        if not relevant_keywords:
            return 0.5  # Neutral for unknown categories
        
        matches = sum(1 for keyword in relevant_keywords if keyword in answer_lower)
        return min(matches / len(relevant_keywords), 1.0)
    
    def evaluate_technical_accuracy(self, answer: str, category: str) -> float:
        """Evaluate technical accuracy indicators."""
        answer_lower = answer.lower()
        score = 0.5  # Base score
        
        # Positive indicators
        positive_indicators = [
            'step', 'process', 'method', 'technique', 'tool', 'command',
            'vulnerability', 'exploit', 'attack', 'defense', 'security'
        ]
        
        # Negative indicators
        negative_indicators = [
            'unknown', 'unclear', 'maybe', 'possibly', 'might be',
            'not sure', 'don\'t know', 'uncertain'
        ]
        
        # Check positive indicators
        positive_count = sum(1 for indicator in positive_indicators if indicator in answer_lower)
        score += min(positive_count * 0.1, 0.3)
        
        # Check negative indicators
        negative_count = sum(1 for indicator in negative_indicators if indicator in answer_lower)
        score -= negative_count * 0.2
        
        return max(0.0, min(score, 1.0))
    
    def evaluate_response_quality(self, detailed_results: List[Dict]) -> Dict:
        """Evaluate overall response quality metrics."""
        if not detailed_results:
            return {}
        
        # Calculate various quality metrics
        confidence_scores = [r['confidence'] for r in detailed_results]
        answer_lengths = [len(r['answer'].split()) for r in detailed_results]
        
        # Response completeness
        complete_responses = sum(1 for r in detailed_results if len(r['answer'].split()) >= 10)
        completeness_rate = complete_responses / len(detailed_results)
        
        # High confidence responses
        high_confidence = sum(1 for score in confidence_scores if score > 0.7)
        high_confidence_rate = high_confidence / len(confidence_scores)
        
        # Technical term usage
        technical_terms = [
            'vulnerability', 'exploit', 'attack', 'payload', 'injection',
            'overflow', 'encryption', 'analysis', 'technique', 'tool'
        ]
        
        responses_with_tech_terms = 0
        for result in detailed_results:
            answer_lower = result['answer'].lower()
            if any(term in answer_lower for term in technical_terms):
                responses_with_tech_terms += 1
        
        technical_usage_rate = responses_with_tech_terms / len(detailed_results)
        
        return {
            'completeness_rate': completeness_rate,
            'high_confidence_rate': high_confidence_rate,
            'technical_usage_rate': technical_usage_rate,
            'average_confidence': np.mean(confidence_scores),
            'average_response_length': np.mean(answer_lengths),
            'response_length_std': np.std(answer_lengths)
        }
    
    def categorize_performance(self, score: float) -> str:
        """Categorize performance level based on score."""
        if score >= 0.8:
            return 'Excellent'
        elif score >= 0.6:
            return 'Good'
        elif score >= 0.4:
            return 'Fair'
        elif score >= 0.2:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def generate_evaluation_report(self, results: Dict) -> str:
        """Generate a human-readable evaluation report."""
        report = []
        report.append("CTF AI Model Evaluation Report")
        report.append("=" * 40)
        report.append("")
        
        # Overall performance
        overall = results['overall_performance']
        report.append(f"Overall Performance:")
        report.append(f"  Average Score: {overall['average_score']:.3f}")
        report.append(f"  Performance Level: {self.categorize_performance(overall['average_score'])}")
        report.append(f"  Questions Evaluated: {overall['total_questions']}")
        report.append("")
        
        # Category breakdown
        report.append("Category Performance:")
        for category, perf in results['category_performance'].items():
            report.append(f"  {category.upper()}:")
            report.append(f"    Score: {perf['average_score']:.3f} ({perf['strength_level']})")
            report.append(f"    Keyword Coverage: {perf['keyword_coverage']:.3f}")
            report.append(f"    Questions: {perf['question_count']}")
        report.append("")
        
        # Response quality
        quality = results['response_quality']
        report.append("Response Quality Metrics:")
        report.append(f"  Completeness Rate: {quality['completeness_rate']:.3f}")
        report.append(f"  High Confidence Rate: {quality['high_confidence_rate']:.3f}")
        report.append(f"  Technical Usage Rate: {quality['technical_usage_rate']:.3f}")
        report.append(f"  Average Response Length: {quality['average_response_length']:.1f} words")
        report.append("")
        
        # Recommendations
        report.append("Recommendations:")
        if overall['average_score'] < 0.5:
            report.append("  - Model needs significant improvement")
            report.append("  - Consider collecting more training data")
            report.append("  - Review preprocessing and training procedures")
        elif overall['average_score'] < 0.7:
            report.append("  - Model shows promise but needs refinement")
            report.append("  - Focus on categories with low performance")
            report.append("  - Increase training data for weak areas")
        else:
            report.append("  - Model performs well overall")
            report.append("  - Consider fine-tuning on specific weak categories")
            report.append("  - Ready for production use with monitoring")
        
        return "\n".join(report)
    
    def save_evaluation_results(self, results: Dict, filepath: str):
        """Save evaluation results to file."""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Also save human-readable report
        report_path = filepath.replace('.json', '_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_evaluation_report(results))
        
        logger.info(f"Evaluation results saved to {filepath}")
        logger.info(f"Evaluation report saved to {report_path}")
