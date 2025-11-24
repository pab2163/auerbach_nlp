
spell_prompt = f"""
You are analyzing a given text message from a teenager to make any spelling corrections, returning the resulting messages with corrections as **valid JSON format**.  
Fix contractions, expand abbreviations and acronyms, and correct misspelled words. Do not change the meaning of the message or fix slang.

#### Example 1:  
**Message:** "I love you!"  
```json
{{
  "corrected_message": "I love you!"
}}
#### Example 2: 
**Message:** "The worl is really tragik :("
```json
{{
    "corrected_message": "The world is really tragic :("
}}
#### Example 3: 
**Message:** "I like her face card, it's on fleek"
```json
{{
    "corrected_message": "I like her face card, it is on fleek"
}}

Now, analyze the following message:

Message: "{message_text}"

Provide your response in valid JSON format. """


   detect_prompt = f"""
You are analyzing a given text message from a teenager to determine if it is in English or another language.
The term ENTITY refers to a name, and should be considered English. Non-words, slang or symbols should be considered English.  

Return the response in **valid JSON format**.  

### Examples:  
#### Example 1:  
**Message:** "I love you!"  
```json
{{
  "language": "English"
}}
#### Example 2: 
**Message:** "Como estas?"
```json
{{
    "language": "Not English"
}}
#### Example 3: 
**Message:** "c'est la vie"
```json
{{
    "language": "Not English"
}}

Now, analyze the following message:

Message: "{message_text}"

Provide your response in valid JSON format. """

translate_prompt = f"""
You are analyzing a given text message from a teenager to translate it into English. Return two fields as valid **JSON** format:
1. `language`: Indicate if the message is in English or another language.
2. `translated_message`: If the message is in another interpretable language, translate the message to English, preserving the meaning and context. Do not change the meaning of the message or fix slang. 
In the case of numbers or symbols, return 'language': 'Not Language' and 'translated_message' should be the original message.
Do not correct misspellings, just translate the message if it is not in English.

#### Example 1:
**Message:** "I love you!"
```json
{{
  "language": "English",
  "translated_message": "I love you!"
}}
```

#### Example 2:
**Message:** "Como estas?"
```json
{{
    "language": "Spanish",
    "translated_message": "How are you?"
}}
```

#### Example 3:
**Message:** "I wish you wre ma frand"
```json
{{
    "language": "English",
    "translated_message": "I wish you wre ma frand"
}}
```

Now, analyze the following message:

Message: "{message_text}"

Provide your response in valid JSON format."""