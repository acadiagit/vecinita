# Location Context Setup for Woonasquatucket River Watershed Council

## Overview

The Vecinita Q&A system has been enhanced with **location-aware context** specifically tailored for the **Woonasquatucket River Watershed Council** in Providence, Rhode Island.

This enhancement ensures that:
- All responses are grounded in Rhode Island community resources
- Clarification questions specifically reference location and local services
- Planning phase considers geographic relevance
- Users understand the service area and organizational focus

## Configuration

### Location Context Settings

The location context is configured in `backend/src/agent/main.py`:

```python
LOCATION_CONTEXT = {
    "organization": "Woonasquatucket River Watershed Council",
    "location": "Providence, Rhode Island",
    "address": "45 Eagle Street, Suite 202, Providence, RI 02909",
    "region": "Rhode Island",
    "service_area": "Woonasquatucket River Watershed",
    "focus_areas": [
        "Water quality and watershed protection",
        "Community environmental education",
        "Habitat restoration",
        "Community health and wellbeing in Rhode Island"
    ]
}
```

### Customizing Location Context

To modify the location context for a different organization or region:

1. **Open** `backend/src/agent/main.py`
2. **Locate** the `LOCATION_CONTEXT` dictionary (lines 100-112)
3. **Update** the following fields as needed:
   - `organization`: Your organization name
   - `location`: Your primary location
   - `address`: Your physical address
   - `region`: Your service region
   - `service_area`: The specific area you serve
   - `focus_areas`: List of main focus areas

4. **Save** the file - changes apply immediately on restart

## Implementation Details

### 1. System Prompts (Enhanced with Location Context)

#### Spanish System Prompt
The system prompt now includes:
- Organization name and location
- Service area and focus areas
- Instruction to clarify location if questions are outside Rhode Island
- Emphasis on local resource focus

```
Eres un asistente comunitario de {organization}, servicial y profesional.
Ubicado en {location} ({address}).

Tu objetivo es dar respuestas claras, concisas y precisas basadas en la información disponible
sobre recursos de la comunidad de Rhode Island...
```

#### English System Prompt
Similar location context included in English version for non-Spanish queries.

**Location:** `backend/src/agent/main.py`, lines 605-655

### 2. Planning Phase (Location-Aware Analysis)

The planning node now evaluates:
- **Local Relevance**: Is the question applicable to Rhode Island?
- **Location Context**: What specific geographic or service area is needed?
- **Service Fit**: Does it align with Woonasquatucket's focus areas?

#### Planning Prompt Structure

```
CONCEPTOS CLAVE: [concepts]
RELEVANCIA LOCAL: [es aplicable a Providence, RI? Sí/No/Parcialmente]
TIPO DE INFORMACIÓN: [information type]
PLAN DE BÚSQUEDA: [search strategy]
BÚSQUEDA NECESITA CLARIFICACIÓN: [yes/no]
CONTEXTO UBICACIÓN: [location-specific notes]
```

**Location:** `backend/src/agent/main.py`, lines 345-380

### 3. Clarification Questions (Location-Specific)

The clarification tool now provides location-aware questions:

#### Watershed-Specific Clarifications
When detecting watershed/environmental questions:
```
- Are you asking about the Woonasquatucket River Watershed specifically?
- Are you interested in habitat restoration, water quality, or community education?
- What aspect of watershed management interests you?
- Are you a community member, volunteer, or researcher?
```

#### Location-Specific Clarifications
When detecting location-related questions:
```
- Are you asking about resources in Providence, Rhode Island specifically?
- Which city or town in Rhode Island are you interested in?
- Is this related to the Rhode Island area or elsewhere?
- Are you looking for programs in a specific neighborhood or district?
```

#### Service-Specific Clarifications
When detecting general service questions:
```
- What specific service or program are you interested in?
- Can you give me more details about what you're looking for?
- Are you looking for environmental, educational, or community health services?
- Is this related to watershed protection, community health, or environmental education?
```

**Location:** `backend/src/agent/tools/clarify_question.py`, lines 40-90

### 4. Response Footer Enhancement

Clarification responses now conclude with:
```
Once you provide more details, I can give you a more accurate answer from our 
{location} community resources.
```

This reinforces the local focus and organizational identity.

## Use Cases

### Example 1: Watershed Question (Spanish)
**User:** "¿Cómo puedo ayudar a limpiar el río?"

**System Response:**
1. Planning detects: **WATERSHED** category
2. Clarification detects: **WATERSHED** questions
3. Offers specific follow-ups:
   - Are you asking about the Woonasquatucket River Watershed specifically?
   - Are you interested in habitat restoration, water quality, or community education?

### Example 2: Location Ambiguity (English)
**User:** "Where can I find environmental programs?"

**System Response:**
1. Planning notes: **LOCAL RELEVANCE: Partially** (not specific to RI)
2. Clarification asks:
   - Are you asking about resources in Providence, Rhode Island specifically?
   - Which city or town in Rhode Island are you interested in?

### Example 3: Service Question (Spanish)
**User:** "Necesito ayuda con recursos comunitarios"

**System Response:**
1. Planning detects: **SERVICE** category
2. Clarification offers:
   - Are you looking for environmental, educational, or community health services?
   - Is this related to watershed protection, community health, or environmental education?

## Testing the Setup

### 1. Test Location Context in Responses
```bash
# Start the backend
cd backend
uv run -m uvicorn src.agent.main:app --reload
```

### 2. Test Spanish Prompts
Send a query in Spanish:
```
"¿Dónde puedo encontrar programas de educación ambiental en Providence?"
```

Check the response includes references to:
- Providence, Rhode Island
- Woonasquatucket River Watershed Council
- Specific focus areas

### 3. Test English Prompts
Send a query in English:
```
"What environmental programs are available near Providence?"
```

Verify location context appears in system prompt and planning.

### 4. Test Clarification Questions
Send a vague query:
```
"How can I help with water?"
```

Verify clarification questions include:
- Watershed-specific options
- Service-specific options
- Location context

### 5. Verify Planning Phase
Check backend logs for planning output:
```
CONCEPTOS CLAVE: water, help, environmental
RELEVANCIA LOCAL: Sí
TIPO DE INFORMACIÓN: Environmental programs/volunteering
PLAN DE BÚSQUEDA: Search database for watershed programs
CONTEXTO UBICACIÓN: Woonasquatucket River area, Providence, RI
```

## Advanced Customization

### Adding New Focus Areas
To add new organizational focus areas:

1. Update `LOCATION_CONTEXT['focus_areas']` in `main.py`
2. Update clarification prompts in `clarify_question.py` if needed
3. Restart the backend

Example:
```python
"focus_areas": [
    "Water quality and watershed protection",
    "Community environmental education",
    "Habitat restoration",
    "Youth mentoring programs",  # NEW
    "Community health and wellbeing in Rhode Island"
]
```

### Adding Language Support
To add a new language (e.g., Portuguese):

1. Create new location context strings for that language
2. Update system prompts in `main.py`
3. Update planning prompts in `main.py`
4. Update clarification questions in `clarify_question.py`
5. Add language detection in `agent_node()` function

### Custom Clarification Categories
To add a custom category for your organization:

In `clarify_question.py`, add to `clarification_prompts`:
```python
"volunteers": [
    "Are you interested in volunteering opportunities?",
    "What type of volunteer work interests you?",
    "Do you have prior experience with environmental projects?",
    "What times are you available?"
]
```

Then update the detection logic:
```python
elif any(word in question_lower for word in ["volunteer", "help", "contribute"]):
    category = "volunteers"
```

## Monitoring & Logging

### Relevant Log Messages

When location context is being used:

**Planning Phase:**
```
Search plan created: RELEVANCIA LOCAL: Sí...
```

**Clarification Generation:**
```
Clarify Question: Generated location-aware clarification response
```

**System Prompt Application:**
```
Agent execution with location context: Woonasquatucket River Watershed Council
```

### Debugging Location Context Issues

If location context isn't appearing:

1. **Check imports**: Ensure `LOCATION_CONTEXT` is imported in all relevant files
2. **Verify config**: Check `LOCATION_CONTEXT` dictionary in `main.py`
3. **Check language detection**: Verify `langdetect` correctly identifies user language
4. **Review logs**: Look for warnings about planning or clarification failures

## API Integration

### Streaming Response Includes Location Context

The `/ask-stream` endpoint now emits:

```json
{
  "type": "progress",
  "stage": "planning",
  "tool": "planning",
  "message": "Analyzing your question and planning the search for Providence, RI resources..."
}
```

### Response Structure

Final response includes:
```json
{
  "type": "complete",
  "answer": "Based on our Woonasquatucket River Watershed Council resources...",
  "sources": [...],
  "plan": "RELEVANCIA LOCAL: Sí\nCONTEXTO UBICACIÓN: Providence, RI...",
  "thread_id": "..."
}
```

## Performance Impact

The location context enhancement has minimal performance impact:
- ✅ No additional database queries
- ✅ Context strings pre-compiled at startup
- ✅ Planning phase analysis is part of existing flow
- ✅ Clarification questions generation is rule-based (not LLM-dependent)

## Future Enhancements

### Planned Features
1. **Multi-location support**: Handle queries for multiple service areas
2. **Geolocation awareness**: Use user's actual location to enhance context
3. **Service-specific routing**: Route questions to appropriate departments
4. **Localized FAQs**: FAQ database filtered by location
5. **Event awareness**: Include location-specific events in responses

### Extended Customization
- Region-specific terminology
- Localized resource URLs
- Time zone considerations
- Accessibility features per region

## References

- **System Prompts**: `backend/src/agent/main.py`, lines 605-655
- **Planning Node**: `backend/src/agent/main.py`, lines 345-380
- **Clarification Tool**: `backend/src/agent/tools/clarify_question.py`, lines 40-120
- **Location Context Definition**: `backend/src/agent/main.py`, lines 100-112
- **Location Context Streaming**: `backend/src/agent/main.py`, lines 910

## Support

For questions about location context setup or customization, refer to:
1. The relevant source files listed above
2. The planning node implementation for understanding context analysis
3. The clarification tool implementation for understanding question routing
4. This documentation for configuration examples

---

**Last Updated:** January 1, 2026  
**Version:** 1.0  
**Status:** Production Ready
