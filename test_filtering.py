#!/usr/bin/env python3
"""
Test the manual filtering functionality for quiz questions
"""

import sys
from pathlib import Path

# Add quiz path
quiz_path = Path(__file__).parent / "quiz"
sys.path.insert(0, str(quiz_path))

from src.quiz_agent.generator import filter_to_20_questions, MCQ

def test_filtering():
    """Test the manual filtering function"""
    print("🧪 Testing Manual Question Filtering")
    print("=" * 50)
    
    # Test case 1: Exactly 20 valid questions
    print("📋 Test 1: Exactly 20 valid questions")
    valid_questions = []
    for i in range(20):
        mcq = MCQ(
            question=f"Question {i+1}?",
            options=[f"Option A{i}", f"Option B{i}", f"Option C{i}", f"Option D{i}"],
            answer_index=0,
            explanation=f"Explanation {i+1}",
            difficulty="medium"
        )
        valid_questions.append(mcq)
    
    filtered = filter_to_20_questions(valid_questions)
    print(f"   Input: {len(valid_questions)} questions")
    print(f"   Output: {len(filtered)} questions")
    print(f"   Result: {'✅ PASS' if len(filtered) == 20 else '❌ FAIL'}")
    
    # Test case 2: More than 20 valid questions (should take first 20)
    print("\n📋 Test 2: 25 valid questions (should take first 20)")
    extra_questions = valid_questions + [
        MCQ(question=f"Extra Q{i}?", options=["A", "B", "C", "D"], answer_index=1, explanation="Extra", difficulty="medium")
        for i in range(5)
    ]
    
    filtered = filter_to_20_questions(extra_questions)
    print(f"   Input: {len(extra_questions)} questions")
    print(f"   Output: {len(filtered)} questions")
    print(f"   Result: {'✅ PASS' if len(filtered) == 20 else '❌ FAIL'}")
    
    # Test case 3: Some invalid questions mixed with valid ones
    print("\n📋 Test 3: Mix of valid and invalid questions")
    mixed_questions = []
    
    # Add 15 valid questions
    for i in range(15):
        mcq = MCQ(
            question=f"Valid Question {i+1}?",
            options=[f"A{i}", f"B{i}", f"C{i}", f"D{i}"],
            answer_index=0,
            explanation=f"Explanation {i+1}",
            difficulty="medium"
        )
        mixed_questions.append(mcq)
    
    # Add 5 invalid questions (missing options, invalid answer_index, etc.)
    invalid_questions = [
        MCQ(question="Invalid 1?", options=["A", "B"], answer_index=0, explanation="Only 2 options", difficulty="medium"),  # Only 2 options
        MCQ(question="Invalid 2?", options=["A", "B", "C", "D"], answer_index=5, explanation="Invalid index", difficulty="medium"),  # Invalid answer_index
        MCQ(question="", options=["A", "B", "C", "D"], answer_index=0, explanation="No question", difficulty="medium"),  # Empty question
        MCQ(question="Invalid 4?", options=["A", "", "C", "D"], answer_index=0, explanation="Empty option", difficulty="medium"),  # Empty option
        MCQ(question="Invalid 5?", options=["A", "B", "C", "D", "E"], answer_index=0, explanation="Too many options", difficulty="medium"),  # Too many options
    ]
    
    mixed_questions.extend(invalid_questions)
    
    filtered = filter_to_20_questions(mixed_questions)
    print(f"   Input: {len(mixed_questions)} questions (15 valid + 5 invalid)")
    print(f"   Output: {len(filtered)} questions")
    print(f"   Result: {'✅ PASS' if len(filtered) == 15 else '❌ FAIL'}")
    
    # Test case 4: Fewer than 10 questions
    print("\n📋 Test 4: Only 5 valid questions")
    few_questions = valid_questions[:5]
    filtered = filter_to_20_questions(few_questions)
    print(f"   Input: {len(few_questions)} questions")
    print(f"   Output: {len(filtered)} questions")
    print(f"   Result: {'✅ PASS' if len(filtered) == 5 else '❌ FAIL'}")
    
    # Test case 5: Empty list
    print("\n📋 Test 5: Empty list")
    filtered = filter_to_20_questions([])
    print(f"   Input: 0 questions")
    print(f"   Output: {len(filtered)} questions")
    print(f"   Result: {'✅ PASS' if len(filtered) == 0 else '❌ FAIL'}")
    
    print("\n" + "=" * 50)
    print("🎉 Manual filtering tests completed!")
    print("The system will now:")
    print("   ✅ Filter out invalid questions automatically")
    print("   ✅ Take exactly 20 questions if more are generated")
    print("   ✅ Accept fewer than 20 if that's all that's valid")
    print("   ✅ Provide appropriate feedback messages")

if __name__ == "__main__":
    test_filtering()
