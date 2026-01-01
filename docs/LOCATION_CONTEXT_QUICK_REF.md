# Quick Reference: Location Context for Woonasquatucket River Watershed Council

## What Changed?

Added **location-aware prompting** to make the Q&A system specifically aware of:
- ✅ Organization: **Woonasquatucket River Watershed Council**
- ✅ Location: **Providence, Rhode Island**
- ✅ Address: **45 Eagle Street, Suite 202, Providence, RI 02909**
- ✅ Focus Areas: Watershed protection, environmental education, habitat restoration, community health

## Where It Appears

### 1. System Prompts (Spanish & English)
Now include organization name, location, and service area context.

**Files Modified:**
- `backend/src/agent/main.py` (lines 605-655)

**Example:**
```
Eres un asistente comunitario de Woonasquatucket River Watershed Council, 
ubicado en Providence, Rhode Island...
```

### 2. Planning Phase
Analyzes questions for **LOCAL RELEVANCE** to Rhode Island.

**Files Modified:**
- `backend/src/agent/main.py` (lines 345-380)

**Output:**
```
RELEVANCIA LOCAL: Sí (applicable to Providence, RI)
CONTEXTO UBICACIÓN: Woonasquatucket River Watershed area
```

### 3. Clarification Questions
Now provides **location-specific** and **watershed-specific** clarifications.

**Files Modified:**
- `backend/src/agent/tools/clarify_question.py` (lines 40-120)

**Example Clarifications:**
- "Are you asking about the Woonasquatucket River Watershed specifically?"
- "Are you interested in habitat restoration, water quality, or community education?"
- "Are you asking about resources in Providence, Rhode Island specifically?"

## Configuration

To customize for a different organization:

**File:** `backend/src/agent/main.py`, lines 100-112

```python
LOCATION_CONTEXT = {
    "organization": "Your Organization Name",
    "location": "Your City, Your State",
    "address": "Your Address",
    "region": "Your Region",
    "service_area": "Your Service Area",
    "focus_areas": [
        "Your focus area 1",
        "Your focus area 2",
        "Your focus area 3"
    ]
}
```

## Testing

### Quick Test in Spanish
```
Question: "¿Cómo puedo ayudar a limpiar el rio?"
Expected: References to Woonasquatucket River and Providence, RI
```

### Quick Test in English
```
Question: "What environmental programs are available?"
Expected: Planning includes "LOCAL RELEVANCE" assessment
Expected: Clarification mentions Providence, Rhode Island
```

### Check for Location Context
Look for:
- ✅ Organization name in responses
- ✅ "Providence, Rhode Island" mentioned
- ✅ "Woonasquatucket" in watershed questions
- ✅ Focus areas in clarifications

## Files Modified

| File | Lines | What Changed |
|------|-------|--------------|
| `backend/src/agent/main.py` | 100-112 | Added `LOCATION_CONTEXT` configuration |
| `backend/src/agent/main.py` | 605-655 | Enhanced system prompts with location |
| `backend/src/agent/main.py` | 345-380 | Enhanced planning node with location awareness |
| `backend/src/agent/tools/clarify_question.py` | 40-120 | Added location-specific clarifications |
| `docs/LOCATION_CONTEXT_SETUP.md` | NEW | Comprehensive documentation |

## Key Features

✅ **Automatic Language Detection**  
- Spanish prompts reference location in Spanish
- English prompts reference location in English

✅ **Smart Clarifications**  
- Detects watershed questions → asks watershed-specific clarifications
- Detects location questions → asks location-specific clarifications
- Detects service questions → asks about organization focus areas

✅ **Planning Phase Awareness**  
- Evaluates if questions are relevant to Rhode Island
- Suggests location context if needed
- Tracks service area relevance

✅ **No Database Changes Required**  
- Works with existing vector database
- No migration needed
- Backward compatible

## Example Flows

### Scenario 1: Watershed Question
```
User (Spanish): "¿Qué puedo hacer para proteger la calidad del agua?"

System:
1. Detects: WATERSHED category
2. Planning identifies: LOCAL RELEVANCE: Sí
3. Clarification offers: 
   - Questions about Woonasquatucket specifically
   - Water quality vs habitat restoration
   - Volunteering vs education
4. Final answer includes: Organization name, location, focus areas
```

### Scenario 2: Vague Location Question
```
User (English): "Where can I find help with environmental issues?"

System:
1. Detects: LOCATION category
2. Planning notes: LOCAL RELEVANCE: Partially
3. Clarification asks:
   - Are you in Providence, Rhode Island?
   - What specific environmental issue?
   - Location-specific services needed?
4. Response references: Rhode Island area, available services
```

### Scenario 3: Community Health Question
```
User (Spanish): "¿Dónde hay recursos de salud comunitaria?"

System:
1. Detects: SERVICE category
2. Planning evaluates: LOCAL RELEVANCE: Sí
3. Clarification offers:
   - Environmental, educational, or health services?
   - Location in Rhode Island?
   - Type of support needed?
4. Final answer: References community health focus area
```

## Verification Checklist

After deployment, verify:

- [ ] Spanish prompts mention "Providence, Rhode Island"
- [ ] English prompts mention "Providence, Rhode Island"
- [ ] Watershed questions receive watershed-specific clarifications
- [ ] Location questions reference Rhode Island
- [ ] Planning shows "LOCAL RELEVANCE" assessment
- [ ] Clarification responses end with organization context
- [ ] All responses cite sources properly
- [ ] No error messages in logs about location context

## Support & Documentation

**Full Documentation:** `docs/LOCATION_CONTEXT_SETUP.md`

**Quick Customization:**
1. Edit `LOCATION_CONTEXT` in `main.py`
2. Update prompts if needed in planning node
3. Update clarifications in `clarify_question.py`
4. Restart backend
5. Test with sample questions

**Questions?** Refer to [LOCATION_CONTEXT_SETUP.md](./LOCATION_CONTEXT_SETUP.md) for detailed information.

---

**Status:** ✅ Production Ready  
**Last Updated:** January 1, 2026
