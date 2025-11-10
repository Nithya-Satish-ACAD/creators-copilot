import pdfplumber
import re
import json
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


def extract_mark_scheme_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract mark scheme data from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries, each containing mark scheme data for one question
    """
    try:
        # Extract full text from PDF
        full_text = _extract_full_text_from_pdf(pdf_path)
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        logger.debug(f"PDF text preview (first 500 chars): {full_text[:500]}")
        
        # Try JSON format first (if the PDF contains JSON structure)
        json_questions = _try_extract_json_format(full_text)
        if json_questions:
            logger.info(f"Extracted {len(json_questions)} questions using JSON format")
            return json_questions
        
        # Try structured text format
        text_questions = _extract_structured_text_format(full_text)
        if text_questions:
            logger.info(f"Extracted {len(text_questions)} questions using structured text format")
            return text_questions
        
        # Fallback: Try to parse as basic question format
        basic_questions = _extract_basic_question_format(full_text)
        logger.info(f"Extracted {len(basic_questions)} questions using basic format")
        return basic_questions
        
    except Exception as e:
        logger.error(f"Error extracting mark scheme from {pdf_path}: {str(e)}")
        raise


def _extract_full_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from PDF using pdfplumber"""
    text_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n".join(text_parts)


def _fix_unescaped_quotes(json_str: str) -> str:
    """
    Fix unescaped quotes within JSON string values.
    This handles cases where PDF extraction includes literal quotes in strings.
    
    Strategy: Parse character by character, track string state, and escape quotes
    that appear within string values (not at string boundaries).
    """
    result = []
    i = 0
    in_string = False
    escape_next = False
    
    while i < len(json_str):
        char = json_str[i]
        
        # Handle escape sequences - if previous char was \, this char is escaped
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue
        
        # Check for escape character
        if char == '\\':
            result.append(char)
            escape_next = True
            i += 1
            continue
        
        # Handle quotes - the tricky part
        if char == '"':
            if not in_string:
                # Starting a new string
                in_string = True
                result.append(char)
            else:
                # We're in a string, this could be:
                # 1. The closing quote (followed by : , } ] or whitespace then one of those)
                # 2. A quote within the string that should be escaped
                
                # Look ahead to see what follows this quote
                j = i + 1
                # Skip any whitespace (including newlines, spaces, tabs)
                while j < len(json_str) and json_str[j] in ' \t\n\r':
                    j += 1
                
                # Check if what follows indicates this is a closing quote
                if j < len(json_str) and json_str[j] in ':,}]':
                    # This is a legitimate closing quote
                    in_string = False
                    result.append(char)
                elif j >= len(json_str):
                    # End of string, this is a closing quote
                    in_string = False
                    result.append(char)
                else:
                    # This quote is within the string value, escape it
                    result.append('\\"')
            i += 1
            continue
        
        result.append(char)
        i += 1
    
    return ''.join(result)


def _try_extract_json_format(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Try to extract JSON format from text.
    Handles cases where PDF contains JSON structure (with or without markdown code blocks)
    """
    try:
        # Remove markdown code blocks if present (handle both 2 and 3 backticks)
        cleaned_text = re.sub(r'`{2,3}json\s*', '', text)
        cleaned_text = re.sub(r'`{2,3}\s*', '', cleaned_text)
        
        # Remove common PDF page headers/footers that might break JSON
        cleaned_text = re.sub(r'Generated on.*?Page \d+ of \d+', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'Page \d+ of \d+', '', cleaned_text, flags=re.IGNORECASE)
        
        # Try to find JSON array pattern - use greedy match to capture all objects
        json_match = re.search(r'\[\s*\{.*\}\s*\]', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            logger.info(f"Found JSON pattern, attempting to parse {len(json_str)} characters")
            
            # Clean up control characters that break JSON parsing
            # Replace various types of newlines and control characters within string values
            json_str = json_str.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
            json_str = json_str.replace('\t', ' ')
            # Remove other common control characters
            json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
            # Clean up multiple spaces
            json_str = re.sub(r'\s+', ' ', json_str)
            
            # Fix unescaped quotes within JSON string values
            json_str = _fix_unescaped_quotes(json_str)
            
            questions_data = json.loads(json_str)
            logger.info(f"Successfully parsed JSON with {len(questions_data)} items")
            
            # Normalize the format
            normalized_questions = []
            for item in questions_data:
                normalized_questions.append(_normalize_question_format(item))
            
            logger.info(f"Normalized {len(normalized_questions)} questions")
            return normalized_questions
        else:
            logger.debug("No JSON array pattern found in text")
            return None
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"JSON extraction failed: {str(e)}")
        # Try to provide helpful context about the error
        if isinstance(e, json.JSONDecodeError):
            error_pos = e.pos
            context_start = max(0, error_pos - 100)
            context_end = min(len(json_str) if 'json_str' in locals() else 0, error_pos + 100)
            if 'json_str' in locals():
                logger.error(f"JSON around error (chars {context_start} to {context_end}):")
                logger.error(f"...{json_str[context_start:context_end]}...")
        return None


def _extract_structured_text_format(text: str) -> List[Dict[str, Any]]:
    """
    Extract mark scheme from structured text format.
    Expected format:
    questionnumber: 1
    question-text: "..."
    answertemplate: "..."
    markingscheme: [
        "(X marks) bullet point 1",
        "(Y marks) bullet point 2"
    ]
    deductions: [
        "(X mark) deduction 1"
    ]
    notes: "..."
    """
    questions = []
    
    # Split by question blocks - look for questionnumber pattern
    question_blocks = re.split(r'\n(?=(?:questionnumber|"questionnumber")\s*:\s*\d+)', text, flags=re.IGNORECASE)
    
    for block in question_blocks:
        if not block.strip():
            continue
        
        question_data = _parse_question_block(block)
        if question_data and question_data.get('questionnumber'):
            questions.append(question_data)
    
    return questions


def _parse_question_block(block: str) -> Dict[str, Any]:
    """Parse a single question block into structured data"""
    question_data = {
        "questionnumber": None,
        "question-text": "",
        "answertemplate": "",
        "markingscheme": []
    }
    
    # Extract question number
    qnum_match = re.search(r'(?:questionnumber|"questionnumber")\s*:\s*(\d+)', block, re.IGNORECASE)
    if qnum_match:
        question_data["questionnumber"] = int(qnum_match.group(1))
    
    # Extract question-text
    qtext_match = re.search(
        r'(?:question-text|"question-text")\s*:\s*["\']?(.*?)(?=["\']?\s*(?:answertemplate|"answertemplate"|$))',
        block,
        re.DOTALL | re.IGNORECASE
    )
    if qtext_match:
        question_data["question-text"] = _clean_text(qtext_match.group(1))
    
    # Extract answertemplate
    answer_match = re.search(
        r'(?:answertemplate|"answertemplate")\s*:\s*["\']?(.*?)(?=["\']?\s*(?:markingscheme|"markingscheme"|$))',
        block,
        re.DOTALL | re.IGNORECASE
    )
    if answer_match:
        question_data["answertemplate"] = _clean_text(answer_match.group(1))
    
    # Extract markingscheme array
    marking_match = re.search(
        r'(?:markingscheme|"markingscheme")\s*:\s*\[(.*?)\]',
        block,
        re.DOTALL | re.IGNORECASE
    )
    if marking_match:
        question_data["markingscheme"] = _extract_array_items(marking_match.group(1))
    
    return question_data


def _extract_basic_question_format(text: str) -> List[Dict[str, Any]]:
    """
    Fallback: Extract questions in basic format.
    Looks for patterns like:
    Question 1: ... Answer: ... Mark Scheme: ... Deductions: ... Notes: ...
    """
    questions = []
    
    # Pattern to match Question X blocks
    question_pattern = re.compile(
        r'(?:Question\s+(\d+)|questionnumber\s*[:=]?\s*(\d+))(.*?)(?=(?:Question\s+\d+|questionnumber\s*[:=]?\s*\d+|$))',
        re.DOTALL | re.IGNORECASE
    )
    
    for match in question_pattern.finditer(text):
        qnum = match.group(1) or match.group(2)
        content = match.group(3)
        
        if not qnum:
            continue
        
        question_data = {
            "questionnumber": int(qnum),
            "question-text": "",
            "answertemplate": "",
            "markingscheme": []
        }
        
        # Extract question text (before answer/template)
        qtext_match = re.search(
            r'^(.*?)(?=(?:answer|answertemplate|marking|mark\s+scheme))',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if qtext_match:
            question_data["question-text"] = _clean_text(qtext_match.group(1))
        
        # Extract answer template
        answer_match = re.search(
            r'(?:answer\s*template|correct\s*answer|answer)\s*[:=]?\s*(.*?)(?=(?:marking|mark\s+scheme|$))',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if answer_match:
            question_data["answertemplate"] = _clean_text(answer_match.group(1))
        
        # Extract marking scheme
        marking_match = re.search(
            r'(?:marking\s*scheme|mark\s*scheme)\s*[:=]?\s*(.*?)$',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if marking_match:
            marking_text = marking_match.group(1)
            question_data["markingscheme"] = _extract_bullet_points(marking_text)
        
        questions.append(question_data)
    
    return questions


def _extract_array_items(array_text: str) -> List[str]:
    """
    Extract items from array text.
    Handles quoted strings separated by commas.
    """
    items = []
    
    # Match quoted strings
    quoted_pattern = re.compile(r'["\']([^"\']*)["\']')
    matches = quoted_pattern.findall(array_text)
    
    if matches:
        items = [_clean_text(m) for m in matches if m.strip()]
    else:
        # Fallback: split by commas if not quoted
        parts = array_text.split(',')
        items = [_clean_text(p) for p in parts if p.strip()]
    
    return items


def _extract_bullet_points(text: str) -> List[str]:
    """
    Extract bullet points from text.
    Handles various bullet point formats: -, *, •, numbers, etc.
    """
    bullets = []
    
    # Split by common bullet point patterns
    lines = text.split('\n')
    
    current_bullet = ""
    for line in lines:
        line = line.strip()
        
        # Check if line starts with bullet pattern
        if re.match(r'^[-*•▪►]\s+', line) or re.match(r'^\(\d+\s*marks?\)', line, re.IGNORECASE):
            # Save previous bullet if exists
            if current_bullet:
                bullets.append(_clean_text(current_bullet))
            current_bullet = line
        elif line and current_bullet:
            # Continuation of current bullet
            current_bullet += " " + line
        elif line and not current_bullet:
            # First line without bullet marker
            current_bullet = line
    
    # Add last bullet
    if current_bullet:
        bullets.append(_clean_text(current_bullet))
    
    # If no bullets found, return the whole text as single item
    if not bullets:
        cleaned = _clean_text(text)
        if cleaned:
            bullets = [cleaned]
    
    return bullets


def _clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove quotes at start/end
    text = text.strip()
    text = re.sub(r'^["\']|["\']$', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove trailing commas and semicolons
    text = re.sub(r'[,;]\s*$', '', text)
    
    return text.strip()


def _normalize_question_format(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize question format to ensure consistent structure.
    Handles variations in field names.
    """
    # Log the incoming keys for debugging
    logger.debug(f"Normalizing question with keys: {list(item.keys())}")
    
    normalized = {
        "questionnumber": None,
        "question-text": "",
        "answertemplate": "",
        "markingscheme": []
    }
    
    # Question number - handle variations including spaces
    qnum = (item.get('questionnumber') or item.get('question_number') or 
            item.get('questionNumber') or item.get('Question number') or 
            item.get('Question Number'))
    
    # If not found, search for keys containing "question" and "number"
    if not qnum:
        for key in item.keys():
            key_lower = key.lower()
            if 'question' in key_lower and 'number' in key_lower:
                qnum = item.get(key)
                logger.debug(f"Found question number with key: '{key}'")
                break
    
    if qnum:
        # Handle string numbers
        if isinstance(qnum, str):
            qnum = qnum.strip()
            if qnum.isdigit():
                normalized["questionnumber"] = int(qnum)
            else:
                # Try to extract first number from string
                num_match = re.search(r'\d+', qnum)
                if num_match:
                    normalized["questionnumber"] = int(num_match.group())
        else:
            normalized["questionnumber"] = int(qnum) if not isinstance(qnum, int) else qnum
    
    # Question text - handle variations including spaces
    qtext = (item.get('question-text') or item.get('question_text') or 
             item.get('questionText') or item.get('question') or 
             item.get('Question text') or item.get('Question Text'))
    
    # If not found, search for keys containing "question" and "text"
    if not qtext:
        for key in item.keys():
            key_lower = key.lower()
            if 'question' in key_lower and ('text' in key_lower or key_lower == 'question'):
                qtext = item.get(key)
                logger.debug(f"Found question text with key: '{key}'")
                break
    
    normalized["question-text"] = str(qtext).strip() if qtext else ""
    
    # Answer template - handle variations including spaces and special formats
    answer = (item.get('answertemplate') or item.get('answer_template') or 
              item.get('answerTemplate') or item.get('answer') or 
              item.get('Answer template') or item.get('Answer Template'))
    
    # If not found, search for keys that contain "answer" and "template" (case-insensitive)
    if not answer:
        for key in item.keys():
            key_lower = key.lower()
            if 'answer' in key_lower and 'template' in key_lower:
                answer = item.get(key)
                logger.debug(f"Found answer template with key: '{key}'")
                break
    
    # If still not found, look for just "answer" or "correct answer"
    if not answer:
        for key in item.keys():
            key_lower = key.lower()
            if key_lower in ['answer', 'correct answer', 'correct_answer', 'correctanswer']:
                answer = item.get(key)
                logger.debug(f"Found answer with key: '{key}'")
                break
    
    # Handle list format for answer templates
    if isinstance(answer, list):
        normalized["answertemplate"] = "\n".join(str(a).strip() for a in answer if a)
    elif answer:
        normalized["answertemplate"] = str(answer).strip()
    else:
        normalized["answertemplate"] = ""
    
    # Marking scheme - handle variations including spaces, parentheses, and object format
    # First try exact matches
    marking = (item.get('markingscheme') or item.get('marking_scheme') or 
               item.get('markingScheme') or item.get('mark_scheme') or 
               item.get('Marking scheme') or item.get('Marking Scheme'))
    
    # If not found, search for keys that contain "marking" or "mark" + "scheme" (case-insensitive)
    # This handles cases like "Marking scheme (Total = 5)"
    if not marking:
        for key in item.keys():
            key_lower = key.lower()
            if ('marking' in key_lower or 'mark' in key_lower) and 'scheme' in key_lower:
                marking = item.get(key)
                logger.debug(f"Found marking scheme with key: '{key}'")
                break
    
    # Default to empty list if still not found
    if marking is None:
        marking = []
    
    # Process the marking scheme based on its type
    if isinstance(marking, dict):
        # Convert dict to list of strings (e.g., {"A [2]": "description"} -> ["A [2]: description"])
        marking_list = []
        for key, value in marking.items():
            if key.lower() == 'total':
                # Handle total marks separately or include it
                marking_list.append(f"Total: {value}")
            else:
                marking_list.append(f"{key}: {value}")
        normalized["markingscheme"] = marking_list
    elif isinstance(marking, list):
        normalized["markingscheme"] = [str(m).strip() for m in marking if m]
    elif isinstance(marking, str):
        normalized["markingscheme"] = [marking.strip()] if marking.strip() else []
    else:
        normalized["markingscheme"] = []
    
    # Log the normalized result for debugging
    logger.debug(f"Normalized question {normalized.get('questionnumber')}: "
                f"has {len(normalized.get('markingscheme', []))} marking scheme items")
    
    return normalized


def validate_mark_scheme(questions: List[Dict[str, Any]]) -> bool:
    """
    Validate that extracted mark scheme has required fields.
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        True if valid, False otherwise
    """
    if not questions:
        return False
    
    required_fields = ["questionnumber", "question-text", "answertemplate", 
                      "markingscheme"]
    
    for question in questions:
        # Check all required fields exist
        if not all(field in question for field in required_fields):
            return False
        
        # Check question number is valid
        if not isinstance(question["questionnumber"], int) or question["questionnumber"] <= 0:
            return False
    
    return True


def extract_mark_scheme_to_json(pdf_path: str, output_path: str = None) -> str:
    """
    Extract mark scheme and save as JSON file.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Optional path to save JSON output
        
    Returns:
        JSON string of extracted mark scheme
    """
    questions = extract_mark_scheme_from_pdf(pdf_path)
    json_output = json.dumps(questions, indent=2, ensure_ascii=False)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_output)
        logger.info(f"Saved mark scheme to {output_path}")
    
    return json_output


# Convenience function to match existing API
def extract_text_from_mark_scheme(pdf_path: str) -> Dict[str, Any]:
    """
    Extract mark scheme from PDF file.
    Returns format compatible with existing evaluation system.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary with 'mark_scheme' key containing list of questions
    """
    questions = extract_mark_scheme_from_pdf(pdf_path)
    return {"mark_scheme": questions}


if __name__ == "__main__":
    # Test with example file
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Extracting mark scheme from: {pdf_path}")
        
        try:
            questions = extract_mark_scheme_from_pdf(pdf_path)
            print(f"\n✓ Extracted {len(questions)} questions\n")
            print(json.dumps(questions, indent=2))
            
            # Validate
            if validate_mark_scheme(questions):
                print("\n✓ Mark scheme is valid!")
            else:
                print("\n⚠ Mark scheme validation failed")
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
    else:
        print("Usage: python extraction_markscheme.py <pdf_path>")


