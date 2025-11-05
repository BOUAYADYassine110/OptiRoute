"""
LLM Service - OpenAI integration for intelligent chat
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'regex').lower()
        self.use_llm = False
        self.client = None
        
        # Try Groq first (FREE and FAST)
        if self.provider == 'groq' or not self.use_llm:
            groq_key = os.getenv('GROQ_API_KEY', '')
            if groq_key and groq_key != 'your-groq-api-key':
                try:
                    from groq import Groq
                    self.client = Groq(api_key=groq_key)
                    self.provider = 'groq'
                    self.use_llm = True
                    print("Groq AI enabled (FREE) - Smart chat parsing active!")
                    return
                except Exception as e:
                    print(f"Groq not available: {e}")
        
        # Try OpenAI as fallback
        if self.provider == 'openai' or not self.use_llm:
            openai_key = os.getenv('OPENAI_API_KEY', '')
            if openai_key and openai_key != 'your-openai-api-key':
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=openai_key)
                    self.provider = 'openai'
                    self.use_llm = True
                    print("OpenAI enabled for chat")
                    return
                except Exception as e:
                    print(f"OpenAI not available: {e}")
        
        # Use regex fallback
        print("Using regex parser (works well with 'from X to Y' format)")
    
    def extract_order_details(self, user_message):
        """Extract order details from user message using LLM or fallback"""
        
        if self.use_llm:
            if self.provider == 'groq':
                return self._extract_with_groq(user_message)
            elif self.provider == 'openai':
                return self._extract_with_openai(user_message)
        
        return self._extract_with_regex(user_message)
    
    def _extract_with_groq(self, user_message):
        """Use Groq (FREE) to extract order details"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Fast and free!
                messages=[
                    {
                        "role": "system",
                        "content": """Extract delivery order details from user messages. Return ONLY valid JSON.

Format:
{
  "pickup_address": "location",
  "delivery_address": "location",
  "weight": number,
  "notes": "text",
  "success": true/false
}

Examples:
"send 2kg from Empire State to Times Square" → {"pickup_address": "Empire State Building", "delivery_address": "Times Square", "weight": 2, "success": true}
"from Central Park to Brooklyn 5kg" → {"pickup_address": "Central Park", "delivery_address": "Brooklyn", "weight": 5, "success": true}"""
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON
            try:
                # Extract JSON from response
                import json
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = result[json_start:json_end]
                    data = json.loads(json_str)
                    data['message'] = 'Order details extracted'
                    return data
            except:
                pass
                
        except Exception as e:
            print(f"Groq error: {e}")
        
        return self._extract_with_regex(user_message)
    
    def _extract_with_openai(self, user_message):
        """Use OpenAI to extract order details"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a delivery order assistant. Extract delivery details from user messages.
                        
Return JSON with:
{
  "pickup_address": "extracted pickup location",
  "delivery_address": "extracted delivery location", 
  "weight": number in kg (default 1.0 if not specified),
  "notes": "any special instructions",
  "success": true/false,
  "message": "friendly response or error message"
}

Examples:
- "Send 2kg from Empire State Building to Times Square" 
  → pickup: "Empire State Building", delivery: "Times Square", weight: 2
- "I need a package delivered from 123 Main St to 456 Oak Ave"
  → pickup: "123 Main St", delivery: "456 Oak Ave", weight: 1.0
- "Deliver from Central Park to Brooklyn, 5 kilos"
  → pickup: "Central Park", delivery: "Brooklyn", weight: 5"""
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            try:
                data = json.loads(result)
                return data
            except:
                # If not valid JSON, try to extract from text
                return self._extract_with_regex(user_message)
                
        except Exception as e:
            print(f"OpenAI error: {e}")
            return self._extract_with_regex(user_message)
    
    def _extract_with_regex(self, text):
        """Fallback: Extract using regex patterns"""
        import re
        
        # Flexible pattern: finds "from X to Y" anywhere in text
        pattern = r'from\s+(.+?)\s+to\s+(.+?)(?:\s*\d+\s*kg|\s*,|\.|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        pickup = None
        delivery = None
        
        if match:
            pickup = match.group(1).strip()
            delivery = match.group(2).strip()
            
            # Clean up pickup and delivery
            pickup = pickup.strip(' ,')
            delivery = delivery.strip(' ,')
            
            # Remove weight from delivery if captured
            delivery = re.sub(r'\s*\d+\s*kg.*$', '', delivery, flags=re.IGNORECASE)
            delivery = delivery.strip()
        
        # Extract weight - simple pattern
        weight = 1.0
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilo)', text, re.IGNORECASE)
        if weight_match:
            weight = float(weight_match.group(1))
        
        # Extract notes
        notes = ""
        if 'fragile' in text.lower():
            notes = "Fragile"
        elif 'urgent' in text.lower():
            notes = "Urgent"
        
        success = bool(pickup and delivery)
        
        if pickup and delivery:
            print(f"  Pickup: '{pickup}'")
            print(f"  Delivery: '{delivery}'")
            print(f"  Weight: {weight} kg")
        else:
            print(f"  Could not extract locations from: '{text}'")
            print(f"  Try: 'from [pickup] to [delivery]'")
        
        return {
            "pickup_address": pickup,
            "delivery_address": delivery,
            "weight": weight,
            "notes": notes,
            "success": success,
            "message": "Order details extracted" if success else "I need both locations. Try: 'from Empire State Building to Times Square' or 'from Central Park to Brooklyn 5kg'"
        }

llm_service = LLMService()