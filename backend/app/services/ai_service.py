from openai import OpenAI
from app.config import settings
import logging
import json
import tiktoken
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered document analysis using OpenAI."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text."""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate
            return len(text) // 4
    
    def truncate_text(self, text: str, max_tokens: int = 6000) -> str:
        """Truncate text to fit within token limit."""
        token_count = self.count_tokens(text)
        
        if token_count <= max_tokens:
            return text
        
        # Truncate to roughly max_tokens * 4 characters
        char_limit = max_tokens * 4
        truncated = text[:char_limit]
        
        logger.warning(f"Text truncated from {token_count} to ~{max_tokens} tokens")
        return truncated + "\n\n[... text truncated due to length ...]"
    
    def classify_document(self, text: str) -> Tuple[str, float]:
        """
        Classify the document type.
        
        Returns:
            Tuple of (document_type, confidence_score)
        """
        try:
            # Truncate text if too long
            text = self.truncate_text(text, max_tokens=3000)
            
            prompt = f"""Analyze the following document and classify it into one of these categories:
- invoice: Bills, invoices, payment requests
- contract: Legal agreements, contracts, terms of service
- resume: CVs, resumes, job applications
- receipt: Sales receipts, purchase confirmations
- form: Application forms, questionnaires, surveys
- letter: Business letters, correspondence
- report: Reports, analyses, white papers
- other: Anything else

Document text:
{text}

Respond ONLY with a JSON object in this exact format:
{{
    "document_type": "invoice",
    "confidence": 0.95,
    "reasoning": "Brief explanation"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document classification expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            result = json.loads(result_text)
            
            document_type = result.get("document_type", "other")
            confidence = result.get("confidence", 0.5)
            
            logger.info(f"Classified as: {document_type} (confidence: {confidence})")
            
            return document_type, confidence
            
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return "other", 0.0
    
    def extract_structured_data(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Extract structured data based on document type.
        """
        try:
            text = self.truncate_text(text, max_tokens=4000)
            
            # Define extraction schema based on document type
            schemas = {
                "invoice": {
                    "fields": ["invoice_number", "date", "due_date", "vendor_name", "vendor_address", 
                              "customer_name", "customer_address", "subtotal", "tax", "total", "currency", "line_items"],
                    "example": {
                        "invoice_number": "INV-2024-001",
                        "date": "2024-01-15",
                        "vendor_name": "Acme Corp",
                        "total": 1234.56,
                        "currency": "USD",
                        "line_items": [{"description": "Service A", "quantity": 2, "price": 100.00}]
                    }
                },
                "contract": {
                    "fields": ["contract_type", "parties", "effective_date", "expiration_date", 
                              "contract_value", "key_terms", "termination_clause"],
                    "example": {
                        "contract_type": "Service Agreement",
                        "parties": ["Company A", "Company B"],
                        "effective_date": "2024-01-01",
                        "contract_value": 50000.00
                    }
                },
                "resume": {
                    "fields": ["name", "email", "phone", "location", "summary", "skills", 
                              "work_experience", "education", "certifications"],
                    "example": {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "skills": ["Python", "JavaScript", "SQL"],
                        "work_experience": [{"company": "Tech Corp", "role": "Developer", "duration": "2020-2023"}]
                    }
                },
                "receipt": {
                    "fields": ["store_name", "date", "time", "items", "subtotal", "tax", "total", "payment_method"],
                    "example": {
                        "store_name": "Coffee Shop",
                        "date": "2024-01-15",
                        "total": 12.50,
                        "items": [{"name": "Coffee", "price": 4.50}]
                    }
                }
            }
            
            schema = schemas.get(document_type, {
                "fields": ["key_information", "important_dates", "amounts", "parties_involved"],
                "example": {"key_information": "Main content summary"}
            })
            
            prompt = f"""Extract structured data from this {document_type} document.

Extract these fields: {', '.join(schema['fields'])}

Example format:
{json.dumps(schema['example'], indent=2)}

Document text:
{text}

Respond ONLY with a JSON object containing the extracted data. If a field is not found, use null."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data extraction expert. Extract information accurately and respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up JSON (remove markdown code blocks if present)
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            extracted_data = json.loads(result_text)
            
            logger.info(f"Extracted {len(extracted_data)} fields from {document_type}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {"error": str(e)}
    
    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a concise summary of the document.
        """
        try:
            text = self.truncate_text(text, max_tokens=4000)
            
            prompt = f"""Summarize the following document in exactly {max_sentences} clear, concise sentences.
Focus on the most important information.

Document text:
{text}

Summary:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document summarization expert. Create clear, concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info(f"Generated summary: {len(summary)} characters")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of an API call.
        GPT-4 Turbo pricing (as of 2024):
        - Input: $0.01 per 1K tokens
        - Output: $0.03 per 1K tokens
        """
        input_cost = (input_tokens / 1000) * 0.01
        output_cost = (output_tokens / 1000) * 0.03
        return input_cost + output_cost
    
    def process_document_with_ai(self, text: str) -> Dict[str, Any]:
        """
        Complete AI processing: classification, extraction, and summarization.
        
        Returns:
            Dict with document_type, confidence, extracted_data, summary, and cost
        """
        try:
            total_cost = 0.0
            
            # 1. Classify document
            document_type, confidence = self.classify_document(text)
            
            # 2. Extract structured data
            extracted_data = self.extract_structured_data(text, document_type)
            
            # 3. Generate summary
            summary = self.generate_summary(text)
            
            # Estimate cost (rough calculation)
            input_tokens = self.count_tokens(text) * 3  # Called 3 times
            output_tokens = 500  # Rough estimate for all outputs
            total_cost = self.calculate_cost(input_tokens, output_tokens)
            
            return {
                "document_type": document_type,
                "document_type_confidence": confidence,
                "extracted_data": extracted_data,
                "summary": summary,
                "ai_processing_cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            return {
                "document_type": "other",
                "document_type_confidence": 0.0,
                "extracted_data": {"error": str(e)},
                "summary": "",
                "ai_processing_cost": 0.0
            }


# Singleton instance
ai_service = AIService()