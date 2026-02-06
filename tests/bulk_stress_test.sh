#!/bin/bash

# Configuration - Aligned with src/agent/main.py
BASE_URL="http://127.0.0.1:8000/ask"
LOG_FILE="logs/bulk_test_results.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Ensure log directory exists
mkdir -p logs

echo "=== BULK STRESS TEST: $TIMESTAMP ===" > $LOG_FILE
echo "Endpoint: $BASE_URL" >> $LOG_FILE
echo "----------------------------------------" >> $LOG_FILE

# Query List: "Query|Condition_Tag"
QUERIES=(
  "Hello|English_Baseline"
  "Hola|Spanish_Baseline"
  "school|Tool_Trigger_English"
  "escuela|Tool_Trigger_Spanish"
  "¿Dónde está la escuela?|Spanish_UTF8_Complex"
  "I need a doctor|English_Medical"
  "Necesito un médico|Spanish_Medical"
  "What is 2+2?|Logic_Math"
  "Tell me a joke|Creative"
  "Bye|Termination"
)

echo "🚀 Starting RIOS Agent Stress Test..."
echo "Targeting: $BASE_URL"

for ENTRY in "${QUERIES[@]}"; do
    # Split the query and the tag
    QUERY=$(echo $ENTRY | cut -d'|' -f1)
    TAG=$(echo $ENTRY | cut -d'|' -f2)

    echo -n "Testing [$TAG]... "

    # Step 1: URL Encode the query (required for GET params)
    ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$QUERY'''))")

    # Step 2: Execute the GET request
    # We use -G to send data as query params and --data-urlencode for the question
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${BASE_URL}?question=${ENCODED_QUERY}&thread_id=test_suite")

    # Step 3: Parse Status and Body
    HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    # Log results
    echo "TAG: $TAG" >> $LOG_FILE
    echo "QUERY: $QUERY" >> $LOG_FILE
    echo "STATUS: $HTTP_STATUS" >> $LOG_FILE
    echo "RESPONSE: $BODY" >> $LOG_FILE
    echo "----------------------------------------" >> $LOG_FILE

    if [ "$HTTP_STATUS" == "200" ]; then
        echo "✅ OK"
    else
        echo "❌ FAIL ($HTTP_STATUS)"
    fi
done

echo "### END OF BULK TEST ###" >> $LOG_FILE
echo "Done! Full details in: $LOG_FILE"
