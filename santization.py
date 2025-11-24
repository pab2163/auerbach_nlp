from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

def sanitizedata(df, debug=False):
    '''
    1. Make name map dictionary of tokens NOT to sanitize (suicide-related tokens, celebrities who died by suicide).
    2. Call the 'get name map' function to hash tokens (names, addresses) not already in the name map
    3. Hashed tokens will be traced with ENTITY1, ENTITY2, etc
    4. Will return the hash dictionary as well as the sanitized data
    '''
    # convert to string
    df['strinput_text'] = df['strinput_text'].astype(str)
    df_copy = df.copy()
    # need to install spacy in environment and download this model
    # pip install presidio-analyzer spacy
    # python -m spacy download en_core_web_lg - this is good for names, otherwise the package uses regexp

    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "en", "model_name": "en_core_web_lg"}
        ]
    }

    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()

    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    anonymizer = AnonymizerEngine()
    
    # Dictionary to store name mappings
    name_map = {}
    
    # Prepopulate dictionary with names of celebrities who died by suicide - these will NOT be hashed
    suicide_names_file = "celebrity_suicide_names/celebrity_suicide_list_hand_edited.txt"  
    name_threshold=12
    # Read the file and process each line into a dictionary
    with open(suicide_names_file, "r", encoding="utf-8") as file:
        name_map = {''.join(line.strip().lower().split()): ''.join(line.strip().lower().split()) for line in file}

    # Also prepopulate dictionary with suicide risk lexicon to make sure we don't hash out suicide-related language
    suicide_lexicon_file = 'lexicons/custom_auerbach_suicide_tokens_for_anonymizer.csv'
    suicide_lexicon = pd.read_csv(suicide_lexicon_file)
    suicide_tokens = suicide_lexicon['token']

    suicide_token_keylist=[]
    for token in suicide_tokens:
        name_map[''.join(token.strip().lower().split())]=''.join(token.strip().lower().split())
        suicide_token_keylist.append(''.join(token.strip().lower().split()))

    # Export timestamped map of pre-saved tokens not to hash
    now = datetime.now()
    with open(f'lexicons/init_tokens_not_to_hash_{now}.json', 'w') as file:
        json.dump(name_map, file, indent=4)

    # Using a list to store counter (mutable object that can be modified in nested function)
    counter = [1]
    def get_name_hash(name):
        # Normalize the name
        normalized = ''.join(name.lower().split())
        found_match=False
        # Check if this name has a 3-char sequence matching any existing names
        if len(normalized) >= 4:
            '''
            Replace with hashed name if 3-char sequence matches any existing names in name_map
            EXCEPT for name_map keys that are celebrities that died by suicide.
            Those will need to be exact matches, or name_threshold 12+ (somewhat arbitrary) characters matching , in order. 
            This is because we don't want to assume, for example, that every instance of "Robin" refers to "Robin williams"
            '''
            # search through existing names that have been hashed
            for existing_key in name_map.keys():
                # hashed keys
                if 'ENTITY' in name_map[existing_key]:
                    if len(existing_key) >= 4:
                        for i in range(len(normalized) - 3):
                            substr = normalized[i:i+4]
                            if substr in existing_key:
                                found_match = True
                                if debug:
                                    print(f'Found existing hashed name segment {substr},replacing with {name_map[existing_key]}')
                                return name_map[existing_key]
                # non-hashed keys (celebrity names or suicidal language)
                # if >= 12 characters, search for 12+ character segments in the flagged text that match
                else:
                    if len(existing_key) >= name_threshold:
                        for i in range(len(normalized) - name_threshold+1):
                            substr = normalized[i:i+name_threshold]
                            if substr in existing_key:
                                found_match = True
                                if existing_key in suicide_token_keylist:
                                    if debug:
                                        print(f'Found existing segment {substr}, NOT REPLACING')
                                    return name
                                else:
                                    if debug:
                                        print(f'Found existing segment {substr},replacing with {name_map[existing_key]}')
                                    return name_map[existing_key]
                    # for tokens in the suicide lexicon < 12 characters
                    elif existing_key in suicide_token_keylist:
                        if existing_key in normalized:
                            if debug:
                                print(f'Found existing suicide token segment {name}, NOT REPLACING')
                            return name
                    else:
                        if normalized == existing_key:
                            found_match = True
                            if debug:
                                    print(f'Found existing full token {normalized},replacing with {name_map[existing_key]}')
                            return name_map[existing_key]

        elif len(normalized) < 4:
            for existing_key in name_map.keys():
                if normalized == existing_key:
                    found_match = True
                    if debug:
                        print(f'Found existing full token {normalized},replacing with {name_map[existing_key]}')
                    return name_map[existing_key]
        
        # If no match found, create new entity
        if not found_match:
            name_map[normalized] = f"ENTITY{counter[0]}"
            counter[0] += 1
            print(f'Creating new entity {normalized}: as ENTITY{counter[0]}')
            return name_map[normalized]
    

    def anonymize_text(text):
        # Analyze the text for PII entities
        analyzer_results = analyzer.analyze(text=text, entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"], language='en')
        sorted_results = sorted(analyzer_results, key=lambda x: x.start, reverse=True)
        
        modified_text = text
        for result in sorted_results:
            if result.entity_type == "PERSON":
                entity_text = text[result.start:result.end]
                replacement = get_name_hash(entity_text)
            else:
                replacement = "PHONE/EMAIL"
            modified_text = modified_text[:result.start] + replacement + modified_text[result.end:]
        return modified_text

    # CHOOSING NOT TO WORRY ABOUT LOWER CASING 
    
    # Then anonymize - THIS IS THE KEY
    df_copy['strinput_text'] = [anonymize_text(text) for text in df_copy['strinput_text']]

    return df_copy, name_map