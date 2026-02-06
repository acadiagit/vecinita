#!/bin/bash
# VECINITA-RIOS: Official Demo Suite
# Path: tests/demo_suite.sh

API_URL="http://localhost:8000/api/v1/chat"

echo "============================================================"
echo "🚀 STARTING VECINITA-RIOS DEMO SUITE"
echo "============================================================"

# 1. Simple Query: Fact Retrieval
echo -e "\n[TEST 1] Simple Retrieval: Health Clinics"
curl -s -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "List two clinics from the Nuestra Salud directory.",
           "history": []
         }' | python3 -m json.tool

# 2. Complex Query: Multi-source Reasoning
echo -e "\n[TEST 2] Complex Reasoning: Immigrant Resources"
curl -s -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "Based on your data, what specific support is available for immigrant families in Providence schools?",
           "history": []
         }' | python3 -m json.tool

# 3. Contextual Query: Memory & History
echo -e "\n[TEST 3] Contextual Memory: Follow-up question"
curl -s -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "Do they have an email address?",
           "history": [
             {"role": "user", "content": "Who is the contact for Immigrant Coalition RI?"},
             {"role": "assistant", "content": "The contact listed is Maria Silva."}
           ]
         }' | python3 -m json.tool

echo -e "\n============================================================"
echo "✅ DEMO SUITE COMPLETE"
echo "============================================================"
